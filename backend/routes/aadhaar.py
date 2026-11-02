# =============================================================================
# routes/aadhaar.py — Aadhaar Verification
# =============================================================================
#
# India's real UIDAI Aadhaar OTP API requires a government-issued AUA/KUA
# licence and PKI certificate — it is not publicly accessible.
#
# All endpoints below return HTTP 503 until a real UIDAI integration is wired
# in.  No OTP code is ever generated, stored, or returned in any response.
# The lookup route (used by Doctor/Lab portals) remains functional.
#
# =============================================================================

from flask import Blueprint, request, jsonify
from flask_login import current_user
from models import Patient

aadhaar_bp = Blueprint('aadhaar', __name__, url_prefix='/api/aadhaar')


def _clean_aadhaar(raw: str) -> str:
    """Strip spaces/dashes, return digits only."""
    return ''.join(c for c in (raw or '') if c.isdigit())


_UNAVAILABLE = {'success': False, 'error': 'Aadhaar OTP verification is not yet available.'}


# ---------------------------------------------------------------------------
# POST /api/aadhaar/send-otp
# ---------------------------------------------------------------------------
@aadhaar_bp.route('/send-otp', methods=['POST'])
def send_otp():
    return jsonify(_UNAVAILABLE), 503


# ---------------------------------------------------------------------------
# POST /api/aadhaar/verify-otp
# ---------------------------------------------------------------------------
@aadhaar_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    return jsonify(_UNAVAILABLE), 503


# ---------------------------------------------------------------------------
# POST /api/aadhaar/verify-and-save
# ---------------------------------------------------------------------------
@aadhaar_bp.route('/verify-and-save', methods=['POST'])
def verify_and_save():
    return jsonify(_UNAVAILABLE), 503


# ---------------------------------------------------------------------------
# GET /api/aadhaar/lookup?number=XXXXXXXXXXXX
# Used by Doctor/Lab portals to fetch a patient by verified Aadhaar number.
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
