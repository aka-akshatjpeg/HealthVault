# =============================================================================
# routes/patient.py — Patient Portal Routes
# =============================================================================
from flask import Blueprint, render_template, redirect, url_for, request, flash, send_from_directory, current_app
from flask_login import login_required, current_user
from models import db, Patient, DiagnosticReport, Observation, Condition, Allergy, Medication, Immunization, Procedure, ImagingStudy, Encounter, Document, Notification, AuditEvent, AccessRequest
from functools import wraps
import utils
import os

patient_bp = Blueprint('patient', __name__, url_prefix='/patient')


def patient_required(f):
    """Decorator: only allow patients to access this route."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != 'patient':
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@patient_bp.route('/dashboard')
@patient_required
def dashboard():
    patient = current_user.patient
    unread_notifications = Notification.query.filter_by(
        patient_id=patient.id, is_read=False
    ).count()
    recent_notifications = Notification.query.filter_by(
        patient_id=patient.id
    ).order_by(Notification.created_at.desc()).limit(5).all()
    recent_reports = DiagnosticReport.query.filter_by(
        patient_id=patient.id
    ).order_by(DiagnosticReport.report_date.desc()).limit(3).all()
    recent_encounters = Encounter.query.filter_by(
        patient_id=patient.id
    ).order_by(Encounter.encounter_date.desc()).limit(3).all()
    active_medications = Medication.query.filter_by(
        patient_id=patient.id, status='active'
    ).all()
    active_conditions = Condition.query.filter(
        Condition.patient_id == patient.id,
        Condition.status.in_(['active', 'monitoring'])
    ).all()
    pending_requests = AccessRequest.query.filter_by(
        patient_id=patient.id, status='pending'
    ).count()
    return render_template('patient/dashboard.html',
        patient=patient,
        unread_notifications=unread_notifications,
        recent_notifications=recent_notifications,
        recent_reports=recent_reports,
        recent_encounters=recent_encounters,
        active_medications=active_medications,
        active_conditions=active_conditions,
        pending_requests=pending_requests
    )


@patient_bp.route('/timeline')
@patient_required
def timeline():
    patient = current_user.patient
    filter_type = request.args.get('filter', 'all')
    timeline_items = utils.build_timeline(patient)
    if filter_type != 'all':
        timeline_items = [i for i in timeline_items if i['type'] == filter_type]
    return render_template('patient/timeline.html',
        patient=patient,
        timeline_items=timeline_items,
        filter_type=filter_type
    )


@patient_bp.route('/health-id')
@patient_required
def health_id():
    patient = current_user.patient
    return render_template('patient/health_id.html', patient=patient)


@patient_bp.route('/health-id/public')
def health_id_public():
    """Public HealthVault ID card — accessible without login when scanned via QR.
    Shows the patient's name, HV-ID and basic info only. No medical records exposed."""
    from models import HealthIdentity
    hv_id = request.args.get('id', '').strip()
    if not hv_id:
        return render_template('patient/health_id_public_notfound.html'), 404
    identity = HealthIdentity.query.filter_by(hv_id=hv_id).first()
    if not identity:
        return render_template('patient/health_id_public_notfound.html'), 404
    patient = identity.patient
    return render_template('patient/health_id_public.html', patient=patient)


@patient_bp.route('/records/lab')
@patient_required
def lab_reports():
    patient = current_user.patient
    reports = DiagnosticReport.query.filter_by(
        patient_id=patient.id
    ).order_by(DiagnosticReport.report_date.desc()).all()
    uploaded_docs = Document.query.filter_by(
        patient_id=patient.id, document_type='lab_report', is_archived=False
    ).order_by(Document.document_date.desc()).all()
    return render_template('patient/lab_reports.html', patient=patient, reports=reports, uploaded_docs=uploaded_docs)


@patient_bp.route('/records/lab/<report_id>')
@patient_required
def lab_report_detail(report_id):
    patient = current_user.patient
    report = DiagnosticReport.query.filter_by(id=report_id, patient_id=patient.id).first_or_404()
    utils.log_audit_event(
        patient_id=patient.id, actor_id=current_user.id,
        actor_name=patient.full_name, action='viewed',
        resource_type='lab_report', resource_description=report.report_name, status='success'
    )
    return render_template('patient/lab_report_detail.html', patient=patient, report=report)


@patient_bp.route('/records/file/<path:filename>')
@patient_required
def download_record_file(filename):
    """Serve a clinical attachment only when it belongs to the signed-in patient."""
    patient = current_user.patient
    owned = (
        Document.query.filter_by(patient_id=patient.id, file_path=filename).first()
        or DiagnosticReport.query.filter_by(patient_id=patient.id, document_path=filename).first()
        or Procedure.query.filter_by(patient_id=patient.id, document_path=filename).first()
        or Immunization.query.filter_by(patient_id=patient.id, document_path=filename).first()
        or ImagingStudy.query.filter_by(patient_id=patient.id, document_path=filename).first()
        or Encounter.query.filter_by(patient_id=patient.id, document_path=filename).first()
    )
    if not owned:
        from flask import abort
        abort(404)
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'], filename,
        as_attachment=request.args.get('download') == '1',
    )


@patient_bp.route('/records/encounter/<encounter_id>')
@patient_required
def encounter_detail(encounter_id):
    patient = current_user.patient
    encounter = Encounter.query.filter_by(id=encounter_id, patient_id=patient.id).first_or_404()
    return render_template('patient/encounter_detail.html', patient=patient, encounter=encounter)


@patient_bp.route('/records/procedure/<procedure_id>')
@patient_required
def procedure_detail(procedure_id):
    patient = current_user.patient
    procedure = Procedure.query.filter_by(id=procedure_id, patient_id=patient.id).first_or_404()
    return render_template('patient/procedure_detail.html', patient=patient, procedure=procedure)


@patient_bp.route('/records/imaging/<imaging_id>')
@patient_required
def imaging_detail(imaging_id):
    patient = current_user.patient
    study = ImagingStudy.query.filter_by(id=imaging_id, patient_id=patient.id).first_or_404()
    return render_template('patient/imaging_detail.html', patient=patient, study=study)


@patient_bp.route('/records/immunization/<immunization_id>')
@patient_required
def immunization_detail(immunization_id):
    patient = current_user.patient
    immunization = Immunization.query.filter_by(id=immunization_id, patient_id=patient.id).first_or_404()
    return render_template('patient/immunization_detail.html', patient=patient, immunization=immunization)


@patient_bp.route('/medications')
@patient_required
def medications():
    patient = current_user.patient
    active_meds = Medication.query.filter_by(patient_id=patient.id, status='active').all()
    past_meds = Medication.query.filter(
        Medication.patient_id == patient.id,
        Medication.status != 'active'
    ).order_by(Medication.start_date.desc()).all()
    uploaded_docs = Document.query.filter_by(
        patient_id=patient.id, document_type='prescription', is_archived=False
    ).order_by(Document.document_date.desc()).all()
    return render_template('patient/medications.html', patient=patient, active_meds=active_meds, past_meds=past_meds, uploaded_docs=uploaded_docs)


@patient_bp.route('/conditions')
@patient_required
def conditions():
    patient = current_user.patient
    uploaded_docs = Document.query.filter_by(
        patient_id=patient.id, document_type='discharge_summary', is_archived=False
    ).order_by(Document.document_date.desc()).all()
    return render_template('patient/conditions.html', patient=patient, uploaded_docs=uploaded_docs)


@patient_bp.route('/allergies')
@patient_required
def allergies():
    patient = current_user.patient
    return render_template('patient/allergies.html', patient=patient)


@patient_bp.route('/vaccinations')
@patient_required
def vaccinations():
    patient = current_user.patient
    uploaded_docs = Document.query.filter_by(
        patient_id=patient.id, document_type='vaccination_record', is_archived=False
    ).order_by(Document.document_date.desc()).all()
    return render_template('patient/vaccinations.html', patient=patient, uploaded_docs=uploaded_docs)


@patient_bp.route('/procedures')
@patient_required
def procedures():
    patient = current_user.patient
    all_procedures = Procedure.query.filter_by(
        patient_id=patient.id
    ).order_by(Procedure.procedure_date.desc()).all()
    uploaded_docs = Document.query.filter_by(
        patient_id=patient.id, document_type='procedure', is_archived=False
    ).order_by(Document.document_date.desc()).all()
    return render_template('patient/procedures.html',
        patient=patient,
        procedures=all_procedures,
        uploaded_docs=uploaded_docs
    )


@patient_bp.route('/health-summary')
@patient_required
def health_summary():
    from datetime import date, timedelta
    patient = current_user.patient
    two_months_ago = date.today() - timedelta(days=60)

    # All-time data
    active_meds       = Medication.query.filter_by(patient_id=patient.id, status='active').all()
    all_conditions    = Condition.query.filter_by(patient_id=patient.id).order_by(Condition.diagnosis_date.desc()).all()
    active_conditions = [c for c in all_conditions if c.status in ['active', 'monitoring']]
    allergies         = Allergy.query.filter_by(patient_id=patient.id).all()
    immunizations     = Immunization.query.filter_by(patient_id=patient.id).order_by(Immunization.vaccination_date.desc()).all()

    # Major condition: prefer severity='severe'/'moderate', then first active
    major_condition = next((c for c in active_conditions if c.severity in ('severe', 'moderate')), None)
    if not major_condition and active_conditions:
        major_condition = active_conditions[0]

    # Last 2 months data
    recent_reports = (DiagnosticReport.query
        .filter(DiagnosticReport.patient_id == patient.id,
                DiagnosticReport.report_date >= two_months_ago)
        .order_by(DiagnosticReport.report_date.desc()).all())

    recent_encounters = (Encounter.query
        .filter(Encounter.patient_id == patient.id,
                Encounter.encounter_date >= two_months_ago)
        .order_by(Encounter.encounter_date.desc()).all())

    recent_procedures = (Procedure.query
        .filter(Procedure.patient_id == patient.id,
                Procedure.procedure_date >= two_months_ago)
        .order_by(Procedure.procedure_date.desc()).all())

    all_procedures = Procedure.query.filter_by(patient_id=patient.id).order_by(Procedure.procedure_date.desc()).all()

    return render_template('patient/health_summary.html',
        patient=patient,
        active_meds=active_meds,
        active_conditions=active_conditions,
        all_conditions=all_conditions,
        major_condition=major_condition,
        allergies=allergies,
        recent_reports=recent_reports,
        recent_encounters=recent_encounters,
        recent_procedures=recent_procedures,
        all_procedures=all_procedures,
        immunizations=immunizations,
        two_months_ago=two_months_ago,
        now=date.today()
    )


@patient_bp.route('/emergency-card')
def emergency_card():
    """Emergency card — accessible without login for emergency situations.
    Only shows minimal pre-approved emergency information."""
    hv_id = request.args.get('id')
    if hv_id:
        from models import HealthIdentity
        identity = HealthIdentity.query.filter_by(hv_id=hv_id).first()
        if identity:
            patient = identity.patient
            return render_template('patient/emergency_card.html', patient=patient, public=True)
    if current_user.is_authenticated and current_user.role == 'patient':
        patient = current_user.patient
        return render_template('patient/emergency_card.html', patient=patient, public=False)
    return render_template('patient/emergency_card_public.html')


@patient_bp.route('/notifications')
@patient_required
def notifications():
    patient = current_user.patient
    all_notifications = Notification.query.filter_by(
        patient_id=patient.id
    ).order_by(Notification.created_at.desc()).all()
    # Mark all as read
    Notification.query.filter_by(patient_id=patient.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return render_template('patient/notifications.html', patient=patient, notifications=all_notifications)


@patient_bp.route('/access-history')
@patient_required
def access_history():
    patient = current_user.patient
    audit_events = AuditEvent.query.filter_by(
        patient_id=patient.id
    ).order_by(AuditEvent.timestamp.desc()).limit(100).all()
    access_requests = AccessRequest.query.filter_by(
        patient_id=patient.id
    ).order_by(AccessRequest.requested_at.desc()).all()
    return render_template('patient/access_history.html',
        patient=patient, audit_events=audit_events, access_requests=access_requests
    )




@patient_bp.route('/settings', methods=['GET', 'POST'])
@patient_required
def settings():
    patient = current_user.patient
    from models import EmergencyProfile
    from datetime import datetime
    
    if request.method == 'POST':
        # Update Patient Profile
        patient.phone = request.form.get('phone')
        patient.address = request.form.get('address')
        patient.city = request.form.get('city')
        patient.state = request.form.get('state')
        patient.blood_group = request.form.get('blood_group')
        patient.biological_sex = request.form.get('biological_sex')
        
        dob_str = request.form.get('date_of_birth')
        if dob_str:
            try:
                patient.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        # Update Emergency Profile
        emergency_profile = EmergencyProfile.query.filter_by(patient_id=patient.id).first()
        if not emergency_profile:
            emergency_profile = EmergencyProfile(patient_id=patient.id)
            db.session.add(emergency_profile)
            
        emergency_profile.emergency_contact_name = request.form.get('em_name')
        emergency_profile.emergency_contact_phone = request.form.get('em_phone')
        emergency_profile.emergency_contact_relation = request.form.get('em_relation')
        emergency_profile.critical_allergies = request.form.get('critical_allergies')
        emergency_profile.critical_medications = request.form.get('critical_medications')
        emergency_profile.major_conditions = request.form.get('major_conditions')
        emergency_profile.special_notes = request.form.get('special_notes')
        emergency_profile.organ_donor = 'organ_donor' in request.form
        
        db.session.commit()
        flash('Profile and emergency settings updated successfully.', 'success')
        
        # Log Audit
        utils.log_audit_event(
            patient_id=patient.id, actor_id=current_user.id,
            actor_name=patient.full_name, action='updated',
            resource_type='patient_profile', resource_description='Updated profile and emergency settings', status='success'
        )
        return redirect(url_for('patient.settings'))
        
    emergency_profile = EmergencyProfile.query.filter_by(patient_id=patient.id).first()
    return render_template('patient/settings.html', patient=patient, emergency=emergency_profile)

@patient_bp.route('/search')
@patient_required
def search():
    patient = current_user.patient
    q = request.args.get('q', '').strip()
    
    if not q:
        return redirect(url_for('patient.dashboard'))
        
    search_term = f"%{q}%"
    
    lab_reports = DiagnosticReport.query.filter(
        DiagnosticReport.patient_id == patient.id,
        DiagnosticReport.report_name.ilike(search_term)
    ).all()
    
    medications = Medication.query.filter(
        Medication.patient_id == patient.id,
        Medication.medicine_name.ilike(search_term)
    ).all()
    
    conditions = Condition.query.filter(
        Condition.patient_id == patient.id,
        Condition.condition_name.ilike(search_term)
    ).all()
    
    documents = Document.query.filter(
        Document.patient_id == patient.id,
        Document.title.ilike(search_term),
        Document.is_archived == False
    ).all()
    
    return render_template('patient/search_results.html', 
                           patient=patient, 
                           query=q, 
                           lab_reports=lab_reports, 
                           medications=medications, 
                           conditions=conditions, 
                           documents=documents)

@patient_bp.route('/provider/<provider_id>')
@patient_required
def provider_profile(provider_id):
    from models import Provider
    provider = Provider.query.get_or_404(provider_id)
    return render_template('patient/provider_profile.html', provider=provider)
