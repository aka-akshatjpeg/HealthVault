# =============================================================================
# routes/auth.py — Authentication Routes (Login · OTP · Register · Logout)
# =============================================================================
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import random
import string

from models import db, User, Patient, Provider, Organization, HealthIdentity, EmergencyProfile, OTPCode
import utils

auth_bp = Blueprint('auth', __name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _redirect_by_role(role):
    if role == 'patient': return redirect(url_for('patient.dashboard'))
    if role == 'doctor':  return redirect(url_for('doctor.dashboard'))
    if role == 'lab':     return redirect(url_for('lab.dashboard'))
    return redirect(url_for('auth.portal_select'))


def _generate_otp():
    """Return a random 6-digit string."""
    return ''.join(random.choices(string.digits, k=6))


def _create_otp(user_id):
    """Invalidate old OTPs, create a fresh one valid for 10 minutes."""
    OTPCode.query.filter_by(user_id=user_id, used=False).update({'used': True})
    otp = OTPCode(
        user_id=user_id,
        code=_generate_otp(),
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.session.add(otp)
    db.session.commit()
    return otp


# =============================================================================
# LANDING
# =============================================================================
@auth_bp.route('/landing')
def landing():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user.role)
    return render_template('landing.html')


# =============================================================================
# PORTAL SELECTOR  /portal-select
# =============================================================================
@auth_bp.route('/portal-select')
def portal_select():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user.role)
    return render_template('auth/portal_select.html')


# =============================================================================
# LOGIN  /login  (Step 1 — email + password)
# =============================================================================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user.role)

    role = request.args.get('role', '')

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'danger')
                return render_template('auth/login.html', role=role)

            # Generate OTP and store user_id in session for Step 2
            otp = _create_otp(user.id)
            session['otp_user_id'] = user.id
            session['otp_role']    = role

            # In production this would be emailed; for the prototype we display it
            flash(f'Your OTP is: {otp.code}  (valid for 10 minutes)', 'info')
            return redirect(url_for('auth.verify_otp'))

        else:
            flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html', role=role)


# =============================================================================
# OTP VERIFY  /verify-otp  (Step 2)
# =============================================================================
@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user.role)

    user_id = session.get('otp_user_id')
    if not user_id:
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.portal_select'))

    role = session.get('otp_role', '')

    if request.method == 'POST':
        entered = request.form.get('otp', '').strip()

        # Find the latest unused OTP for this user
        otp = OTPCode.query.filter_by(user_id=user_id, used=False)\
                           .order_by(OTPCode.created_at.desc()).first()

        if otp and otp.is_valid() and otp.code == entered:
            otp.used = True
            user = User.query.get(user_id)
            user.last_login = datetime.utcnow()
            db.session.commit()

            # Clear session OTP data
            session.pop('otp_user_id', None)
            session.pop('otp_role', None)

            login_user(user, remember=True)

            if user.role == 'patient' and user.patient:
                utils.log_audit_event(
                    patient_id=user.patient.id,
                    actor_id=user.id,
                    actor_name=user.patient.full_name,
                    action='login',
                    resource_type='account',
                    resource_description='User logged in via OTP',
                    status='success',
                    ip_address=request.remote_addr
                )

            flash('Welcome back!', 'success')
            return _redirect_by_role(user.role)

        elif otp and not otp.is_valid():
            flash('OTP has expired. Please log in again to get a new one.', 'danger')
            session.pop('otp_user_id', None)
            return redirect(url_for('auth.login', role=role))
        else:
            flash('Incorrect OTP. Please try again.', 'danger')

    return render_template('auth/verify_otp.html', role=role)


# =============================================================================
# RESEND OTP
# =============================================================================
@auth_bp.route('/resend-otp')
def resend_otp():
    user_id = session.get('otp_user_id')
    if not user_id:
        return redirect(url_for('auth.portal_select'))

    otp = _create_otp(user_id)
    flash(f'New OTP sent: {otp.code}  (valid for 10 minutes)', 'info')
    return redirect(url_for('auth.verify_otp'))


# =============================================================================
# REGISTER  /register?role=  (Patient · Doctor · Lab)
# =============================================================================
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user.role)

    role = request.args.get('role', 'patient')

    if request.method == 'POST':
        role     = request.form.get('role', 'patient')
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')
        fullname = request.form.get('full_name', '').strip()

        errors = []
        if not fullname:         errors.append('Full name is required.')
        if not email or '@' not in email: errors.append('A valid email is required.')
        if len(password) < 8:    errors.append('Password must be at least 8 characters.')
        if password != confirm:  errors.append('Passwords do not match.')
        if User.query.filter_by(email=email).first():
            errors.append('This email is already registered.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('auth/register.html', role=role)

        pw_hash  = generate_password_hash(password)
        new_user = User(email=email, password_hash=pw_hash, role=role)
        db.session.add(new_user)
        db.session.flush()

        # ── Patient ──────────────────────────────────────────────────────────
        if role == 'patient':
            dob = None
            dob_str = request.form.get('date_of_birth', '')
            if dob_str:
                try: dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
                except ValueError: pass

            patient = Patient(
                user_id=new_user.id,
                full_name=fullname,
                date_of_birth=dob,
                biological_sex=request.form.get('biological_sex', ''),
                blood_group=request.form.get('blood_group', ''),
                phone=request.form.get('phone', '').strip()
            )

            # If Aadhaar was verified in the OTP flow, save it now
            verified_aadhaar = session.pop('aadhaar_verified', None)
            if verified_aadhaar:
                patient.aadhaar_number = verified_aadhaar
                patient.aadhaar_verified = True

            db.session.add(patient)
            db.session.flush()

            hv_id = utils.generate_hv_id()
            db.session.add(HealthIdentity(patient_id=patient.id, hv_id=hv_id))
            db.session.add(EmergencyProfile(patient_id=patient.id))
            db.session.commit()
            utils.generate_qr_code(hv_id, patient.id)
            flash(f'Account created! Your HealthVault ID is {hv_id}. Please log in.', 'success')

        # ── Doctor ────────────────────────────────────────────────────────────
        elif role == 'doctor':
            # Find or create org
            org_name = request.form.get('organization', '').strip()
            org = None
            if org_name:
                org = Organization.query.filter_by(name=org_name).first()
                if not org:
                    org = Organization(name=org_name, type='hospital')
                    db.session.add(org)
                    db.session.flush()

            provider = Provider(
                user_id=new_user.id,
                full_name=fullname,
                specialty=request.form.get('specialty', '').strip(),
                registration_number=request.form.get('registration_number', '').strip(),
                phone=request.form.get('phone', '').strip(),
                organization_id=org.id if org else None
            )
            db.session.add(provider)
            db.session.commit()
            flash('Doctor account created successfully! Please log in.', 'success')

        # ── Lab ───────────────────────────────────────────────────────────────
        elif role == 'lab':
            lab_name = request.form.get('lab_name', '').strip() or fullname

            org = Organization.query.filter_by(name=lab_name, type='lab').first()
            if not org:
                org = Organization(
                    name=lab_name, type='lab',
                    address=request.form.get('address', '').strip(),
                    phone=request.form.get('phone', '').strip(),
                    email=email
                )
                db.session.add(org)
                db.session.flush()

            provider = Provider(
                user_id=new_user.id,
                full_name=fullname,
                phone=request.form.get('phone', '').strip(),
                organization_id=org.id
            )
            db.session.add(provider)
            db.session.commit()
            flash('Laboratory account created! Please log in.', 'success')

        return redirect(url_for('auth.login', role=role))

    return render_template('auth/register.html', role=role)


# =============================================================================
# LOGOUT
# =============================================================================
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('otp_user_id', None)
    session.pop('otp_role', None)
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('auth.portal_select'))
