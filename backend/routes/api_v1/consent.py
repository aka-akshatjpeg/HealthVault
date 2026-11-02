# routes/api_v1/consent.py — Consent Management JSON API
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, AccessRequest, Patient, User
from datetime import datetime, timedelta
import utils

consent_v1_bp = Blueprint('consent_v1', __name__)


def _get_patient():
    import json
    raw = get_jwt_identity()
    try:
        identity = json.loads(raw) if isinstance(raw, str) else raw
    except:
        identity = {'role': 'patient', 'user_id': raw}
        
    if identity.get('role') != 'patient':
        return None, (jsonify({'error': 'Patient account required.'}), 403)
    user = User.query.get(identity['user_id'])
    if not user or not user.patient:
        return None, (jsonify({'error': 'Patient not found.'}), 404)
    return user.patient, None


@consent_v1_bp.route('/requests', methods=['GET'])
@jwt_required()
def requests():
    patient, err = _get_patient()
    if err: return err
    pending = AccessRequest.query.filter_by(patient_id=patient.id, status='pending').all()
    history = AccessRequest.query.filter(
        AccessRequest.patient_id == patient.id,
        AccessRequest.status != 'pending'
    ).order_by(AccessRequest.responded_at.desc()).all()
    def req_dict(r):
        return {
            'id': r.id,
            'provider_name': r.provider.full_name if r.provider else 'Unknown',
            'provider_specialty': r.provider.specialty if r.provider else None,
            'provider_org': r.provider.organization.name if r.provider and r.provider.organization else None,
            'purpose': r.purpose, 'status': r.status,
            'requested_categories': r.requested_categories.split(',') if r.requested_categories else [],
            'approved_categories': r.approved_categories.split(',') if r.approved_categories else [],
            'duration_hours': r.duration_hours,
            'requested_at': r.requested_at.isoformat() if r.requested_at else None,
            'expires_at': r.expires_at.isoformat() if r.expires_at else None,
            'responded_at': r.responded_at.isoformat() if r.responded_at else None,
        }
    return jsonify({'pending': [req_dict(r) for r in pending], 'history': [req_dict(r) for r in history]})


@consent_v1_bp.route('/approve/<request_id>', methods=['POST'])
@jwt_required()
def approve(request_id):
    patient, err = _get_patient()
    if err: return err
    data = request.get_json() or {}
    approved_cats = data.get('approved_categories', [])
    access_request = AccessRequest.query.filter_by(id=request_id, patient_id=patient.id, status='pending').first()
    if not access_request:
        return jsonify({'error': 'Request not found or already responded.'}), 404
    if not approved_cats:
        return jsonify({'error': 'Please select at least one record category to approve.'}), 400
    access_request.status = 'approved'
    access_request.responded_at = datetime.utcnow()
    access_request.approved_categories = ','.join(approved_cats)
    access_request.expires_at = datetime.utcnow() + timedelta(hours=access_request.duration_hours)
    utils.log_audit_event(
        patient_id=patient.id, actor_id=patient.user_id,
        actor_name=patient.full_name, action='approved',
        resource_type='access_request',
        resource_description=f'Approved access for {access_request.provider.full_name if access_request.provider else "provider"}: {", ".join(approved_cats)}',
        purpose=access_request.purpose, status='success'
    )
    db.session.commit()
    return jsonify({'success': True, 'status': 'approved', 'expires_at': access_request.expires_at.isoformat()})


@consent_v1_bp.route('/deny/<request_id>', methods=['POST'])
@jwt_required()
def deny(request_id):
    patient, err = _get_patient()
    if err: return err
    access_request = AccessRequest.query.filter_by(id=request_id, patient_id=patient.id, status='pending').first()
    if not access_request:
        return jsonify({'error': 'Request not found or already responded.'}), 404
    access_request.status = 'denied'
    access_request.responded_at = datetime.utcnow()
    utils.log_audit_event(
        patient_id=patient.id, actor_id=patient.user_id,
        actor_name=patient.full_name, action='denied',
        resource_type='access_request',
        resource_description=f'Denied access for {access_request.provider.full_name if access_request.provider else "provider"}',
        status='denied'
    )
    db.session.commit()
    return jsonify({'success': True, 'status': 'denied'})


@consent_v1_bp.route('/revoke/<request_id>', methods=['POST'])
@jwt_required()
def revoke(request_id):
    patient, err = _get_patient()
    if err: return err
    access_request = AccessRequest.query.filter_by(id=request_id, patient_id=patient.id, status='approved').first()
    if not access_request:
        return jsonify({'error': 'Active approved request not found.'}), 404
    access_request.status = 'revoked'
    utils.log_audit_event(
        patient_id=patient.id, actor_id=patient.user_id,
        actor_name=patient.full_name, action='revoked',
        resource_type='access_request',
        resource_description=f'Revoked access for {access_request.provider.full_name if access_request.provider else "provider"}',
        status='revoked'
    )
    db.session.commit()
    return jsonify({'success': True, 'status': 'revoked'})
