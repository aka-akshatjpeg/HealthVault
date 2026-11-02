# =============================================================================
# routes/lab.py — Diagnostic Lab Portal Routes  (fully rebuilt)
# =============================================================================
from flask import (Blueprint, render_template, redirect, url_for,
                   request, flash, current_app)
from flask_login import login_required, current_user
from models import db, Patient, HealthIdentity, DiagnosticReport, Observation, Document, Provider
from functools import wraps
from datetime import datetime, date
import utils, os

lab_bp = Blueprint('lab', __name__, url_prefix='/lab')


# ─── Auth decorator ──────────────────────────────────────────────────────────
def lab_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != 'lab':
            flash('Access denied. Lab account required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# ─── Lookup helper ───────────────────────────────────────────────────────────
def _lookup_patient(hv_id=None, aadhaar=None, search_query=None):
    """Return (patient, error_msg) from a Health ID or Aadhaar string."""
    if search_query:
        digits_only = ''.join(c for c in search_query if c.isdigit())
        if len(digits_only) == 12:
            aadhaar = digits_only
        else:
            hv_id = search_query

    hv_id = (hv_id or '').strip().upper()
    aadhaar_raw = (aadhaar or '').strip()
    aadhaar_clean = ''.join(c for c in aadhaar_raw if c.isdigit())

    if aadhaar_clean:
        patient = Patient.query.filter_by(aadhaar_number=aadhaar_clean, aadhaar_verified=True).first()
        if patient:
            return patient, None
        return None, f'No verified patient found with Aadhaar ending in ...{aadhaar_clean[-4:]}.'

    if hv_id:
        identity = HealthIdentity.query.filter_by(hv_id=hv_id).first()
        if identity:
            return identity.patient, None
        return None, f'No patient found with HealthVault ID: {hv_id}'
    
    return None, None


# ─── Dashboard ───────────────────────────────────────────────────────────────
@lab_bp.route('/dashboard')
@lab_required
def dashboard():
    provider = current_user.provider
    lab_name = provider.organization.name if provider and provider.organization else ''

    recent_reports = (DiagnosticReport.query
        .filter_by(source_organization=lab_name, source='lab')
        .order_by(DiagnosticReport.created_at.desc())
        .limit(20).all())

    # Stats for dashboard
    from datetime import timedelta
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    total_reports   = DiagnosticReport.query.filter_by(source_organization=lab_name, source='lab').count()
    reports_today   = DiagnosticReport.query.filter_by(source_organization=lab_name, source='lab').filter(
        DiagnosticReport.report_date == today).count()
    reports_this_week = DiagnosticReport.query.filter_by(source_organization=lab_name, source='lab').filter(
        DiagnosticReport.report_date >= week_ago).count()
    reports_this_month = DiagnosticReport.query.filter_by(source_organization=lab_name, source='lab').filter(
        DiagnosticReport.report_date >= month_ago).count()

    return render_template('lab/dashboard.html',
        provider=provider,
        lab_name=lab_name,
        recent_reports=recent_reports,
        total_reports=total_reports,
        reports_today=reports_today,
        reports_this_week=reports_this_week,
        reports_this_month=reports_this_month,
    )


# ─── Patient Lookup (AJAX / GET) ─────────────────────────────────────────────
@lab_bp.route('/lookup-patient')
@lab_required
def lookup_patient():
    hv_id = request.args.get('hv_id', '')
    aadhaar = request.args.get('aadhaar', '')
    search_query = request.args.get('search_query', '')
    patient, error = _lookup_patient(hv_id=hv_id, aadhaar=aadhaar, search_query=search_query)
    return render_template('lab/patient_card.html', patient=patient, error=error, hv_id=hv_id, aadhaar=aadhaar)


# ─── Add Report (full page with file upload) ─────────────────────────────────
@lab_bp.route('/add-report', methods=['GET', 'POST'])
@lab_required
def add_report():
    provider  = current_user.provider
    lab_name  = provider.organization.name if provider and provider.organization else 'Unknown Lab'
    hv_id     = request.args.get('hv_id', '') or request.form.get('hv_id', '')
    aadhaar   = request.args.get('aadhaar', '') or request.form.get('aadhaar', '')
    search_query = request.args.get('search_query', '') or request.form.get('search_query', '')
    patient, error = _lookup_patient(hv_id=hv_id, aadhaar=aadhaar, search_query=search_query)

    if request.method == 'POST' and patient and not error:
        # ── Collect form data ──────────────────────────────────────────────
        report_name     = request.form.get('report_name', '').strip()
        report_date_str = request.form.get('report_date', '')
        ordering_doctor = request.form.get('ordering_doctor', '').strip()
        summary         = request.form.get('summary', '').strip()
        status          = request.form.get('status', 'final')

        try:
            report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()
        except ValueError:
            report_date = date.today()

        if not report_name:
            flash('Report name is required.', 'danger')
            return render_template('lab/add_report.html',
                provider=provider, patient=patient, error=error, hv_id=hv_id)

        # ── Handle file upload ─────────────────────────────────────────────
        doc_path = None
        uploaded_file = request.files.get('report_file')
        if uploaded_file and uploaded_file.filename:
            if utils.allowed_file(uploaded_file.filename):
                filename  = utils.secure_filename_custom(uploaded_file.filename)
                filepath  = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                uploaded_file.save(filepath)
                file_size = os.path.getsize(filepath)
                file_ext  = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
                doc_path  = filename

                # Save as Document record too
                doc = Document(
                    patient_id=patient.id,
                    title=report_name,
                    document_type='lab_report',
                    document_date=report_date,
                    provider=lab_name,
                    file_path=filename,
                    file_name=uploaded_file.filename,
                    file_type=file_ext,
                    file_size=file_size,
                    source='lab',
                    source_organization=lab_name,
                )
                db.session.add(doc)
            else:
                flash('Invalid file type. Please upload PDF, JPG, or PNG.', 'danger')
                return render_template('lab/add_report.html',
                    provider=provider, patient=patient, error=error, hv_id=hv_id)

        # ── Create DiagnosticReport ────────────────────────────────────────
        report = DiagnosticReport(
            patient_id=patient.id,
            report_name=report_name,
            report_date=report_date,
            laboratory=lab_name,
            ordering_doctor=ordering_doctor,
            summary=summary,
            status=status,
            document_path=doc_path,
            source='lab',
            source_organization=lab_name,
        )
        db.session.add(report)
        db.session.flush()

        # ── Individual test observations ───────────────────────────────────
        test_names    = request.form.getlist('test_name[]')
        test_values   = request.form.getlist('test_value[]')
        test_units    = request.form.getlist('test_unit[]')
        test_ranges   = request.form.getlist('test_range[]')
        test_abnormal = request.form.getlist('test_abnormal[]')  # list of row indices

        for i, tname in enumerate(test_names):
            if tname.strip():
                obs = Observation(
                    report_id=report.id,
                    test_name=tname.strip(),
                    value=test_values[i].strip()   if i < len(test_values)   else '',
                    unit=test_units[i].strip()     if i < len(test_units)    else '',
                    reference_range=test_ranges[i].strip() if i < len(test_ranges) else '',
                    is_abnormal=(str(i) in test_abnormal),
                    interpretation='high' if (str(i) in test_abnormal) else 'normal',
                )
                db.session.add(obs)

        # ── Notification & audit ──────────────────────────────────────────
        utils.create_notification(
            patient_id=patient.id,
            title=f'New Lab Report: {report_name}',
            message=f'{lab_name} has added a new {report_name} report dated {report_date.strftime("%d %b %Y")}.',
            notification_type='new_report',
            related_id=report.id,
        )
        utils.log_audit_event(
            patient_id=patient.id, actor_id=current_user.id,
            actor_name=provider.full_name or lab_name,
            actor_organization=lab_name,
            action='uploaded', resource_type='lab_report',
            resource_description=report_name, status='success',
        )

        db.session.commit()
        flash(f'✓ Report "{report_name}" successfully added to {patient.full_name}\'s HealthVault.', 'success')
        return redirect(url_for('lab.dashboard'))

    return render_template('lab/add_report.html',
        provider=provider, patient=patient, error=error, hv_id=hv_id, aadhaar=aadhaar, search_query=search_query,
        today=date.today().isoformat()
    )

@lab_bp.route('/report/<report_id>/view')
@lab_required
def view_report(report_id):
    from flask import send_from_directory
    report = DiagnosticReport.query.get_or_404(report_id)
    if report.document_path:
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], report.document_path)
    flash('No document file attached to this report.', 'warning')
    return redirect(url_for('lab.dashboard'))


@lab_bp.route('/profile')
@lab_required
def profile():
    provider = current_user.provider
    return render_template('lab/profile.html', provider=provider)

@lab_bp.route('/profile/edit', methods=['GET', 'POST'])
@lab_required
def edit_profile():
    provider = current_user.provider

    if request.method == 'POST':
        # Update provider identity
        provider.full_name = request.form.get('lab_name', provider.full_name).strip()
        provider.bio = request.form.get('about', provider.bio or '').strip()
        provider.phone = request.form.get('phone', provider.phone or '').strip()

        # Handle Logo/Profile image upload
        if 'profile_photo' in request.files:
            file = request.files['profile_photo']
            if file.filename != '':
                import utils
                if utils.allowed_file(file.filename):
                    import os
                    from flask import current_app
                    filename = utils.secure_filename_custom(file.filename)
                    filename = f"lab_{provider.id}_{filename}"
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    provider.profile_photo = filename

        # Update lab organization details
        if not provider.organization:
            from models import Organization
            from models import db
            new_org = Organization(type='lab', name=provider.full_name)
            db.session.add(new_org)
            db.session.flush()
            provider.organization_id = new_org.id
        
        org = provider.organization
        org.name = provider.full_name
        org.address = request.form.get('address', org.address or '').strip()
        org.city = request.form.get('city', org.city or '').strip()
        org.state = request.form.get('state', org.state or '').strip()
        org.pincode = request.form.get('pincode', org.pincode or '').strip()
        
        org.email = request.form.get('email', org.email or '').strip()
        org.website = request.form.get('website', org.website or '').strip()
        
        org.opening_hours = request.form.get('opening_hours', org.opening_hours or '').strip()
        org.closing_hours = request.form.get('closing_hours', org.closing_hours or '').strip()
        org.working_days = request.form.get('working_days', org.working_days or '').strip()
        org.emergency_hours = request.form.get('emergency_hours', org.emergency_hours or '').strip()
        
        org.services_offered = request.form.get('services_offered', org.services_offered or '').strip()
        org.tests_available = request.form.get('tests_available', org.tests_available or '').strip()
        
        from models import db
        db.session.commit()
        from flask import flash, redirect, url_for
        flash('Laboratory profile updated successfully.', 'success')
        return redirect(url_for('lab.profile'))

    return render_template('lab/edit_profile.html', provider=provider)
