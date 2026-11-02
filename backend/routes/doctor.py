# =============================================================================
# routes/doctor.py — Doctor Portal Routes
# =============================================================================
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from models import db, Patient, HealthIdentity, Provider, AccessRequest, Encounter, DiagnosticReport, Medication, Allergy, Condition, Notification
from functools import wraps
from datetime import datetime, timedelta
import utils

doctor_bp = Blueprint('doctor', __name__, url_prefix='/doctor')


def doctor_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != 'doctor':
            flash('Access denied. Doctor account required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@doctor_bp.route('/dashboard')
@doctor_required
def dashboard():
    provider = current_user.provider
    
    # Active Accesses
    active_requests = AccessRequest.query.filter_by(
        provider_id=provider.id,
        status='approved'
    ).filter(AccessRequest.expires_at > datetime.utcnow()).order_by(AccessRequest.requested_at.desc()).all()
    
    # Recent Consultations (History of what prescriptions/notes were given)
    recent_consultations = Encounter.query.filter_by(
        provider_id=provider.id,
        encounter_type='consultation'
    ).order_by(Encounter.encounter_date.desc(), Encounter.created_at.desc()).limit(10).all()
    
    # Stats
    total_patients_seen = db.session.query(Encounter.patient_id).filter_by(provider_id=provider.id).distinct().count()
    today_date = datetime.utcnow().date()
    consultations_today = Encounter.query.filter(
        Encounter.provider_id == provider.id,
        db.func.date(Encounter.created_at) == today_date
    ).count()

    recent_requests = AccessRequest.query.filter_by(
        provider_id=provider.id
    ).order_by(AccessRequest.requested_at.desc()).limit(15).all()

    return render_template('doctor/dashboard.html', 
                           provider=provider, 
                           recent_requests=recent_requests,
                           active_requests=active_requests,
                           recent_consultations=recent_consultations,
                           total_patients=total_patients_seen,
                           consultations_today=consultations_today)


@doctor_bp.route('/search', methods=['GET', 'POST'])
@doctor_required
def patient_search():
    patient = None
    error = None
    
    hv_id = request.args.get('hv_id', '') or request.form.get('hv_id', '')
    aadhaar_raw = request.args.get('aadhaar', '') or request.form.get('aadhaar', '')
    
    search_query = request.args.get('search_query', '') or request.form.get('search_query', '')
    
    if search_query:
        digits_only = ''.join(c for c in search_query if c.isdigit())
        if len(digits_only) == 12:
            aadhaar_raw = digits_only
        else:
            hv_id = search_query

    hv_id = hv_id.strip().upper()
    aadhaar = ''.join(c for c in aadhaar_raw if c.isdigit())

    if aadhaar:
        patient = Patient.query.filter_by(aadhaar_number=aadhaar, aadhaar_verified=True).first()
        if not patient:
            error = f'No verified patient found with Aadhaar ending in ...{aadhaar[-4:]}. Ensure the patient has linked and verified their Aadhaar on HealthVault.'

    elif hv_id:
        identity = HealthIdentity.query.filter_by(hv_id=hv_id).first()
        if identity:
            patient = identity.patient
        else:
            error = f'HealthVault ID "{hv_id}" not found. Please check and try again.'

    if patient:
        active_access = AccessRequest.query.filter_by(
            provider_id=current_user.provider.id,
            patient_id=patient.id,
            status='approved'
        ).filter(AccessRequest.expires_at > datetime.utcnow()).first()

        pending_request = AccessRequest.query.filter_by(
            provider_id=current_user.provider.id,
            patient_id=patient.id,
            status='pending'
        ).first()

        return render_template('doctor/patient_search.html',
                               patient=patient,
                               active_access=active_access,
                               pending_request=pending_request,
                               error=error)

    elif request.method == 'POST':
        if not error:
            error = 'Please enter a HealthVault ID or Aadhaar number.'

    return render_template('doctor/patient_search.html', patient=patient, error=error)




@doctor_bp.route('/request-access/<patient_id>', methods=['GET', 'POST'])
@doctor_required
def request_access(patient_id):
    provider = current_user.provider
    patient = Patient.query.get_or_404(patient_id)

    # Check if there's already an active pending request
    existing = AccessRequest.query.filter_by(
        patient_id=patient_id, provider_id=provider.id, status='pending'
    ).first()
    if existing:
        flash('You already have a pending access request for this patient.', 'warning')
        return redirect(url_for('doctor.patient_search'))

    if request.method == 'POST':
        purpose = request.form.get('purpose', '')
        duration = int(request.form.get('duration', 24))
        categories = request.form.getlist('categories')  # list of selected checkboxes

        if not purpose or not categories:
            flash('Please provide a purpose and select at least one record category.', 'danger')
            return render_template('doctor/request_access.html', patient=patient, provider=provider)

        access_request = AccessRequest(
            patient_id=patient_id,
            provider_id=provider.id,
            purpose=purpose,
            requested_categories=','.join(categories),
            duration_hours=duration,
            status='pending'
        )
        db.session.add(access_request)
        db.session.flush()

        # Notify the patient
        utils.create_notification(
            patient_id=patient_id,
            title='Access Request from Dr. ' + provider.full_name,
            message=f'Dr. {provider.full_name} ({provider.specialty}) is requesting access to your health records for: {purpose}',
            notification_type='access_request',
            related_id=access_request.id
        )

        utils.log_audit_event(
            patient_id=patient_id, actor_id=current_user.id,
            actor_name=provider.full_name,
            actor_organization=provider.organization.name if provider.organization else '',
            action='access_requested', resource_type='multiple',
            resource_description=', '.join(categories),
            purpose=purpose, status='pending'
        )

        db.session.commit()
        flash('Access request sent. The patient will be notified.', 'success')
        return redirect(url_for('doctor.dashboard'))

    return render_template('doctor/request_access.html', patient=patient, provider=provider)


@doctor_bp.route('/patient/<patient_id>/records')
@doctor_required
def patient_records(patient_id):
    provider = current_user.provider
    patient = Patient.query.get_or_404(patient_id)

    # Find active approved access request
    access_request = AccessRequest.query.filter_by(
        patient_id=patient_id, provider_id=provider.id, status='approved'
    ).first()

    if not access_request or access_request.is_expired():
        if access_request and access_request.is_expired():
            access_request.status = 'expired'
            db.session.commit()
        flash('You do not have authorized access to this patient\'s records.', 'danger')
        return redirect(url_for('doctor.patient_search'))

    # Only show the approved categories
    approved_cats = access_request.approved_categories.split(',') if access_request.approved_categories else []

    records = {}
    if 'lab_reports' in approved_cats:
        records['lab_reports'] = DiagnosticReport.query.filter_by(patient_id=patient_id).order_by(DiagnosticReport.report_date.desc()).all()
    if 'medications' in approved_cats:
        records['medications'] = Medication.query.filter_by(patient_id=patient_id).all()
    if 'allergies' in approved_cats:
        records['allergies'] = patient.allergies
    if 'conditions' in approved_cats:
        records['conditions'] = patient.conditions
    if 'vaccinations' in approved_cats:
        records['vaccinations'] = patient.immunizations
    if 'procedures' in approved_cats:
        records['procedures'] = patient.procedures
    if 'encounters' in approved_cats:
        records['encounters'] = patient.encounters

    # Log this access
    utils.log_audit_event(
        patient_id=patient_id, actor_id=current_user.id,
        actor_name=provider.full_name,
        actor_organization=provider.organization.name if provider.organization else '',
        action='viewed', resource_type='authorized_records',
        resource_description=', '.join(approved_cats),
        purpose=access_request.purpose, status='success'
    )

    return render_template('doctor/patient_records.html',
        patient=patient, provider=provider,
        access_request=access_request, approved_cats=approved_cats, records=records
    )


@doctor_bp.route('/patient/<patient_id>/add-consultation', methods=['GET', 'POST'])
@doctor_required
def add_consultation(patient_id):
    provider = current_user.provider
    patient = Patient.query.get_or_404(patient_id)

    # Verify access
    access_request = AccessRequest.query.filter_by(
        patient_id=patient_id, provider_id=provider.id, status='approved'
    ).first()
    if not access_request or access_request.is_expired():
        flash('Authorized access required to add a consultation.', 'danger')
        return redirect(url_for('doctor.patient_search'))

    if request.method == 'POST':
        encounter = Encounter(
            patient_id=patient_id,
            provider_id=provider.id,
            encounter_type='consultation',
            encounter_date=datetime.strptime(request.form.get('encounter_date'), '%Y-%m-%d').date(),
            facility=provider.organization.name if provider.organization else '',
            doctor_name=provider.full_name,
            specialty=provider.specialty,
            reason=request.form.get('reason', ''),
            diagnosis=request.form.get('diagnosis', ''),
            clinical_notes=request.form.get('clinical_notes', ''),
            prescription=request.form.get('prescription', ''),
            follow_up_date=datetime.strptime(request.form.get('follow_up_date'), '%Y-%m-%d').date() if request.form.get('follow_up_date') else None,
            source='provider',
            source_organization=provider.organization.name if provider.organization else 'Unknown'
        )
        db.session.add(encounter)
        db.session.flush()

        utils.create_notification(
            patient_id=patient_id,
            title=f'New consultation added by Dr. {provider.full_name}',
            message=f'Dr. {provider.full_name} added a consultation record dated {encounter.encounter_date}.',
            notification_type='new_consultation',
            related_id=encounter.id
        )

        utils.log_audit_event(
            patient_id=patient_id, actor_id=current_user.id,
            actor_name=provider.full_name,
            actor_organization=provider.organization.name if provider.organization else '',
            action='uploaded', resource_type='consultation',
            resource_description='Consultation record added', status='success'
        )

        db.session.commit()
        flash('Consultation record added successfully.', 'success')
        return redirect(url_for('doctor.patient_records', patient_id=patient_id))

    return render_template('doctor/add_consultation.html', patient=patient, provider=provider)

# =============================================================================
# DOCTOR SETTINGS / PROFILE
# =============================================================================
@doctor_bp.route('/settings', methods=['GET', 'POST'])
@doctor_required
def settings():
    provider = current_user.provider
    if not provider:
        flash('Provider profile not found.', 'danger')
        return redirect(url_for('doctor.dashboard'))

    if request.method == 'POST':
        provider.full_name = request.form.get('full_name', provider.full_name).strip()
        provider.specialty = request.form.get('specialty', provider.specialty or '').strip()
        provider.phone = request.form.get('phone', provider.phone or '').strip()
        provider.registration_number = request.form.get('registration_number', provider.registration_number or '').strip()
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('doctor.settings'))

    return render_template('doctor/settings.html', provider=provider)

@doctor_bp.route('/profile')
@doctor_required
def profile():
    provider = current_user.provider
    return render_template('doctor/profile.html', provider=provider)


@doctor_bp.route('/profile/edit', methods=['GET', 'POST'])
@doctor_required
def edit_profile():
    provider = current_user.provider

    if request.method == 'POST':
        # Update identity/professional info
        provider.full_name = request.form.get('full_name', provider.full_name).strip()
        provider.specialty = request.form.get('specialty', provider.specialty or '').strip()
        provider.qualifications = request.form.get('qualifications', provider.qualifications or '').strip()
        provider.experience_years = request.form.get('experience_years', provider.experience_years, type=int)
        provider.registration_number = request.form.get('registration_number', provider.registration_number or '').strip()
        provider.bio = request.form.get('bio', provider.bio or '').strip()
        provider.languages = request.form.get('languages', provider.languages or '').strip()
        provider.gender = request.form.get('gender', provider.gender or '').strip()

        # Update contact
        provider.phone = request.form.get('phone', provider.phone or '').strip()
        
        # Update consultation
        provider.consultation_fee = request.form.get('consultation_fee', provider.consultation_fee, type=int)
        provider.consultation_type = request.form.get('consultation_type', provider.consultation_type or '').strip()
        
        # Update availability
        provider.working_days = request.form.get('working_days', provider.working_days or '').strip()
        provider.working_hours = request.form.get('working_hours', provider.working_hours or '').strip()
        provider.slot_duration = request.form.get('slot_duration', provider.slot_duration, type=int)
        
        # Update services
        provider.services = request.form.get('services', provider.services or '').strip()

        # Update hospital/clinic details (using existing organization relationship if any, otherwise skip or handle it)
        hospital_name = request.form.get('hospital_name', '').strip()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        pincode = request.form.get('pincode', '').strip()

        if hospital_name:
            if not provider.organization:
                from models import Organization
                new_org = Organization(type='clinic', name=hospital_name)
                db.session.add(new_org)
                db.session.flush()
                provider.organization_id = new_org.id
            
            provider.organization.name = hospital_name
            provider.organization.address = address
            provider.organization.city = city
            provider.organization.state = state
            provider.organization.pincode = pincode

        # Handle Profile Photo upload
        if 'profile_photo' in request.files:
            file = request.files['profile_photo']
            if file and file.filename and file.filename != '':
                ALLOWED = {'jpg', 'jpeg', 'png', 'webp'}
                ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
                if ext in ALLOWED:
                    try:
                        import os, uuid
                        from flask import current_app
                        # Build a unique filename keyed to this provider
                        new_filename = f"doc_{provider.id}_{uuid.uuid4().hex}.{ext}"
                        upload_folder = current_app.config['UPLOAD_FOLDER']
                        os.makedirs(upload_folder, exist_ok=True)
                        new_filepath = os.path.join(upload_folder, new_filename)

                        # Save new file first
                        file.save(new_filepath)

                        # Verify the file actually landed on disk with content
                        if os.path.exists(new_filepath) and os.path.getsize(new_filepath) > 0:
                            old_photo = provider.profile_photo  # keep ref for cleanup
                            provider.profile_photo = new_filename
                            # Commit happens below — if it fails, old_photo is still in DB
                            # We'll delete the old file AFTER successful commit
                        else:
                            # File save produced empty/missing file — do not update DB
                            import logging
                            logging.warning(f"Profile photo save produced empty file: {new_filepath}")
                            flash('Photo could not be saved. Please try a different file.', 'warning')
                            old_photo = None  # skip cleanup
                    except Exception as e:
                        import logging
                        logging.exception(f"Profile photo upload failed for provider {provider.id}: {e}")
                        flash('Photo upload failed. Profile saved without photo change.', 'warning')
                        old_photo = None
                else:
                    flash(f'File type ".{ext}" is not allowed. Please upload a JPG, PNG, or WebP image.', 'warning')
                    old_photo = None
            else:
                old_photo = None  # No file selected — leave existing photo unchanged
        else:
            old_photo = None

        db.session.commit()

        # Only delete old photo file AFTER successful DB commit
        if old_photo and old_photo != provider.profile_photo:
            try:
                import os
                from flask import current_app
                old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], old_photo)
                if os.path.exists(old_path):
                    os.remove(old_path)
            except Exception:
                pass  # Non-critical — file cleanup failure should not affect user experience

        flash('Profile updated successfully.', 'success')
        return redirect(url_for('doctor.profile'))

    return render_template('doctor/edit_profile.html', provider=provider)

@doctor_bp.route('/history')
@doctor_required
def history():
    provider = current_user.provider
    recent_consultations = Encounter.query.filter_by(provider_id=provider.id, encounter_type='consultation').order_by(Encounter.encounter_date.desc(), Encounter.created_at.desc()).all()
    return render_template('doctor/history.html', provider=provider, recent_consultations=recent_consultations)

def _lookup_patient(identifier, id_type='hv_id'):
    from models import HealthIdentity
    if not identifier:
        return None
    if id_type == 'hv_id':
        identity = HealthIdentity.query.filter_by(hv_id=identifier).first()
    elif id_type == 'aadhaar':
        identifier = ''.join(filter(str.isdigit, identifier))
        if len(identifier) != 12:
            return None
        from models import Patient
        patient = Patient.query.filter_by(aadhaar_number=identifier, aadhaar_verified=True).first()
        return patient
    return identity.patient if identity and id_type == 'hv_id' else None

@doctor_bp.route('/add-condition', methods=['GET', 'POST'])
@doctor_required
def add_condition():
    provider = current_user.provider
    patient = None
    error = None

    hv_id = request.args.get('hv_id', '').strip() or request.form.get('hv_id', '').strip()
    aadhaar = request.args.get('aadhaar', '').strip() or request.form.get('aadhaar', '').strip()

    if aadhaar:
        patient = _lookup_patient(aadhaar, 'aadhaar')
        if not patient:
            error = "No verified patient found with that Aadhaar number."
    elif hv_id:
        patient = _lookup_patient(hv_id, 'hv_id')
        if not patient:
            error = "No patient found with that HealthVault ID."
            
    if patient:
        # Check if doctor has access
        access_request = AccessRequest.query.filter_by(
            patient_id=patient.id, provider_id=provider.id, status='approved'
        ).first()
        if not access_request or access_request.is_expired():
            error = "You do not have active access to this patient's records."
            patient = None

    if request.method == 'POST' and patient:
        from datetime import datetime
        from models import Condition
        
        condition_name = request.form.get('condition_name', '').strip()
        diagnosis_date_str = request.form.get('diagnosis_date')
        status = request.form.get('status', 'active')
        severity = request.form.get('severity', 'mild')
        notes = request.form.get('notes', '').strip()

        if condition_name:
            diagnosis_date = None
            if diagnosis_date_str:
                try:
                    diagnosis_date = datetime.strptime(diagnosis_date_str, '%Y-%m-%d').date()
                except ValueError:
                    pass
                    
            new_cond = Condition(
                patient_id=patient.id,
                condition_name=condition_name,
                diagnosis_date=diagnosis_date,
                status=status,
                severity=severity,
                treating_doctor=provider.full_name,
                notes=notes,
                source='provider',
                source_organization=provider.organization
            )
            db.session.add(new_cond)
            
            # Log audit event
            utils.log_audit_event(
                patient_id=patient.id, actor_id=current_user.id,
                actor_name=provider.full_name, action='created',
                resource_type='condition', resource_description=condition_name, status='success'
            )
            
            db.session.commit()
            flash('Condition successfully added to patient records.', 'success')
            return redirect(url_for('doctor.add_condition', hv_id=patient.health_identity.hv_id))
        else:
            error = "Condition name is required."

    return render_template('doctor/add_condition.html', provider=provider, patient=patient, hv_id=hv_id, aadhaar=aadhaar, error=error)

@doctor_bp.route('/add-medication', methods=['GET', 'POST'])
@doctor_required
def add_medication():
    provider = current_user.provider
    patient = None
    error = None

    hv_id = request.args.get('hv_id', '').strip() or request.form.get('hv_id', '').strip()
    aadhaar = request.args.get('aadhaar', '').strip() or request.form.get('aadhaar', '').strip()

    if aadhaar:
        patient = _lookup_patient(aadhaar, 'aadhaar')
        if not patient:
            error = "No verified patient found with that Aadhaar number."
    elif hv_id:
        patient = _lookup_patient(hv_id, 'hv_id')
        if not patient:
            error = "No patient found with that HealthVault ID."
            
    if patient:
        # Check if doctor has access
        access_request = AccessRequest.query.filter_by(
            patient_id=patient.id, provider_id=provider.id, status='approved'
        ).first()
        if not access_request or access_request.is_expired():
            error = "You do not have active access to this patient's records."
            patient = None

    if request.method == 'POST' and patient:
        from datetime import datetime
        from models import Medication
        
        medicine_name = request.form.get('medicine_name', '').strip()
        dosage = request.form.get('dosage', '').strip()
        frequency = request.form.get('frequency', '').strip()
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        status = request.form.get('status', 'active')
        notes = request.form.get('notes', '').strip()

        if medicine_name:
            start_date = None
            if start_date_str:
                try:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                except ValueError:
                    pass

            end_date = None
            if end_date_str:
                try:
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                except ValueError:
                    pass
                    
            new_med = Medication(
                patient_id=patient.id,
                medicine_name=medicine_name,
                dosage=dosage,
                frequency=frequency,
                start_date=start_date,
                end_date=end_date,
                status=status,
                prescribing_doctor=provider.full_name,
                notes=notes,
                source='provider',
                source_organization=provider.organization
            )
            db.session.add(new_med)
            
            # Log audit event
            utils.log_audit_event(
                patient_id=patient.id, actor_id=current_user.id,
                actor_name=provider.full_name, action='created',
                resource_type='medication', resource_description=medicine_name, status='success'
            )
            
            db.session.commit()
            flash('Medication successfully added to patient records.', 'success')
            return redirect(url_for('doctor.add_medication', hv_id=patient.health_identity.hv_id))
        else:
            error = "Medicine name is required."

    return render_template('doctor/add_medication.html', provider=provider, patient=patient, hv_id=hv_id, aadhaar=aadhaar, error=error)


