# routes/api_v1/patient.py — Patient JSON API
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Patient, DiagnosticReport, Observation, Condition, Allergy, Medication, Immunization, Procedure, ImagingStudy, Encounter, Document, Notification, AuditEvent, AccessRequest, EmergencyProfile, HealthIdentity
from datetime import datetime, timedelta, date
import utils, os

patient_v1_bp = Blueprint('patient_v1', __name__)


def _get_patient():
    """Get current patient from JWT identity. Returns (patient, error_response)."""
    from flask_jwt_extended import get_jwt_identity
    from models import User
    import json
    raw = get_jwt_identity()
    try:
        identity = json.loads(raw) if isinstance(raw, str) else raw
    except:
        identity = {'role': 'patient', 'user_id': raw}
        
    if identity.get('role') != 'patient':
        return None, (jsonify({'error': 'Patient account required.'}), 403)
    user = db.session.get(User, identity['user_id'])
    if not user or not user.patient:
        return None, (jsonify({'error': 'Patient profile not found.'}), 404)
    return user.patient, None


# ── Dashboard ────────────────────────────────────────────────────────────────
@patient_v1_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    patient, err = _get_patient()
    if err: return err
    recent_reports = DiagnosticReport.query.filter_by(patient_id=patient.id).order_by(DiagnosticReport.report_date.desc()).limit(3).all()
    recent_encounters = Encounter.query.filter_by(patient_id=patient.id).order_by(Encounter.encounter_date.desc()).limit(3).all()
    active_medications = Medication.query.filter_by(patient_id=patient.id, status='active').all()
    active_conditions = Condition.query.filter(
        Condition.patient_id == patient.id,
        Condition.status.in_(['active', 'monitoring'])
    ).all()
    pending_requests = AccessRequest.query.filter_by(patient_id=patient.id, status='pending').count()
    unread_notifications = Notification.query.filter_by(patient_id=patient.id, is_read=False).count()
    return jsonify({
        'patient': {
            'id': patient.id, 'full_name': patient.full_name,
            'blood_group': patient.blood_group, 'biological_sex': patient.biological_sex,
            'date_of_birth': str(patient.date_of_birth) if patient.date_of_birth else None,
            'age': patient.age(), 'phone': patient.phone,
            'hv_id': patient.health_identity.hv_id if patient.health_identity else None,
            'aadhaar_verified': patient.aadhaar_verified,
        },
        'stats': {
            'active_medications': len(active_medications),
            'active_conditions': len(active_conditions),
            'pending_consent_requests': pending_requests,
            'unread_notifications': unread_notifications,
        },
        'recent_reports': [{
            'id': r.id, 'report_name': r.report_name,
            'report_date': str(r.report_date), 'laboratory': r.laboratory,
            'status': r.status
        } for r in recent_reports],
        'recent_encounters': [{
            'id': e.id, 'encounter_type': e.encounter_type,
            'encounter_date': str(e.encounter_date), 'doctor_name': e.doctor_name,
            'specialty': e.specialty, 'reason': e.reason, 'facility': e.facility
        } for e in recent_encounters],
        'active_medications': [{
            'id': m.id, 'medicine_name': m.medicine_name,
            'dosage': m.dosage, 'frequency': m.frequency,
            'prescribing_doctor': m.prescribing_doctor
        } for m in active_medications],
    })


# ── Timeline ─────────────────────────────────────────────────────────────────
@patient_v1_bp.route('/timeline', methods=['GET'])
@jwt_required()
def timeline():
    patient, err = _get_patient()
    if err: return err
    filter_type = request.args.get('filter', 'all')
    items = utils.build_timeline(patient)
    if filter_type != 'all':
        items = [i for i in items if i['type'] == filter_type]
    # Serialize dates
    for item in items:
        if item.get('date') and hasattr(item['date'], 'isoformat'):
            item['date'] = item['date'].isoformat()
    return jsonify({'timeline': items, 'filter': filter_type})


# ── Health ID ─────────────────────────────────────────────────────────────────
@patient_v1_bp.route('/health-id', methods=['GET'])
@jwt_required()
def health_id():
    patient, err = _get_patient()
    if err: return err
    hi = patient.health_identity
    qr_url = None
    if hi and hi.qr_code_path:
        qr_url = f'/uploads/{hi.qr_code_path}'
    return jsonify({
        'hv_id': hi.hv_id if hi else None,
        'qr_url': qr_url,
        'patient_name': patient.full_name,
        'blood_group': patient.blood_group,
    })


# ── Health ID Public (no auth) ────────────────────────────────────────────────
@patient_v1_bp.route('/health-id/public', methods=['GET'])
def health_id_public():
    hv_id = request.args.get('id', '').strip()
    if not hv_id:
        return jsonify({'error': 'HV-ID is required.'}), 400
    identity = HealthIdentity.query.filter_by(hv_id=hv_id).first()
    if not identity:
        return jsonify({'error': 'HealthVault ID not found.'}), 404
    p = identity.patient
    return jsonify({
        'found': True, 'hv_id': hv_id,
        'full_name': p.full_name,
        'blood_group': p.blood_group,
        'biological_sex': p.biological_sex,
    })


# ── Emergency Card (no auth) ──────────────────────────────────────────────────
@patient_v1_bp.route('/emergency', methods=['GET'])
def emergency():
    hv_id = request.args.get('hv_id', '').strip()
    if not hv_id:
        return jsonify({'error': 'hv_id is required.'}), 400
    identity = HealthIdentity.query.filter_by(hv_id=hv_id).first()
    if not identity:
        return jsonify({'error': 'Not found.'}), 404
    p = identity.patient
    ep = p.emergency_profile
    return jsonify({
        'full_name': p.full_name,
        'blood_group': p.blood_group,
        'biological_sex': p.biological_sex,
        'date_of_birth': str(p.date_of_birth) if p.date_of_birth else None,
        'age': p.age(),
        'critical_allergies': ep.critical_allergies if ep else None,
        'critical_medications': ep.critical_medications if ep else None,
        'major_conditions': ep.major_conditions if ep else None,
        'emergency_contact_name': ep.emergency_contact_name if ep else None,
        'emergency_contact_phone': ep.emergency_contact_phone if ep else None,
        'emergency_contact_relation': ep.emergency_contact_relation if ep else None,
        'organ_donor': ep.organ_donor if ep else False,
        'special_notes': ep.special_notes if ep else None,
    })


# ── Lab Reports ───────────────────────────────────────────────────────────────
@patient_v1_bp.route('/records/lab', methods=['GET'])
@jwt_required()
def lab_reports():
    patient, err = _get_patient()
    if err: return err
    reports = DiagnosticReport.query.filter_by(patient_id=patient.id).order_by(DiagnosticReport.report_date.desc()).all()
    return jsonify({'reports': [{
        'id': r.id, 'report_name': r.report_name,
        'report_date': str(r.report_date), 'laboratory': r.laboratory,
        'ordering_doctor': r.ordering_doctor, 'status': r.status,
        'summary': r.summary, 'source': r.source,
        'has_document': bool(r.document_path),
        'abnormal_count': sum(1 for o in r.observations if o.is_abnormal)
    } for r in reports]})


@patient_v1_bp.route('/records/lab/<report_id>', methods=['GET'])
@jwt_required()
def lab_report_detail(report_id):
    patient, err = _get_patient()
    if err: return err
    report = DiagnosticReport.query.filter_by(id=report_id, patient_id=patient.id).first()
    if not report:
        return jsonify({'error': 'Report not found.'}), 404
    utils.log_audit_event(
        patient_id=patient.id, actor_id=patient.user_id,
        actor_name=patient.full_name, action='viewed',
        resource_type='lab_report', resource_description=report.report_name, status='success'
    )
    return jsonify({
        'report': {
            'id': report.id, 'report_name': report.report_name,
            'report_date': str(report.report_date), 'laboratory': report.laboratory,
            'ordering_doctor': report.ordering_doctor, 'status': report.status,
            'summary': report.summary, 'source': report.source,
            'source_organization': report.source_organization,
            'document_url': (
                f'/api/v1/patient/records/lab/{report.id}/download'
                if report.document_path else None
            ),
        },
        'observations': [{
            'id': o.id, 'test_name': o.test_name, 'value': o.value,
            'unit': o.unit, 'reference_range': o.reference_range,
            'is_abnormal': o.is_abnormal, 'interpretation': o.interpretation
        } for o in report.observations]
    })


@patient_v1_bp.route('/records/lab/<report_id>/download', methods=['GET'])
@jwt_required()
def download_lab_report(report_id):
    patient, err = _get_patient()
    if err:
        return err
    report = DiagnosticReport.query.filter_by(id=report_id, patient_id=patient.id).first()
    if not report or not report.document_path:
        return jsonify({'error': 'Report document not found.'}), 404
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'], report.document_path,
        as_attachment=True,
    )


# ── Medications ───────────────────────────────────────────────────────────────
@patient_v1_bp.route('/medications', methods=['GET'])
@jwt_required()
def medications():
    patient, err = _get_patient()
    if err: return err
    active = Medication.query.filter_by(patient_id=patient.id, status='active').all()
    past = Medication.query.filter(
        Medication.patient_id == patient.id, Medication.status != 'active'
    ).order_by(Medication.start_date.desc()).all()
    def med_dict(m):
        return {'id': m.id, 'medicine_name': m.medicine_name, 'dosage': m.dosage,
                'frequency': m.frequency, 'start_date': str(m.start_date) if m.start_date else None,
                'end_date': str(m.end_date) if m.end_date else None,
                'prescribing_doctor': m.prescribing_doctor, 'status': m.status,
                'notes': m.notes, 'source': m.source}
    return jsonify({'active': [med_dict(m) for m in active], 'past': [med_dict(m) for m in past]})


# ── Conditions ────────────────────────────────────────────────────────────────
@patient_v1_bp.route('/conditions', methods=['GET'])
@jwt_required()
def conditions():
    patient, err = _get_patient()
    if err: return err
    return jsonify({'conditions': [{
        'id': c.id, 'condition_name': c.condition_name,
        'diagnosis_date': str(c.diagnosis_date) if c.diagnosis_date else None,
        'status': c.status, 'severity': c.severity,
        'treating_doctor': c.treating_doctor, 'notes': c.notes, 'source': c.source
    } for c in patient.conditions]})


# ── Allergies ─────────────────────────────────────────────────────────────────
@patient_v1_bp.route('/allergies', methods=['GET'])
@jwt_required()
def allergies():
    patient, err = _get_patient()
    if err: return err
    return jsonify({'allergies': [{
        'id': a.id, 'allergen': a.allergen, 'reaction': a.reaction,
        'severity': a.severity,
        'date_identified': str(a.date_identified) if a.date_identified else None,
        'notes': a.notes, 'source': a.source
    } for a in patient.allergies]})


# ── Vaccinations ──────────────────────────────────────────────────────────────
@patient_v1_bp.route('/vaccinations', methods=['GET'])
@jwt_required()
def vaccinations():
    patient, err = _get_patient()
    if err: return err
    return jsonify({'immunizations': [{
        'id': i.id, 'vaccine_name': i.vaccine_name, 'dose_number': i.dose_number,
        'vaccination_date': str(i.vaccination_date) if i.vaccination_date else None,
        'provider': i.provider, 'batch_number': i.batch_number,
        'next_dose_date': str(i.next_dose_date) if i.next_dose_date else None,
        'source': i.source
    } for i in patient.immunizations]})


# ── Procedures ────────────────────────────────────────────────────────────────
@patient_v1_bp.route('/procedures', methods=['GET'])
@jwt_required()
def procedures():
    patient, err = _get_patient()
    if err: return err
    return jsonify({'procedures': [{
        'id': p.id, 'procedure_name': p.procedure_name,
        'procedure_date': str(p.procedure_date) if p.procedure_date else None,
        'hospital': p.hospital, 'surgeon': p.surgeon,
        'indication': p.indication, 'outcome': p.outcome,
        'notes': p.notes, 'source': p.source
    } for p in patient.procedures]})


# ── Health Summary ────────────────────────────────────────────────────────────
@patient_v1_bp.route('/health-summary', methods=['GET'])
@jwt_required()
def health_summary():
    patient, err = _get_patient()
    if err: return err
    two_months_ago = date.today() - timedelta(days=60)
    active_meds = Medication.query.filter_by(patient_id=patient.id, status='active').all()
    all_conditions = Condition.query.filter_by(patient_id=patient.id).order_by(Condition.diagnosis_date.desc()).all()
    active_conditions = [c for c in all_conditions if c.status in ['active', 'monitoring']]
    allergies_list = Allergy.query.filter_by(patient_id=patient.id).all()
    immunizations = Immunization.query.filter_by(patient_id=patient.id).order_by(Immunization.vaccination_date.desc()).all()
    recent_reports = DiagnosticReport.query.filter(
        DiagnosticReport.patient_id == patient.id,
        DiagnosticReport.report_date >= two_months_ago
    ).order_by(DiagnosticReport.report_date.desc()).all()
    return jsonify({
        'active_medications': [{'id': m.id, 'medicine_name': m.medicine_name, 'dosage': m.dosage, 'frequency': m.frequency} for m in active_meds],
        'active_conditions': [{'id': c.id, 'condition_name': c.condition_name, 'status': c.status, 'severity': c.severity} for c in active_conditions],
        'allergies': [{'id': a.id, 'allergen': a.allergen, 'severity': a.severity, 'reaction': a.reaction} for a in allergies_list],
        'recent_immunizations': [{'id': i.id, 'vaccine_name': i.vaccine_name, 'vaccination_date': str(i.vaccination_date) if i.vaccination_date else None} for i in immunizations[:5]],
        'recent_reports': [{'id': r.id, 'report_name': r.report_name, 'report_date': str(r.report_date)} for r in recent_reports],
    })


# ── Notifications ─────────────────────────────────────────────────────────────
@patient_v1_bp.route('/notifications', methods=['GET'])
@jwt_required()
def notifications():
    patient, err = _get_patient()
    if err: return err
    all_notifs = Notification.query.filter_by(patient_id=patient.id).order_by(Notification.created_at.desc()).all()
    Notification.query.filter_by(patient_id=patient.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'notifications': [{
        'id': n.id, 'title': n.title, 'message': n.message,
        'notification_type': n.notification_type, 'is_read': n.is_read,
        'related_id': n.related_id,
        'created_at': n.created_at.isoformat() if n.created_at else None
    } for n in all_notifs]})


# ── Access History ────────────────────────────────────────────────────────────
@patient_v1_bp.route('/access-history', methods=['GET'])
@jwt_required()
def access_history():
    patient, err = _get_patient()
    if err: return err
    audit_events = AuditEvent.query.filter_by(patient_id=patient.id).order_by(AuditEvent.timestamp.desc()).limit(50).all()
    access_requests = AccessRequest.query.filter_by(patient_id=patient.id).order_by(AccessRequest.requested_at.desc()).all()
    return jsonify({
        'audit_events': [{
            'id': e.id, 'actor_name': e.actor_name, 'actor_organization': e.actor_organization,
            'action': e.action, 'resource_type': e.resource_type,
            'resource_description': e.resource_description, 'purpose': e.purpose,
            'status': e.status, 'timestamp': e.timestamp.isoformat() if e.timestamp else None
        } for e in audit_events],
        'access_requests': [{
            'id': r.id,
            'provider_name': r.provider.full_name if r.provider else 'Unknown',
            'provider_org': r.provider.organization.name if r.provider and r.provider.organization else None,
            'purpose': r.purpose, 'status': r.status,
            'requested_categories': r.requested_categories.split(',') if r.requested_categories else [],
            'approved_categories': r.approved_categories.split(',') if r.approved_categories else [],
            'duration_hours': r.duration_hours,
            'requested_at': r.requested_at.isoformat() if r.requested_at else None,
            'expires_at': r.expires_at.isoformat() if r.expires_at else None,
        } for r in access_requests]
    })


# ── Settings ──────────────────────────────────────────────────────────────────
@patient_v1_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_settings():
    patient, err = _get_patient()
    if err: return err
    ep = patient.emergency_profile
    return jsonify({
        'patient': {
            'id': patient.id, 'full_name': patient.full_name,
            'email': patient.user.public_email,
            'date_of_birth': str(patient.date_of_birth) if patient.date_of_birth else None,
            'biological_sex': patient.biological_sex, 'blood_group': patient.blood_group,
            'phone': patient.phone, 'address': patient.address,
            'city': patient.city, 'state': patient.state,
            'aadhaar_verified': patient.aadhaar_verified,
            'aadhaar_masked': f'XXXX-XXXX-{patient.aadhaar_number[-4:]}' if patient.aadhaar_number else None,
        },
        'emergency_profile': {
            'critical_allergies': ep.critical_allergies if ep else None,
            'critical_medications': ep.critical_medications if ep else None,
            'major_conditions': ep.major_conditions if ep else None,
            'emergency_contact_name': ep.emergency_contact_name if ep else None,
            'emergency_contact_phone': ep.emergency_contact_phone if ep else None,
            'emergency_contact_relation': ep.emergency_contact_relation if ep else None,
            'organ_donor': ep.organ_donor if ep else False,
            'special_notes': ep.special_notes if ep else None,
        } if ep else {}
    })


@patient_v1_bp.route('/settings', methods=['PATCH'])
@jwt_required()
def update_settings():
    patient, err = _get_patient()
    if err: return err
    data = request.get_json() or {}
    # Update patient fields
    for field in ['phone', 'address', 'city', 'state', 'blood_group', 'biological_sex']:
        if field in data:
            setattr(patient, field, data[field])
    if 'date_of_birth' in data and data['date_of_birth']:
        try:
            patient.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
        except ValueError:
            pass
    # Update emergency profile
    ep = patient.emergency_profile
    if not ep:
        ep = EmergencyProfile(patient_id=patient.id)
        db.session.add(ep)
    ep_fields = ['critical_allergies', 'critical_medications', 'major_conditions',
                 'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation',
                 'special_notes']
    for field in ep_fields:
        if field in data:
            setattr(ep, field, data[field])
    if 'organ_donor' in data:
        ep.organ_donor = bool(data['organ_donor'])
    db.session.commit()
    utils.log_audit_event(
        patient_id=patient.id, actor_id=patient.user_id,
        actor_name=patient.full_name, action='updated',
        resource_type='patient_profile', resource_description='Updated profile via mobile app', status='success'
    )
    return jsonify({'success': True, 'message': 'Profile updated successfully.'})
