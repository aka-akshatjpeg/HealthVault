# =============================================================================
# models.py — Database Tables
# =============================================================================
#
# WHAT IS THIS FILE?
# This file defines all the "tables" in our database using Python classes.
# Instead of writing SQL like:
#   CREATE TABLE users (id INTEGER, email TEXT, ...)
# We write Python classes and Flask-SQLAlchemy creates the tables for us.
#
# Each class = one table in the database
# Each variable inside the class = one column in that table
# =============================================================================

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import uuid

# db is our database connection object — we import this everywhere we need the database
db = SQLAlchemy()


def generate_uuid():
    """Generate a random unique ID for each record."""
    return str(uuid.uuid4())


# =============================================================================
# USER TABLE
# Stores login information for ALL users (patients, doctors, labs, admins)
# =============================================================================
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)  # NEVER store plain password
    role = db.Column(db.String(20), nullable=False)  # 'patient', 'doctor', 'lab', 'admin'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relationships — tell SQLAlchemy how tables connect to each other
    patient = db.relationship('Patient', backref='user', uselist=False, cascade='all, delete-orphan')
    provider = db.relationship('Provider', backref='user', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


# =============================================================================
# ORGANIZATION TABLE
# Hospitals, clinics, diagnostic labs, pharmacies
# =============================================================================
class Organization(db.Model):
    __tablename__ = 'organizations'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50))  # 'hospital', 'clinic', 'lab', 'pharmacy'
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Organization {self.name}>'


# =============================================================================
# PROVIDER TABLE
# Doctors and other healthcare professionals
# =============================================================================
class Provider(db.Model):
    __tablename__ = 'providers'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'))
    full_name = db.Column(db.String(200), nullable=False)
    specialty = db.Column(db.String(100))
    registration_number = db.Column(db.String(50))  # Medical council registration
    phone = db.Column(db.String(20))
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organization = db.relationship('Organization', backref='providers')

    def __repr__(self):
        return f'<Provider {self.full_name}>'


# =============================================================================
# PATIENT TABLE
# The patient's health profile — personal and medical details
# =============================================================================
class Patient(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    date_of_birth = db.Column(db.Date)
    biological_sex = db.Column(db.String(10))  # 'male', 'female', 'other'
    blood_group = db.Column(db.String(5))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    profile_photo = db.Column(db.String(255))  # path to photo file
    abha_id = db.Column(db.String(20))  # ABHA (Ayushman Bharat) ID — optional
    aadhaar_number = db.Column(db.String(12), unique=True)   # 12-digit Aadhaar number
    aadhaar_verified = db.Column(db.Boolean, default=False)  # True after OTP verification
    abha_id = db.Column(db.String(20))  # ABHA (Ayushman Bharat) ID — optional
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships — all health records linked to this patient
    health_identity = db.relationship('HealthIdentity', backref='patient', uselist=False, cascade='all, delete-orphan')
    conditions = db.relationship('Condition', backref='patient', cascade='all, delete-orphan', order_by='Condition.diagnosis_date.desc()')
    allergies = db.relationship('Allergy', backref='patient', cascade='all, delete-orphan')
    medications = db.relationship('Medication', backref='patient', cascade='all, delete-orphan', order_by='Medication.start_date.desc()')
    diagnostic_reports = db.relationship('DiagnosticReport', backref='patient', cascade='all, delete-orphan', order_by='DiagnosticReport.report_date.desc()')
    procedures = db.relationship('Procedure', backref='patient', cascade='all, delete-orphan', order_by='Procedure.procedure_date.desc()')
    immunizations = db.relationship('Immunization', backref='patient', cascade='all, delete-orphan', order_by='Immunization.vaccination_date.desc()')
    imaging_studies = db.relationship('ImagingStudy', backref='patient', cascade='all, delete-orphan', order_by='ImagingStudy.study_date.desc()')
    documents = db.relationship('Document', backref='patient', cascade='all, delete-orphan', order_by='Document.document_date.desc()')
    encounters = db.relationship('Encounter', backref='patient', cascade='all, delete-orphan', order_by='Encounter.encounter_date.desc()')
    access_requests = db.relationship('AccessRequest', backref='patient', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='patient', cascade='all, delete-orphan', order_by='Notification.created_at.desc()')
    emergency_profile = db.relationship('EmergencyProfile', backref='patient', uselist=False, cascade='all, delete-orphan')
    family_history = db.relationship('FamilyHistory', backref='patient', cascade='all, delete-orphan')

    def age(self):
        """Calculate current age from date of birth."""
        if self.date_of_birth:
            today = datetime.today()
            dob = self.date_of_birth
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return None

    def __repr__(self):
        return f'<Patient {self.full_name}>'


# =============================================================================
# HEALTH IDENTITY TABLE
# The HealthVault ID and QR code for each patient
# =============================================================================
class HealthIdentity(db.Model):
    __tablename__ = 'health_identities'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    patient_id = db.Column(db.String(36), db.ForeignKey('patients.id'), nullable=False)
    hv_id = db.Column(db.String(20), unique=True, nullable=False)  # e.g. HV-IND-8F42-K92P
    qr_code_path = db.Column(db.String(255))  # path to generated QR image
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<HealthIdentity {self.hv_id}>'


# =============================================================================
# EMERGENCY PROFILE TABLE
# Minimal critical information shown in emergencies (without full access)
# =============================================================================
class EmergencyProfile(db.Model):
    __tablename__ = 'emergency_profiles'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    patient_id = db.Column(db.String(36), db.ForeignKey('patients.id'), nullable=False)
    critical_allergies = db.Column(db.Text)       # e.g. "Penicillin (anaphylaxis)"
    critical_medications = db.Column(db.Text)     # e.g. "Aspirin 75mg daily"
    major_conditions = db.Column(db.Text)         # e.g. "Type 2 Diabetes"
    emergency_contact_name = db.Column(db.String(200))
    emergency_contact_phone = db.Column(db.String(20))
    emergency_contact_relation = db.Column(db.String(50))
    organ_donor = db.Column(db.Boolean, default=False)
    special_notes = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<EmergencyProfile for patient {self.patient_id}>'


# =============================================================================
# CONDITION TABLE
# Medical diagnoses and conditions (maps to FHIR Condition resource)
# =============================================================================
class Condition(db.Model):
    __tablename__ = 'conditions'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    patient_id = db.Column(db.String(36), db.ForeignKey('patients.id'), nullable=False)
    condition_name = db.Column(db.String(200), nullable=False)
    diagnosis_date = db.Column(db.Date)
    status = db.Column(db.String(20))     # 'active', 'resolved', 'monitoring', 'unknown'
    severity = db.Column(db.String(20))   # 'mild', 'moderate', 'severe'
    treating_doctor = db.Column(db.String(200))
    notes = db.Column(db.Text)
    # Provenance — where did this record come from?
    source = db.Column(db.String(50), default='self_entered')  # 'provider', 'patient_uploaded', 'self_entered'
    source_organization = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Condition {self.condition_name}>'


# =============================================================================
# ALLERGY TABLE
# Allergies and intolerances (maps to FHIR AllergyIntolerance)
# =============================================================================
class Allergy(db.Model):
    __tablename__ = 'allergies'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    patient_id = db.Column(db.String(36), db.ForeignKey('patients.id'), nullable=False)
    allergen = db.Column(db.String(200), nullable=False)   # e.g. "Penicillin"
    reaction = db.Column(db.String(200))                   # e.g. "Mild rash"
    severity = db.Column(db.String(20))                    # 'mild', 'moderate', 'severe', 'life-threatening'
    date_identified = db.Column(db.Date)
    notes = db.Column(db.Text)
    source = db.Column(db.String(50), default='self_entered')
    source_organization = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Allergy {self.allergen}>'


# =============================================================================
# MEDICATION TABLE
# Current and past medications (maps to FHIR MedicationStatement)
# =============================================================================
class Medication(db.Model):
    __tablename__ = 'medications'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    patient_id = db.Column(db.String(36), db.ForeignKey('patients.id'), nullable=False)
    medicine_name = db.Column(db.String(200), nullable=False)
    dosage = db.Column(db.String(100))          # e.g. "10mg"
    frequency = db.Column(db.String(100))       # e.g. "Once daily at night"
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    prescribing_doctor = db.Column(db.String(200))
    status = db.Column(db.String(20), default='active')  # 'active', 'completed', 'stopped', 'unknown'
    notes = db.Column(db.Text)
    source = db.Column(db.String(50), default='self_entered')
    source_organization = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Medication {self.medicine_name}>'


# =============================================================================
# DIAGNOSTIC REPORT TABLE
# Lab test reports (e.g. CBC, Lipid Profile) — maps to FHIR DiagnosticReport
# Each report can have multiple individual test results (Observations)
# =============================================================================
class DiagnosticReport(db.Model):
    __tablename__ = 'diagnostic_reports'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    patient_id = db.Column(db.String(36), db.ForeignKey('patients.id'), nullable=False)
    report_name = db.Column(db.String(200), nullable=False)  # e.g. "CBC Blood Test"
    report_date = db.Column(db.Date, nullable=False)
    laboratory = db.Column(db.String(200))
    ordering_doctor = db.Column(db.String(200))
    status = db.Column(db.String(20), default='final')  # 'final', 'preliminary', 'amended'
    summary = db.Column(db.Text)                         # Overall findings
    document_path = db.Column(db.String(255))            # Path to PDF report
    source = db.Column(db.String(50), default='patient_uploaded')
    source_organization = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Each report has multiple individual test results
    observations = db.relationship('Observation', backref='report', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<DiagnosticReport {self.report_name} on {self.report_date}>'


# =============================================================================
# OBSERVATION TABLE
# Individual test results within a lab report (maps to FHIR Observation)
# Example: Hemoglobin = 13.8 g/dL (Normal)
# =============================================================================
class Observation(db.Model):
    __tablename__ = 'observations'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    report_id = db.Column(db.String(36), db.ForeignKey('diagnostic_reports.id'), nullable=False)
    test_name = db.Column(db.String(200), nullable=False)    # e.g. "Hemoglobin"
    value = db.Column(db.String(50))                          # e.g. "13.8"
    unit = db.Column(db.String(30))                           # e.g. "g/dL"
    reference_range = db.Column(db.String(50))                # e.g. "13.0 - 17.0"
    is_abnormal = db.Column(db.Boolean, default=False)        # True if outside normal range
    interpretation = db.Column(db.String(20))                 # 'normal', 'high', 'low', 'critical'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Observation {self.test_name}: {self.value} {self.unit}>'


# =============================================================================
# PROCEDURE TABLE
# Surgeries and medical procedures (maps to FHIR Procedure)
# =============================================================================
class Procedure(db.Model):
    __tablename__ = 'procedures'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    patient_id = db.Column(db.String(36), db.ForeignKey('patients.id'), nullable=False)
    procedure_name = db.Column(db.String(200), nullable=False)   # e.g. "Appendectomy"
    procedure_date = db.Column(db.Date)
    hospital = db.Column(db.String(200))
    surgeon = db.Column(db.String(200))
    indication = db.Column(db.Text)    # Why it was done
    outcome = db.Column(db.Text)       # Result/recovery
    notes = db.Column(db.Text)
    document_path = db.Column(db.String(255))
    source = db.Column(db.String(50), default='patient_uploaded')
    source_organization = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Procedure {self.procedure_name}>'


# =============================================================================
# IMMUNIZATION TABLE
# Vaccination records (maps to FHIR Immunization)
# =============================================================================
class Immunization(db.Model):
    __tablename__ = 'immunizations'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    patient_id = db.Column(db.String(36), db.ForeignKey('patients.id'), nullable=False)
    vaccine_name = db.Column(db.String(200), nullable=False)
    dose_number = db.Column(db.String(20))         # e.g. "Dose 1", "Booster"
    vaccination_date = db.Column(db.Date)
    provider = db.Column(db.String(200))            # Where/who administered
    batch_number = db.Column(db.String(50))
    next_dose_date = db.Column(db.Date)
    document_path = db.Column(db.String(255))       # Certificate/proof
    source = db.Column(db.String(50), default='self_entered')
    source_organization = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Immunization {self.vaccine_name}>'


# =============================================================================
# IMAGING STUDY TABLE
# X-rays, CT scans, MRIs, Ultrasounds (maps to FHIR ImagingStudy)
# =============================================================================
class ImagingStudy(db.Model):
    __tablename__ = 'imaging_studies'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    patient_id = db.Column(db.String(36), db.ForeignKey('patients.id'), nullable=False)
    imaging_type = db.Column(db.String(50))         # 'X-ray', 'CT', 'MRI', 'Ultrasound'
    body_region = db.Column(db.String(100))         # e.g. "Chest", "Abdomen"
    study_date = db.Column(db.Date)
    facility = db.Column(db.String(200))
    radiologist = db.Column(db.String(200))
    findings = db.Column(db.Text)                   # Radiology report
    document_path = db.Column(db.String(255))
    source = db.Column(db.String(50), default='patient_uploaded')
    source_organization = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ImagingStudy {self.imaging_type} - {self.body_region}>'


# =============================================================================
# ENCOUNTER TABLE
# Clinical visits and consultations (maps to FHIR Encounter)
# =============================================================================
class Encounter(db.Model):
    __tablename__ = 'encounters'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    patient_id = db.Column(db.String(36), db.ForeignKey('patients.id'), nullable=False)
    provider_id = db.Column(db.String(36), db.ForeignKey('providers.id'))
    encounter_type = db.Column(db.String(50))       # 'consultation', 'hospitalization', 'emergency'
    encounter_date = db.Column(db.Date, nullable=False)
    facility = db.Column(db.String(200))
    doctor_name = db.Column(db.String(200))
    specialty = db.Column(db.String(100))
    reason = db.Column(db.Text)                     # Chief complaint
    diagnosis = db.Column(db.Text)
    clinical_notes = db.Column(db.Text)
    prescription = db.Column(db.Text)
    follow_up_date = db.Column(db.Date)
    # Hospitalization specific
    admission_date = db.Column(db.Date)
    discharge_date = db.Column(db.Date)
    discharge_summary = db.Column(db.Text)
    document_path = db.Column(db.String(255))
    source = db.Column(db.String(50), default='provider')
    source_organization = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    provider = db.relationship('Provider', backref='encounters')

    def __repr__(self):
        return f'<Encounter {self.encounter_type} on {self.encounter_date}>'


# =============================================================================
# DOCUMENT TABLE
# Uploaded files — PDFs, images of reports, etc. (maps to FHIR DocumentReference)
# =============================================================================
class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    patient_id = db.Column(db.String(36), db.ForeignKey('patients.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    document_type = db.Column(db.String(50))        # 'lab_report', 'prescription', 'discharge_summary', etc.
    document_date = db.Column(db.Date)
    provider = db.Column(db.String(200))
    file_path = db.Column(db.String(255), nullable=False)
    file_name = db.Column(db.String(255))
    file_type = db.Column(db.String(20))            # 'pdf', 'jpg', 'png'
    file_size = db.Column(db.Integer)               # in bytes
    tags = db.Column(db.String(500))                # comma-separated tags
    source = db.Column(db.String(50), default='patient_uploaded')
    source_organization = db.Column(db.String(200))
    is_archived = db.Column(db.Boolean, default=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Document {self.title}>'


# =============================================================================
# FAMILY HISTORY TABLE
# Family medical history
# =============================================================================
class FamilyHistory(db.Model):
    __tablename__ = 'family_history'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    patient_id = db.Column(db.String(36), db.ForeignKey('patients.id'), nullable=False)
    relative = db.Column(db.String(100))            # e.g. "Father", "Mother"
    condition = db.Column(db.String(200))
    age_at_onset = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<FamilyHistory {self.relative}: {self.condition}>'


# =============================================================================
# ACCESS REQUEST TABLE
# A doctor requests access to a patient's records (consent workflow)
# =============================================================================
class AccessRequest(db.Model):
    __tablename__ = 'access_requests'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    patient_id = db.Column(db.String(36), db.ForeignKey('patients.id'), nullable=False)
    provider_id = db.Column(db.String(36), db.ForeignKey('providers.id'), nullable=False)
    purpose = db.Column(db.String(200))             # e.g. "Medical consultation"
    requested_categories = db.Column(db.String(500))  # comma-separated: "lab_reports,medications"
    duration_hours = db.Column(db.Integer, default=24)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'denied', 'revoked', 'expired'
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    approved_categories = db.Column(db.String(500))  # What the patient actually approved

    provider = db.relationship('Provider', backref='access_requests')

    def is_expired(self):
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return True
        return False

    def __repr__(self):
        return f'<AccessRequest from {self.provider_id} to patient {self.patient_id}>'


# =============================================================================
# SHARE LINK TABLE
# Time-limited links to share specific records with anyone
# =============================================================================
class ShareLink(db.Model):
    __tablename__ = 'share_links'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    patient_id = db.Column(db.String(36), db.ForeignKey('patients.id'), nullable=False)
    share_token = db.Column(db.String(20), unique=True, nullable=False)  # e.g. HV-SHARE-72K91
    shared_categories = db.Column(db.String(500))
    purpose = db.Column(db.String(200))
    recipient_name = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    access_count = db.Column(db.Integer, default=0)

    patient = db.relationship('Patient', backref='share_links')

    def is_expired(self):
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return f'<ShareLink {self.share_token}>'


# =============================================================================
# AUDIT EVENT TABLE
# Every access to patient data is logged here (maps to FHIR AuditEvent)
# This is critical for privacy and security
# =============================================================================
class AuditEvent(db.Model):
    __tablename__ = 'audit_events'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    patient_id = db.Column(db.String(36), db.ForeignKey('patients.id'))
    actor_id = db.Column(db.String(36))             # User ID of who did the action
    actor_name = db.Column(db.String(200))          # Name for display
    actor_organization = db.Column(db.String(200))
    action = db.Column(db.String(50))               # 'viewed', 'uploaded', 'shared', 'approved', 'denied', 'revoked'
    resource_type = db.Column(db.String(50))        # 'lab_reports', 'medications', 'documents', etc.
    resource_description = db.Column(db.String(200))
    purpose = db.Column(db.String(200))
    status = db.Column(db.String(20))               # 'success', 'denied', 'expired'
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship('Patient', backref='audit_events')

    def __repr__(self):
        return f'<AuditEvent {self.action} by {self.actor_name} at {self.timestamp}>'


# =============================================================================
# NOTIFICATION TABLE
# In-app notifications for patients
# =============================================================================
class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    patient_id = db.Column(db.String(36), db.ForeignKey('patients.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text)
    notification_type = db.Column(db.String(50))    # 'new_report', 'access_request', 'access_approved', etc.
    is_read = db.Column(db.Boolean, default=False)
    related_id = db.Column(db.String(36))           # ID of the related record (e.g. report ID)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Notification {self.title}>'

class OTPCode(db.Model):
    __tablename__ = 'otp_codes'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='otp_codes')

    def is_valid(self):
        from datetime import datetime as dt
        return not self.used and dt.utcnow() < self.expires_at

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    patient_id = db.Column(db.String(36), db.ForeignKey('patients.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class AadhaarOTP(db.Model):
    __tablename__ = 'aadhaar_otps'
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    aadhaar_number = db.Column(db.String(12), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_valid(self):
        from datetime import datetime as dt
        return not self.used and dt.utcnow() < self.expires_at

