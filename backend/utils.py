# =============================================================================
# utils.py — Helper Functions
# =============================================================================
#
# WHAT IS THIS FILE?
# A collection of small utility functions used across the app.
# Instead of copy-pasting the same code everywhere, we write it once here
# and import it wherever needed.
# =============================================================================

import random
import string
import qrcode
import os
from datetime import datetime


def generate_hv_id():
    """
    Generate a unique HealthVault ID in the format: HV-IND-XXXX-XXXX
    
    Rules:
    - Must be unique (we check against the database)
    - Human-readable
    - Non-sequential (random, not 001, 002, 003...)
    - Safe to share
    
    Example output: HV-IND-8F42-K92P
    """
    from models import db, HealthIdentity

    # Characters to use — no confusing ones like 0/O, 1/I/L
    chars = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'

    while True:
        # Generate two groups of 4 random characters
        part1 = ''.join(random.choices(chars, k=4))
        part2 = ''.join(random.choices(chars, k=4))
        hv_id = f'HV-IND-{part1}-{part2}'

        # Make sure this ID doesn't already exist in the database
        existing = HealthIdentity.query.filter_by(hv_id=hv_id).first()
        if not existing:
            return hv_id  # Found a unique one!


def generate_share_token():
    """
    Generate a short share token: HV-SHARE-XXXXX
    Example: HV-SHARE-72K91
    """
    from models import db, ShareLink
    chars = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'

    while True:
        token_part = ''.join(random.choices(chars, k=5))
        token = f'HV-SHARE-{token_part}'
        existing = ShareLink.query.filter_by(share_token=token).first()
        if not existing:
            return token


def generate_qr_code(hv_id, patient_id, base_url='http://localhost:5000'):
    """
    Generate a QR code image for a patient's HealthVault ID.
    
    The QR code encodes a full URL pointing to the patient's public
    Health ID card page. Scanning it opens a browser directly.
    
    Saves the image to: uploads/qr_{patient_id}.png
    """
    # Encode a full scannable URL — opens patient's Health ID card in browser
    qr_data = f"{base_url}/patient/health-id/public?id={hv_id}"

    # Create QR code with some styling
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    # Create the image
    img = qr.make_image(fill_color="#1e3a5f", back_color="white")

    # Save to the uploads folder
    uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    qr_path = os.path.join(uploads_dir, f'qr_{patient_id}.png')
    img.save(qr_path)

    # Update the database with the QR code path
    from models import db, HealthIdentity
    identity = HealthIdentity.query.filter_by(patient_id=patient_id).first()
    if identity:
        identity.qr_code_path = f'qr_{patient_id}.png'
        db.session.commit()

    return qr_path


def log_audit_event(patient_id, actor_id, actor_name, action, resource_type,
                    resource_description='', actor_organization='', purpose='',
                    status='success', ip_address=''):
    """
    Log every important action to the audit trail.
    
    This is critical for privacy and security — every time someone
    views, uploads, or shares health data, it's recorded here.
    
    Example:
    "Dr. Sharma viewed Lab Reports at 10:42 PM on 17 Sep 2026"
    """
    from models import db, AuditEvent
    event = AuditEvent(
        patient_id=patient_id,
        actor_id=actor_id,
        actor_name=actor_name,
        actor_organization=actor_organization,
        action=action,
        resource_type=resource_type,
        resource_description=resource_description,
        purpose=purpose,
        status=status,
        ip_address=ip_address,
        timestamp=datetime.utcnow()
    )
    db.session.add(event)
    db.session.commit()


def create_notification(patient_id, title, message, notification_type, related_id=None):
    """
    Create an in-app notification for a patient.
    
    Examples:
    - "City Diagnostics uploaded a new CBC report"
    - "Dr. Sharma requested access to your records"
    - "New login detected on your account"
    """
    from models import db, Notification
    notification = Notification(
        patient_id=patient_id,
        title=title,
        message=message,
        notification_type=notification_type,
        related_id=related_id
    )
    db.session.add(notification)
    db.session.commit()
    return notification


def allowed_file(filename):
    """
    Check if an uploaded file has an allowed extension.
    We only accept: PDF, JPG, JPEG, PNG
    """
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def secure_filename_custom(filename):
    """
    Make a filename safe to save on disk.
    Removes spaces and special characters that could cause issues.
    """
    from werkzeug.utils import secure_filename
    import uuid
    # Get the file extension
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    # Generate a unique name to avoid overwriting existing files
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    return unique_name


def format_file_size(size_bytes):
    """Convert bytes to a human-readable string like '2.3 MB'."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def get_source_badge(source):
    """
    Return a human-readable label and Bootstrap badge color for a record source.
    
    This is used to show WHERE a record came from:
    - Provider = from a doctor or hospital
    - Patient uploaded = the patient uploaded a file
    - Self entered = the patient typed it in manually
    """
    source_map = {
        'provider': ('Verified Provider', 'success'),
        'patient_uploaded': ('Patient Uploaded', 'primary'),
        'self_entered': ('Self Entered', 'secondary'),
        'lab': ('Laboratory', 'info'),
        'imported': ('Imported', 'warning'),
    }
    return source_map.get(source, ('Unknown', 'secondary'))


def build_timeline(patient):
    """
    Build a chronological list of ALL health events for a patient's timeline.
    
    Combines records from all categories (lab reports, consultations,
    vaccinations, etc.) into a single sorted list.
    
    Each timeline item has:
    - date
    - type (e.g. 'lab', 'consultation', 'vaccination')
    - title
    - summary
    - source
    - link (URL to the full record)
    """
    timeline_items = []

    # --- Lab Reports ---
    for report in patient.diagnostic_reports:
        timeline_items.append({
            'date': report.report_date,
            'type': 'lab',
            'icon': 'flask',
            'color': 'info',
            'title': report.report_name,
            'summary': f"Lab: {report.laboratory or 'Unknown'}",
            'source': report.source,
            'organization': report.source_organization or report.laboratory,
            'link': f'/patient/records/lab/{report.id}',
            'id': report.id
        })

    # --- Encounters (Consultations + Hospitalizations) ---
    for encounter in patient.encounters:
        if encounter.encounter_type == 'hospitalization':
            timeline_items.append({
                'date': encounter.encounter_date,
                'type': 'hospitalization',
                'icon': 'hospital',
                'color': 'danger',
                'title': f"Hospitalization: {encounter.reason or 'Admission'}",
                'summary': f"Hospital: {encounter.facility or 'Unknown'}",
                'source': encounter.source,
                'organization': encounter.source_organization or encounter.facility,
                'link': f'/patient/records/encounter/{encounter.id}',
                'id': encounter.id
            })
        else:
            timeline_items.append({
                'date': encounter.encounter_date,
                'type': 'consultation',
                'icon': 'stethoscope',
                'color': 'primary',
                'title': f"Consultation: {encounter.doctor_name or 'Doctor'}",
                'summary': f"{encounter.specialty or 'General'} — {encounter.reason or ''}",
                'source': encounter.source,
                'organization': encounter.source_organization or encounter.facility,
                'link': f'/patient/records/encounter/{encounter.id}',
                'id': encounter.id
            })

    # --- Procedures (Surgeries) ---
    for procedure in patient.procedures:
        timeline_items.append({
            'date': procedure.procedure_date,
            'type': 'procedure',
            'icon': 'scissors',
            'color': 'warning',
            'title': procedure.procedure_name,
            'summary': f"Hospital: {procedure.hospital or 'Unknown'}",
            'source': procedure.source,
            'organization': procedure.source_organization or procedure.hospital,
            'link': f'/patient/records/procedure/{procedure.id}',
            'id': procedure.id
        })

    # --- Vaccinations ---
    for immunization in patient.immunizations:
        timeline_items.append({
            'date': immunization.vaccination_date,
            'type': 'vaccination',
            'icon': 'syringe',
            'color': 'success',
            'title': f"{immunization.vaccine_name} {immunization.dose_number or ''}".strip(),
            'summary': f"Provider: {immunization.provider or 'Unknown'}",
            'source': immunization.source,
            'organization': immunization.source_organization or immunization.provider,
            'link': f'/patient/records/immunization/{immunization.id}',
            'id': immunization.id
        })

    # --- Imaging Studies ---
    for study in patient.imaging_studies:
        timeline_items.append({
            'date': study.study_date,
            'type': 'imaging',
            'icon': 'image',
            'color': 'secondary',
            'title': f"{study.imaging_type}: {study.body_region}",
            'summary': f"Facility: {study.facility or 'Unknown'}",
            'source': study.source,
            'organization': study.source_organization or study.facility,
            'link': f'/patient/records/imaging/{study.id}',
            'id': study.id
        })

    # Sort all items by date, most recent first
    # Items without a date go to the bottom
    timeline_items.sort(
        key=lambda x: x['date'] if x['date'] else datetime.min.date(),
        reverse=True
    )

    return timeline_items
