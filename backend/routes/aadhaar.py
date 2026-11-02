# =============================================================================
# routes/aadhaar.py — Aadhaar Verification Simulation
# =============================================================================
#
# NOTE: India's real UIDAI Aadhaar OTP API (Authentication API) requires
# a government-issued AUA/KUA licence and a PKI certificate. It is NOT
# publicly accessible for prototypes.
#
# This module SIMULATES the UIDAI flow exactly:
#   1.  Client sends a 12-digit Aadhaar number → we "dispatch" an OTP
#   2.  OTP is shown on screen (in a real app UIDAI sends it to the
#       mobile linked to Aadhaar, which we cannot do here)
#   3.  Client submits the 6-digit OTP → we verify & mark the Aadhaar
#
# The UI clearly labels every step as "Demo Simulation — not real UIDAI".
# =============================================================================

from flask import Blueprint, request, jsonify, session
from flask_login import current_user
from models import db, AadhaarOTP, Patient
from datetime import datetime, timedelta
import random

aadhaar_bp = Blueprint('aadhaar', __name__, url_prefix='/api/aadhaar')


def _clean_aadhaar(raw: str) -> str:
    """Strip spaces/dashes, return digits only."""
    return ''.join(c for c in (raw or '') if c.isdigit())


# ---------------------------------------------------------------------------
# POST /api/aadhaar/send-otp
# Body: { "aadhaar_number": "XXXXXXXXXXXX" }
# Generates a 6-digit OTP valid for 10 minutes and returns it (demo only).
# ---------------------------------------------------------------------------
@aadhaar_bp.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json() or {}
    aadhaar = _clean_aadhaar(data.get('aadhaar_number', ''))

    # Validate length
    if len(aadhaar) != 12:
        return jsonify({'success': False, 'error': 'Aadhaar number must be exactly 12 digits.'}), 400

    # Reject numbers that are obviously invalid (all same digit, sequential)
    if len(set(aadhaar)) == 1:
        return jsonify({'success': False, 'error': 'Invalid Aadhaar number.'}), 400

    # Check if already verified and linked to another patient
    existing = Patient.query.filter_by(aadhaar_number=aadhaar, aadhaar_verified=True).first()
    if existing:
        # Allow the owner themselves to re-verify
        if not (current_user.is_authenticated and current_user.role == 'patient'
                and current_user.patient and current_user.patient.id == existing.id):
            return jsonify({'success': False, 'error': 'This Aadhaar number is already linked to another HealthVault account.'}), 409

    # Invalidate any previous unused OTPs for this number
    AadhaarOTP.query.filter_by(aadhaar_number=aadhaar, used=False).update({'used': True})
    db.session.commit()

    # Generate OTP
    code = str(random.randint(100000, 999999))
    otp_record = AadhaarOTP(
        aadhaar_number=aadhaar,
        code=code,
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.session.add(otp_record)
    db.session.commit()

    # In production: UIDAI sends OTP to the registered mobile — we cannot do that.
    # We return the OTP in the response for demo purposes.
    return jsonify({
        'success': True,
        'otp': code,   # DEMO ONLY — remove in production
        'message': f'[DEMO] OTP sent to Aadhaar-linked mobile. Your demo OTP is: {code}',
        'expires_in': 600
    })


# ---------------------------------------------------------------------------
# POST /api/aadhaar/verify-otp
# Body: { "aadhaar_number": "XXXXXXXXXXXX", "otp": "123456" }
# Verifies the OTP; if valid, marks the Aadhaar as verified in session.
# Actual saving to the Patient record is done by the form submit.
# ---------------------------------------------------------------------------
@aadhaar_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json() or {}
    aadhaar = _clean_aadhaar(data.get('aadhaar_number', ''))
    entered  = str(data.get('otp', '')).strip()

    if len(aadhaar) != 12 or not entered:
        return jsonify({'success': False, 'error': 'Aadhaar number and OTP are required.'}), 400

    otp_record = (
        AadhaarOTP.query
        .filter_by(aadhaar_number=aadhaar, used=False)
        .order_by(AadhaarOTP.created_at.desc())
        .first()
    )

    if not otp_record:
        return jsonify({'success': False, 'error': 'No OTP found. Please request a new one.'}), 400

    if not otp_record.is_valid():
        return jsonify({'success': False, 'error': 'OTP has expired. Please request a new one.'}), 400

    if otp_record.code != entered:
        return jsonify({'success': False, 'error': 'Incorrect OTP. Please try again.'}), 400

    # Mark OTP used
    otp_record.used = True
    db.session.commit()

    # Store verified aadhaar in session so the subsequent form POST can trust it
    session['aadhaar_verified'] = aadhaar

    return jsonify({'success': True, 'message': 'Aadhaar verified successfully!'})


# ---------------------------------------------------------------------------
# POST /api/aadhaar/verify-and-save
# For authenticated patients updating their Aadhaar in Account Settings.
# Body: { "aadhaar_number": "XXXXXXXXXXXX", "otp": "123456" }
# ---------------------------------------------------------------------------
@aadhaar_bp.route('/verify-and-save', methods=['POST'])
def verify_and_save():
    if not current_user.is_authenticated or current_user.role != 'patient':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    data = request.get_json() or {}
    aadhaar = _clean_aadhaar(data.get('aadhaar_number', ''))
    entered  = str(data.get('otp', '')).strip()

    if len(aadhaar) != 12 or not entered:
        return jsonify({'success': False, 'error': 'Aadhaar number and OTP are required.'}), 400

    # Check not already used by another verified account
    existing = Patient.query.filter_by(aadhaar_number=aadhaar, aadhaar_verified=True).first()
    if existing and existing.id != current_user.patient.id:
        return jsonify({'success': False, 'error': 'This Aadhaar is already linked to another account.'}), 409

    otp_record = (
        AadhaarOTP.query
        .filter_by(aadhaar_number=aadhaar, used=False)
        .order_by(AadhaarOTP.created_at.desc())
        .first()
    )

    if not otp_record or not otp_record.is_valid():
        return jsonify({'success': False, 'error': 'OTP expired or not found. Request a new one.'}), 400

    if otp_record.code != entered:
        return jsonify({'success': False, 'error': 'Incorrect OTP.'}), 400

    # Mark OTP used and save Aadhaar to Patient
    otp_record.used = True
    patient = current_user.patient
    patient.aadhaar_number = aadhaar
    patient.aadhaar_verified = True
    db.session.commit()

    return jsonify({'success': True, 'message': 'Aadhaar linked and verified successfully!', 'masked': f'XXXX-XXXX-{aadhaar[-4:]}'})


# ---------------------------------------------------------------------------
# GET /api/aadhaar/lookup?number=XXXXXXXXXXXX
# Used by Doctor/Lab portals to fetch a patient by Aadhaar number.
# ---------------------------------------------------------------------------
@aadhaar_bp.route('/lookup', methods=['GET'])
def lookup():
    if not current_user.is_authenticated or current_user.role not in ('doctor', 'lab', 'admin'):
        return jsonify({'error': 'Unauthorized'}), 403

    raw = request.args.get('number', '')
    aadhaar = _clean_aadhaar(raw)

    if len(aadhaar) != 12:
        return jsonify({'error': 'Invalid Aadhaar number.'}), 400

    patient = Patient.query.filter_by(aadhaar_number=aadhaar, aadhaar_verified=True).first()
    if not patient:
        return jsonify({'error': 'No verified patient found with this Aadhaar number.'}), 404

    hi = patient.health_identity
    return jsonify({
        'found': True,
        'patient_id': patient.id,
        'full_name': patient.full_name,
        'hv_id': hi.hv_id if hi else None,
        'date_of_birth': str(patient.date_of_birth) if patient.date_of_birth else None,
        'blood_group': patient.blood_group,
        'aadhaar_masked': f'XXXX-XXXX-{aadhaar[-4:]}',
    })
