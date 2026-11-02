# routes/api_v1/auth.py — JWT Authentication API
from flask import Blueprint, request, jsonify, session
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from models import db, User, Patient, Provider, Organization, HealthIdentity, EmergencyProfile, OTPCode
import utils, random, string, json

def _make_identity(user_id, role):
    """Encode identity as JSON string (flask-jwt-extended v4 requires string subject)."""
    return json.dumps({'user_id': str(user_id), 'role': role})

def _parse_identity(raw):
    """Decode identity string back to dict."""
    try:
        return json.loads(raw)
    except Exception:
        return {'user_id': raw, 'role': 'patient'}

auth_v1_bp = Blueprint('auth_v1', __name__)


def _generate_otp():
    return ''.join(random.choices(string.digits, k=6))


def _create_otp(user_id):
    OTPCode.query.filter_by(user_id=user_id, used=False).update({'used': True})
    otp = OTPCode(
        user_id=user_id,
        code=_generate_otp(),
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.session.add(otp)
    db.session.commit()
    return otp


# POST /api/v1/auth/login
# Body: { email, password }
# Returns: { otp_pending: true, otp_code: '123456' (demo only) }
@auth_v1_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Invalid email or password.'}), 401
    if not user.is_active:
        return jsonify({'error': 'Account deactivated. Contact support.'}), 403
    otp = _create_otp(user.id)
    # Store user_id in a short-lived way — we use the OTP record itself as the state
    return jsonify({
        'otp_pending': True,
        'user_id': user.id,  # client holds this to pass back with OTP
        'otp_code': otp.code,  # DEMO ONLY: in production, send via email/SMS
        'message': f'OTP sent. Demo OTP: {otp.code}',
        'role': user.role
    })


# POST /api/v1/auth/verify-otp
# Body: { user_id, otp }
# Returns: { access_token, refresh_token, role, user: { id, email, role } }
@auth_v1_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json() or {}
    user_id = data.get('user_id', '')
    entered = str(data.get('otp', '')).strip()
    if not user_id or not entered:
        return jsonify({'error': 'user_id and otp are required.'}), 400
    otp = OTPCode.query.filter_by(user_id=user_id, used=False).order_by(OTPCode.created_at.desc()).first()
    if not otp:
        return jsonify({'error': 'No OTP found. Please log in again.'}), 400
    if not otp.is_valid():
        return jsonify({'error': 'OTP expired. Please log in again.'}), 400
    if otp.code != entered:
        return jsonify({'error': 'Incorrect OTP.'}), 400
    otp.used = True
    user = User.query.get(user_id)
    user.last_login = datetime.utcnow()
    db.session.commit()
    if user.role == 'patient' and user.patient:
        utils.log_audit_event(
            patient_id=user.patient.id, actor_id=user.id,
            actor_name=user.patient.full_name, action='login',
            resource_type='account', resource_description='Mobile app login via OTP', status='success'
        )
    identity = _make_identity(user.id, user.role)
    access_token = create_access_token(identity=identity)
    refresh_token = create_refresh_token(identity=identity)
    user_data = {'id': user.id, 'email': user.email, 'role': user.role}
    if user.role == 'patient' and user.patient:
        p = user.patient
        user_data['full_name'] = p.full_name
        user_data['hv_id'] = p.health_identity.hv_id if p.health_identity else None
    elif user.role in ('doctor', 'lab') and user.provider:
        user_data['full_name'] = user.provider.full_name
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'role': user.role,
        'user': user_data
    })


# POST /api/v1/auth/refresh
# Header: Authorization: Bearer <refresh_token>
@auth_v1_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({'access_token': access_token})


# POST /api/v1/auth/register
# Body: { role, email, password, confirm_password, full_name, date_of_birth?, biological_sex?, blood_group?, phone?, ... }
@auth_v1_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    role = data.get('role', 'patient')
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    confirm = data.get('confirm_password', '')
    fullname = data.get('full_name', '').strip()
    if not fullname:
        return jsonify({'error': 'Full name is required.'}), 400
    if not email or '@' not in email:
        return jsonify({'error': 'A valid email is required.'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters.'}), 400
    if password != confirm:
        return jsonify({'error': 'Passwords do not match.'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'This email is already registered.'}), 409
    pw_hash = generate_password_hash(password)
    new_user = User(email=email, password_hash=pw_hash, role=role)
    db.session.add(new_user)
    db.session.flush()
    hv_id = None
    if role == 'patient':
        dob = None
        dob_str = data.get('date_of_birth', '')
        if dob_str:
            try:
                from datetime import date
                dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        patient = Patient(
            user_id=new_user.id, full_name=fullname,
            date_of_birth=dob,
            biological_sex=data.get('biological_sex', ''),
            blood_group=data.get('blood_group', ''),
            phone=data.get('phone', '').strip()
        )
        db.session.add(patient)
        db.session.flush()
        hv_id = utils.generate_hv_id()
        db.session.add(HealthIdentity(patient_id=patient.id, hv_id=hv_id))
        db.session.add(EmergencyProfile(patient_id=patient.id))
        db.session.commit()
        utils.generate_qr_code(hv_id, patient.id)
    elif role == 'doctor':
        org_name = data.get('organization', '').strip()
        org = None
        if org_name:
            org = Organization.query.filter_by(name=org_name).first()
            if not org:
                org = Organization(name=org_name, type='hospital')
                db.session.add(org)
                db.session.flush()
        provider = Provider(
            user_id=new_user.id, full_name=fullname,
            specialty=data.get('specialty', '').strip(),
            registration_number=data.get('registration_number', '').strip(),
            phone=data.get('phone', '').strip(),
            organization_id=org.id if org else None
        )
        db.session.add(provider)
        db.session.commit()
    elif role == 'lab':
        lab_name = data.get('lab_name', '').strip() or fullname
        org = Organization.query.filter_by(name=lab_name, type='lab').first()
        if not org:
            org = Organization(name=lab_name, type='lab',
                               address=data.get('address', '').strip(),
                               phone=data.get('phone', '').strip(),
                               email=email)
            db.session.add(org)
            db.session.flush()
        provider = Provider(user_id=new_user.id, full_name=fullname,
                            phone=data.get('phone', '').strip(),
                            organization_id=org.id)
        db.session.add(provider)
        db.session.commit()
    # Issue tokens immediately after registration
    identity = _make_identity(new_user.id, role)
    access_token = create_access_token(identity=identity)
    refresh_token = create_refresh_token(identity=identity)
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'role': role,
        'hv_id': hv_id,
        'message': f'Account created! Your HealthVault ID is {hv_id}.' if hv_id else 'Account created.'
    }), 201


# GET /api/v1/auth/me
@auth_v1_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    raw_identity = get_jwt_identity()
    identity = _parse_identity(raw_identity)
    user = User.query.get(identity['user_id'])
    if not user:
        return jsonify({'error': 'User not found.'}), 404
    user_data = {'id': user.id, 'email': user.email, 'role': user.role}
    if user.role == 'patient' and user.patient:
        p = user.patient
        user_data['full_name'] = p.full_name
        user_data['hv_id'] = p.health_identity.hv_id if p.health_identity else None
    elif user.role in ('doctor', 'lab') and user.provider:
        user_data['full_name'] = user.provider.full_name
    return jsonify({'user': user_data})
