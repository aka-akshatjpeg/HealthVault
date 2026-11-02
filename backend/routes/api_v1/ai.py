from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import json
import markdown
from models import db, ChatMessage, User

ai_v1_bp = Blueprint('ai_v1', __name__)

def get_gemini_client():
    from google import genai
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None, "GEMINI_API_KEY is not set in the .env file."
    client = genai.Client(api_key=api_key)
    return client, None

def _get_patient():
    raw_identity = get_jwt_identity()
    try:
        identity = json.loads(raw_identity) if isinstance(raw_identity, str) else raw_identity
    except (TypeError, json.JSONDecodeError):
        identity = {'user_id': raw_identity, 'role': 'patient'}
    if not isinstance(identity, dict):
        return None, (jsonify({'error': 'Invalid account identity.'}), 401)
    if identity.get('role') != 'patient':
        return None, (jsonify({'error': 'Only patients can use the AI assistant.'}), 403)
    user = db.session.get(User, identity.get('user_id'))
    if not user or not user.patient:
        return None, (jsonify({'error': 'Patient not found.'}), 404)
    return user.patient, None

@ai_v1_bp.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    patient, err = _get_patient()
    if err: return err

    client, err_client = get_gemini_client()
    if err_client:
        return jsonify({'error': err_client}), 500

    data = request.get_json()
    user_message = (data or {}).get('message', '').strip()
    if not user_message:
        return jsonify({'error': 'Message is empty.'}), 400

    # Save user message to DB
    user_chat_msg = ChatMessage(patient_id=patient.id, role='user', content=user_message)
    db.session.add(user_chat_msg)
    db.session.commit()

    context_parts = [
        f"Patient Name: {patient.full_name}",
        f"Date of Birth: {patient.date_of_birth}",
        f"Blood Group: {patient.blood_group or 'Unknown'}",
        f"Biological Sex: {patient.biological_sex or 'Unknown'}",
    ]

    all_conds = [f"{c.condition_name} (status: {c.status}, diagnosed: {c.diagnosis_date or 'unknown'})"
                 for c in patient.conditions]
    if all_conds:
        context_parts.append("Medical Conditions:\n" + "\n".join(f"  - {c}" for c in all_conds))

    all_meds = [f"{m.medicine_name} {m.dosage or ''} {m.frequency or ''}".strip()
                for m in patient.medications if m.status == 'active']
    if all_meds:
        context_parts.append("Current Medications:\n" + "\n".join(f"  - {m}" for m in all_meds))

    allergies = [f"{a.allergen} — severity: {a.severity}, reaction: {a.reaction or 'unknown'}"
                 for a in patient.allergies]
    if allergies:
        context_parts.append("Allergies:\n" + "\n".join(f"  - {a}" for a in allergies))

    from models import DiagnosticReport
    all_reports = DiagnosticReport.query.filter_by(patient_id=patient.id)\
        .order_by(DiagnosticReport.report_date.desc()).all()

    if all_reports:
        lab_sections = []
        for report in all_reports:
            lines = [
                f"Report: {report.report_name}",
                f"  Date: {report.report_date}",
                f"  Lab: {report.laboratory or 'N/A'}",
                f"  Ordered by: {report.ordering_doctor or 'N/A'}",
                f"  Status: {report.status}",
            ]
            if report.summary:
                lines.append(f"  Summary: {report.summary}")
            if report.observations:
                lines.append("  Individual Test Results:")
                for obs in report.observations:
                    flag = ""
                    if obs.interpretation and obs.interpretation.lower() in ('high', 'low', 'critical'):
                        flag = f" — {obs.interpretation.upper()}"
                    ref = f" (ref: {obs.reference_range})" if obs.reference_range else ""
                    lines.append(
                        f"    - {obs.test_name}: {obs.value} {obs.unit or ''}{ref}{flag}"
                    )
            lab_sections.append("\n".join(lines))
        context_parts.append("Lab Reports:\n" + "\n\n".join(lab_sections))

    sys_prompt = (
        "You are HealthVault AI, a helpful, empathetic, and professional medical assistant embedded in a secure patient health platform. "
        f"You are speaking with {patient.full_name}. "
        "Below is the patient's complete health record. Use this data to answer their questions accurately and specifically. "
        "When asked about a specific test, report, or parameter — reference the exact value, unit, and reference range from the data. "
        "Rules: You are NOT a doctor. Always remind the patient to consult their doctor for medical decisions. "
        "Be warm, clear, and concise. Format answers with markdown (bullet points, bold, tables if helpful).\n\n"
        "=== PATIENT HEALTH RECORD ===\n"
        + "\n\n".join(context_parts)
        + "\n=== END OF RECORD ==="
    )

    history = ChatMessage.query.filter_by(patient_id=patient.id).order_by(ChatMessage.timestamp.asc()).all()
    
    contents = []
    for msg in history:
        contents.append({"role": msg.role, "parts": [{"text": msg.content}]})

    try:
        from google.genai import types
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=sys_prompt
            )
        )
        
        model_chat_msg = ChatMessage(patient_id=patient.id, role='model', content=response.text)
        db.session.add(model_chat_msg)
        db.session.commit()

        # Just return markdown for mobile apps
        return jsonify({'response': response.text})
    except Exception as e:
        return jsonify({'error': f"Gemini API Error: {str(e)}"}), 500

@ai_v1_bp.route('/clear-history', methods=['POST'])
@jwt_required()
def clear_history():
    patient, err = _get_patient()
    if err: return err
    ChatMessage.query.filter_by(patient_id=patient.id).delete()
    db.session.commit()
    return jsonify({'success': True}), 200
