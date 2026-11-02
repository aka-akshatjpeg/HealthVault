# routes/api_v1/auth.py — JWT Authentication API
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from datetime import datetime
from models import db, User, Patient, Provider, Organization, HealthIdentity, EmergencyProfile
from firebase_auth import (
    FirebaseAccountConflict, FirebaseAccountInactive, FirebaseAuthUnavailable,
    FirebaseLinkRejected, FirebaseProfileRequired, FirebaseTokenInvalid, authenticate_firebase_user,
    link_firebase_phone_account, record_firebase_login, verify_firebase_token,
)
import utils, json

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


# ---------------------------------------------------------------------------
# REMOVED — demo email/password login
# POST /api/v1/auth/login → 410 Gone
# The mobile app must not use password auth. Use /firebase-login instead.
# ---------------------------------------------------------------------------
@auth_v1_bp.route('/login', methods=['POST'])
def login():
    return jsonify({
        'error': 'This endpoint has been removed. '
                 'Use POST /api/v1/auth/firebase-login with a Firebase ID token.'
    }), 410


# ---------------------------------------------------------------------------
# REMOVED — demo OTP verification
# POST /api/v1/auth/verify-otp → 410 Gone
# OTP is now handled entirely by Firebase on the mobile client.
# ---------------------------------------------------------------------------
@auth_v1_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    return jsonify({
        'error': 'This endpoint has been removed. '
                 'Use POST /api/v1/auth/firebase-login with a Firebase ID token.'
    }), 410


# POST /api/v1/auth/firebase-login
# Body: { id_token: <Firebase ID token>, full_name?: string }
# Returns: { access_token, refresh_token, role, user }
@auth_v1_bp.route('/firebase-login', methods=['POST'])
def firebase_login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'A JSON object is required.'}), 400
    id_token = data.get('id_token')
    if not isinstance(id_token, str) or not id_token.strip():
        return jsonify({'error': 'A Firebase ID token is required.'}), 400
    profile = {'full_name': data.get('full_name', '')}
    try:
        claims = verify_firebase_token(id_token.strip())
        user = authenticate_firebase_user(claims, profile)
        record_firebase_login(user, 'mobile', request.remote_addr or '')
    except FirebaseAuthUnavailable:
        return jsonify({'error': 'Firebase authentication is not configured on the server.'}), 503
    except FirebaseTokenInvalid:
        return jsonify({'error': 'The Firebase sign-in token is invalid or expired.'}), 401
    except FirebaseProfileRequired as exc:
        return jsonify({'error': 'profile_required', 'required_fields': exc.fields}), 422
    except FirebaseAccountConflict as exc:
        return jsonify({'error': str(exc)}), 409
    except FirebaseAccountInactive:
        return jsonify({'error': 'This HealthVault account is deactivated.'}), 403
    identity = _make_identity(user.id, user.role)
    user_data = {'id': user.id, 'email': user.public_email, 'role': user.role}
    if user.role == 'patient' and user.patient:
        user_data['full_name'] = user.patient.full_name
        user_data['hv_id'] = user.patient.health_identity.hv_id if user.patient.health_identity else None
    elif user.role in ('doctor', 'lab') and user.provider:
        user_data['full_name'] = user.provider.full_name
    return jsonify({
        'access_token': create_access_token(identity=identity),
        'refresh_token': create_refresh_token(identity=identity),
        'role': user.role,
        'user': user_data,
    })


# POST /api/v1/auth/firebase-link
# Existing users prove their current password and complete Firebase phone
# verification. The account's existing HealthVault role is preserved.
@auth_v1_bp.route('/firebase-link', methods=['POST'])
def firebase_link():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'A JSON object is required.'}), 400
    id_token = data.get('id_token')
    email = data.get('email')
    password = data.get('password')
    if not all(isinstance(value, str) and value.strip() for value in (id_token, email, password)):
        return jsonify({'error': 'Firebase token, account email, and current password are required.'}), 400
    try:
        claims = verify_firebase_token(id_token.strip())
        user = link_firebase_phone_account(claims, email, password)
        record_firebase_login(user, 'mobile account-link', request.remote_addr or '')
    except FirebaseAuthUnavailable:
        return jsonify({'error': 'Firebase authentication is not configured on the server.'}), 503
    except FirebaseTokenInvalid:
        return jsonify({'error': 'The Firebase phone verification is invalid or expired.'}), 401
    except FirebaseLinkRejected:
        return jsonify({'error': 'The account credentials could not be confirmed.'}), 401
    except FirebaseAccountConflict as exc:
        return jsonify({'error': str(exc)}), 409
    except FirebaseAccountInactive:
        return jsonify({'error': 'This HealthVault account is deactivated.'}), 403

    identity = _make_identity(user.id, user.role)
    user_data = {'id': user.id, 'email': user.public_email, 'role': user.role}
    if user.role == 'patient' and user.patient:
        user_data['full_name'] = user.patient.full_name
        user_data['hv_id'] = user.patient.health_identity.hv_id if user.patient.health_identity else None
    elif user.role in ('doctor', 'lab') and user.provider:
        user_data['full_name'] = user.provider.full_name
    return jsonify({
        'access_token': create_access_token(identity=identity),
        'refresh_token': create_refresh_token(identity=identity),
        'role': user.role,
        'user': user_data,
    })


# POST /api/v1/auth/refresh
# Header: Authorization: Bearer <refresh_token>
@auth_v1_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({'access_token': access_token})


# ---------------------------------------------------------------------------
# CLOSED — unauthenticated account creation via the mobile API is disabled.
#
# New PATIENT accounts are created automatically by /firebase-login when a
# Firebase-verified phone/Google/Apple credential is presented for the first
# time.  No unauthenticated caller should be able to choose a role or receive
# a token through this route.
#
# PROVIDER (doctor/lab) accounts must be provisioned by an authenticated admin
# through the web portal — not through the mobile API.
# ---------------------------------------------------------------------------
@auth_v1_bp.route('/register', methods=['POST'])
def register():
    return jsonify({
        'error': 'Self-registration via this endpoint is closed. '
                 'Patients: sign in with Firebase (phone, Google, or Apple). '
                 'Providers: contact your HealthVault administrator.'
    }), 410


# GET /api/v1/auth/me
@auth_v1_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    raw_identity = get_jwt_identity()
    identity = _parse_identity(raw_identity)
    user = db.session.get(User, identity['user_id'])
    if not user:
        return jsonify({'error': 'User not found.'}), 404
    user_data = {'id': user.id, 'email': user.public_email, 'role': user.role}
    if user.role == 'patient' and user.patient:
        p = user.patient
        user_data['full_name'] = p.full_name
        user_data['hv_id'] = p.health_identity.hv_id if p.health_identity else None
    elif user.role in ('doctor', 'lab') and user.provider:
        user_data['full_name'] = user.provider.full_name
    return jsonify({'user': user_data})
