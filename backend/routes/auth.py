# =============================================================================
# routes/auth.py — Authentication Routes (Firebase web sign-in · Logout)
# =============================================================================
#
# Sign-in policy
# ──────────────
# • Web portal sign-in is exclusively via Firebase (Google, Apple, Phone).
#   The legacy email + password → OTP two-step flow is RETIRED.
#
# Account-creation policy
# ───────────────────────
# • Patient accounts are created automatically on first Firebase phone/email
#   sign-in (see firebase_auth.authenticate_firebase_user).
#   Public self-registration is closed — GET /register redirects to /login;
#   POST /register always returns 410 Gone.
#
# • Doctor / Lab accounts must be provisioned by an authenticated admin.
#   No public route allows a caller to choose a privileged role.
#
# Routes kept
# ───────────
#   GET  /login          → renders the Firebase-only login page
#   POST /login          → flashes a warning (form is gone; kept for bots)
#   POST /firebase-login → exchanges a Firebase ID token for a Flask session
#   GET  /portal-select  → role chooser
#   GET  /register       → 302 → /login  (route kept so old links don't 404)
#   POST /register       → 410 Gone
#   GET  /verify-otp     → 302 → /login  (retired)
#   POST /verify-otp     → 302 → /login  (retired)
#   GET  /resend-otp     → 302 → /login  (retired)
#   GET  /logout
# =============================================================================

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import login_required, login_user, logout_user, current_user

from firebase_auth import (
    FirebaseAccountConflict, FirebaseAccountInactive, FirebaseAuthUnavailable,
    FirebaseProfileRequired, FirebaseTokenInvalid, authenticate_firebase_user,
    record_firebase_login, verify_firebase_token,
)

auth_bp = Blueprint('auth', __name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _redirect_by_role(role):
    if role == 'patient': return redirect(url_for('patient.dashboard'))
    if role == 'doctor':  return redirect(url_for('doctor.dashboard'))
    if role == 'lab':     return redirect(url_for('lab.dashboard'))
    return redirect(url_for('auth.portal_select'))


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
# LOGIN  /login  — Firebase sign-in only
# =============================================================================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user.role)

    role = request.args.get('role', '')

    if request.method == 'POST':
        # The email + password form is retired — reject any form POST.
        flash(
            'Email/password sign-in is no longer available. '
            'Please use one of the sign-in options below.',
            'warning',
        )

    return render_template('auth/login.html', role=role)


# =============================================================================
# FIREBASE SESSION EXCHANGE  POST /firebase-login
# =============================================================================
@auth_bp.route('/firebase-login', methods=['POST'])
def firebase_login():
    """Exchange a Firebase ID token for a Flask web session cookie."""
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
        record_firebase_login(user, 'web', request.remote_addr or '')
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
    login_user(user, remember=True)
    destinations = {
        'patient': 'patient.dashboard',
        'doctor':  'doctor.dashboard',
        'lab':     'lab.dashboard',
    }
    return jsonify({
        'success': True,
        'redirect_url': url_for(destinations.get(user.role, 'auth.portal_select')),
    })


# =============================================================================
# CLOSED: /register
# Public self-registration is not permitted.
# • Patients register via Firebase phone sign-in (authenticate_firebase_user).
# • Providers are provisioned by an authenticated admin (not yet built).
# The GET redirect keeps old inbound links from 404-ing; POST is 410 Gone.
# =============================================================================
@auth_bp.route('/register', methods=['GET'])
def register_redirect():
    flash(
        'Self-registration is closed. '
        'Patient accounts are created on first Firebase sign-in. '
        'Provider accounts are provisioned by an administrator.',
        'info',
    )
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['POST'])
def register():
    """Permanently closed — return 410 Gone for any POST."""
    return (
        'Self-registration is closed. '
        'Patient accounts are created through Firebase sign-in. '
        'Provider accounts require administrator provisioning.',
        410,
        {'Content-Type': 'text/plain'},
    )


# =============================================================================
# RETIRED: /verify-otp and /resend-otp
# =============================================================================
@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    session.pop('otp_user_id', None)
    session.pop('otp_role', None)
    flash('The one-time-code login step has been removed. Please sign in below.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/resend-otp')
def resend_otp():
    session.pop('otp_user_id', None)
    session.pop('otp_role', None)
    return redirect(url_for('auth.login'))


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
