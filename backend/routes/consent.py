# =============================================================================
# routes/consent.py — Consent Management Routes
# =============================================================================
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, AccessRequest, Patient, Provider
from functools import wraps
from datetime import datetime, timedelta
import utils

consent_bp = Blueprint('consent', __name__, url_prefix='/consent')


def patient_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != 'patient':
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@consent_bp.route('/requests')
@patient_required
def requests():
    patient = current_user.patient
    pending = AccessRequest.query.filter_by(patient_id=patient.id, status='pending').all()
    history = AccessRequest.query.filter(
        AccessRequest.patient_id == patient.id,
        AccessRequest.status != 'pending'
    ).order_by(AccessRequest.responded_at.desc()).all()
    return render_template('patient/consent_requests.html',
        patient=patient, pending_requests=pending, history=history
    )


@consent_bp.route('/review/<request_id>')
@patient_required
def review(request_id):
    patient = current_user.patient
    access_request = AccessRequest.query.filter_by(
        id=request_id, patient_id=patient.id
    ).first_or_404()
    return render_template('patient/consent_review.html',
        patient=patient, access_request=access_request,
        requested_categories=access_request.requested_categories.split(',') if access_request.requested_categories else []
    )


@consent_bp.route('/approve/<request_id>', methods=['POST'])
@patient_required
def approve(request_id):
    patient = current_user.patient
    access_request = AccessRequest.query.filter_by(
        id=request_id, patient_id=patient.id, status='pending'
    ).first_or_404()

    # Patient selects which categories to approve (may be a subset)
    approved_cats = request.form.getlist('approved_categories')
    if not approved_cats:
        flash('Please select at least one record category to approve.', 'warning')
        return redirect(url_for('consent.review', request_id=request_id))

    access_request.status = 'approved'
    access_request.responded_at = datetime.utcnow()
    access_request.approved_categories = ','.join(approved_cats)
    access_request.expires_at = datetime.utcnow() + timedelta(hours=access_request.duration_hours)

    cats_str = ', '.join(approved_cats)
    utils.log_audit_event(
        patient_id=patient.id, actor_id=current_user.id,
        actor_name=patient.full_name, action='approved',
        resource_type='access_request',
        resource_description=f'Approved access for {access_request.provider.full_name}: {cats_str}',
        purpose=access_request.purpose, status='success'
    )

    db.session.commit()
    flash(f'Access approved for Dr. {access_request.provider.full_name}. Expires in {access_request.duration_hours} hours.', 'success')
    return redirect(url_for('consent.requests'))


@consent_bp.route('/deny/<request_id>', methods=['POST'])
@patient_required
def deny(request_id):
    patient = current_user.patient
    access_request = AccessRequest.query.filter_by(
        id=request_id, patient_id=patient.id, status='pending'
    ).first_or_404()

    access_request.status = 'denied'
    access_request.responded_at = datetime.utcnow()

    utils.log_audit_event(
        patient_id=patient.id, actor_id=current_user.id,
        actor_name=patient.full_name, action='denied',
        resource_type='access_request',
        resource_description=f'Denied access for {access_request.provider.full_name}',
        status='denied'
    )

    db.session.commit()
    flash(f'Access request from Dr. {access_request.provider.full_name} has been denied.', 'info')
    return redirect(url_for('consent.requests'))


@consent_bp.route('/revoke/<request_id>', methods=['POST'])
@patient_required
def revoke(request_id):
    patient = current_user.patient
    access_request = AccessRequest.query.filter_by(
        id=request_id, patient_id=patient.id, status='approved'
    ).first_or_404()

    access_request.status = 'revoked'

    utils.log_audit_event(
        patient_id=patient.id, actor_id=current_user.id,
        actor_name=patient.full_name, action='revoked',
        resource_type='access_request',
        resource_description=f'Revoked access for {access_request.provider.full_name}',
        status='revoked'
    )

    db.session.commit()
    flash(f'Access for Dr. {access_request.provider.full_name} has been revoked.', 'success')
    return redirect(url_for('patient.access_history'))
