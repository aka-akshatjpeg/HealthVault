# =============================================================================
# seed.py — Demo Data
# =============================================================================
#
# WHAT IS THIS FILE?
# This file fills the database with realistic demo data so you can
# immediately see HealthVault working without manually entering records.
#
# HOW TO RUN IT:
# 1. Make sure your virtual environment is activated
# 2. Run: python seed.py
#
# IMPORTANT: Running this twice will not duplicate data because we check
# if accounts already exist before creating them.
# =============================================================================

import sys
import os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from models import db, User, Patient, HealthIdentity, Organization, Provider
from models import Condition, Allergy, Medication, DiagnosticReport, Observation
from models import Procedure, Immunization, ImagingStudy, Encounter
from models import EmergencyProfile, FamilyHistory, Document, Notification, AuditEvent
from werkzeug.security import generate_password_hash
from datetime import date, datetime, timedelta
import utils


def seed_database():
    app = create_app()
    with app.app_context():
        print("\n🌱 Seeding HealthVault database with demo data...")
        print("=" * 60)

        # ======================================================================
        # ORGANIZATIONS
        # ======================================================================
        print("\n📍 Creating organizations...")

        hospital = Organization.query.filter_by(name='Example General Hospital').first()
        if not hospital:
            hospital = Organization(
                name='Example General Hospital',
                type='hospital',
                address='42 Medical Avenue, Connaught Place',
                city='New Delhi',
                state='Delhi',
                phone='+91-11-4000-0000',
                email='info@examplehospital.demo',
                is_verified=True
            )
            db.session.add(hospital)

        lab_org = Organization.query.filter_by(name='City Diagnostics').first()
        if not lab_org:
            lab_org = Organization(
                name='HealthCare Diagnostics',
                type='lab',
                address='15 Health Street, Lajpat Nagar',
                city='Varanasi',
                state='Uttar Pradesh',
                pincode='221002',
                phone='+91-11-5000-0000',
                email='reports@healthcarediag.demo',
                is_verified=True,
                opening_hours='7:00 AM',
                closing_hours='8:00 PM',
                working_days='Monday-Sunday',
                services_offered='Pathology, Biochemistry, Microbiology',
                tests_available='CBC, Blood Sugar, Lipid Profile, Liver Function Test, Kidney Function Test, Thyroid Profile, Urine Analysis'
            )
            lab_org2 = Organization(
                name='Mediscan Diagnostics',
                type='lab',
                address='20 Scan Avenue',
                city='Varanasi',
                state='Uttar Pradesh',
                pincode='221003',
                phone='+91-11-5000-0001',
                email='reports@mediscan.demo',
                is_verified=True,
                services_offered='Pathology, Biochemistry, Hormone Tests, Preventive Health Packages'
            )
            db.session.add(lab_org2)
            db.session.add(lab_org)

        clinic = Organization.query.filter_by(name='CityCare Heart Institute').first()
        if not clinic:
            clinic = Organization(
                name='CityCare Heart Institute',
                type='clinic',
                address='10 Heart Blvd',
                city='Varanasi',
                state='Uttar Pradesh',
                pincode='221005',
                phone='+91-11-4000-0000',
                email='contact@citycare.demo',
                is_verified=True
            )
            db.session.add(clinic)

        clinic2 = Organization.query.filter_by(name='HealthFirst Clinic').first()
        if not clinic2:
            clinic2 = Organization(
                name='HealthFirst Clinic',
                type='clinic',
                address='42 Wellness Ave, Sector 4',
                city='Varanasi',
                state='Uttar Pradesh',
                pincode='221001',
                phone='+91-11-4000-0001',
                email='contact@healthfirst.demo',
                is_verified=True
            )
            db.session.add(clinic2)
            
        db.session.flush()
        print("   ✅ Organizations created")

        # ======================================================================
        # DEMO ACCOUNTS
        # ======================================================================
        print("\n👤 Creating demo user accounts...")

        # --- PATIENT ---
        patient_user = User.query.filter_by(email='patient@demo.healthvault').first()
        if not patient_user:
            patient_user = User(
                email='patient@demo.healthvault',
                password_hash=generate_password_hash('DemoPassword123!'),
                role='patient',
                is_active=True
            )
            db.session.add(patient_user)
            db.session.flush()

            patient = Patient(
                user_id=patient_user.id,
                full_name='Akshat Sharma',
                date_of_birth=date(1995, 3, 14),
                biological_sex='male',
                blood_group='B+',
                phone='+91-98765-43210',
                address='Flat 4B, Sunrise Apartments, Sector 15',
                city='New Delhi',
                state='Delhi'
            )
            db.session.add(patient)
            db.session.flush()

            # Assign HealthVault ID
            health_identity = HealthIdentity(
                patient_id=patient.id,
                hv_id='HV-IND-8F42-K92P'
            )
            db.session.add(health_identity)
            db.session.flush()

            # Emergency Profile
            emergency = EmergencyProfile(
                patient_id=patient.id,
                critical_allergies='Penicillin (Mild rash)',
                critical_medications='Atorvastatin 10mg (nightly)',
                major_conditions='Pre-diabetes (monitoring)',
                emergency_contact_name='Sunita Sharma',
                emergency_contact_phone='+91-98765-11111',
                emergency_contact_relation='Mother',
                organ_donor=False,
                special_notes='Patient carries no specific implants. No known latex allergy.'
            )
            db.session.add(emergency)
            print("   ✅ Patient: Akshat Sharma (patient@demo.healthvault)")

        # --- DOCTOR ---
        doctor_user = User.query.filter_by(email='doctor@demo.healthvault').first()
        if not doctor_user:
            doctor_user = User(
                email='doctor@demo.healthvault',
                password_hash=generate_password_hash('DemoPassword123!'),
                role='doctor',
                is_active=True
            )
            db.session.add(doctor_user)
            db.session.flush()

            doctor_provider = Provider(
                user_id=doctor_user.id,
                organization_id=clinic.id,
                full_name='Dr. Ananya Sharma',
                specialty='Cardiologist',
                registration_number='MCI-12345-DEMO',
                phone='+91-98765-00001',
                gender='Female',
                qualifications='MBBS, MD, DM Cardiology',
                experience_years=12,
                consultation_fee=800,
                consultation_type='Both',
                working_days='Monday-Saturday',
                working_hours='10:00 AM - 2:00 PM, 5:00 PM - 8:00 PM',
                slot_duration=15,
                services='Cardiology consultation, ECG consultation, Heart health assessment, Follow-up consultation',
                is_verified=True
            )
            doctor_user2 = User(
                email='doctor2@demo.healthvault',
                password_hash=generate_password_hash('DemoPassword123!'),
                role='doctor',
                is_active=True
            )
            db.session.add(doctor_user2)
            db.session.flush()
            doctor_provider2 = Provider(
                user_id=doctor_user2.id,
                organization_id=clinic2.id,
                full_name='Dr. Rahul Mehta',
                specialty='General Physician',
                registration_number='MCI-67890-DEMO',
                phone='+91-98765-00002',
                gender='Male',
                qualifications='MBBS, MD',
                experience_years=8,
                consultation_fee=500,
                consultation_type='In-person',
                working_days='Monday-Saturday',
                working_hours='10:00 AM - 6:00 PM',
                slot_duration=20,
                is_verified=True
            )
            db.session.add(doctor_provider2)
            db.session.add(doctor_provider)
            print("   ✅ Doctor: Dr. Ananya Sharma (doctor@demo.healthvault)")

        # --- LAB ---
        lab_user = User.query.filter_by(email='lab@demo.healthvault').first()
        if not lab_user:
            lab_user = User(
                email='lab@demo.healthvault',
                password_hash=generate_password_hash('DemoPassword123!'),
                role='lab',
                is_active=True
            )
            db.session.add(lab_user)
            db.session.flush()

            lab_provider = Provider(
                user_id=lab_user.id,
                organization_id=lab_org.id,
                full_name='HealthCare Diagnostics',
                specialty='Diagnostic Laboratory',
                is_verified=True
            )
            
            lab_user2 = User(
                email='lab2@demo.healthvault',
                password_hash=generate_password_hash('DemoPassword123!'),
                role='lab',
                is_active=True
            )
            db.session.add(lab_user2)
            db.session.flush()
            lab_provider2 = Provider(
                user_id=lab_user2.id,
                organization_id=lab_org2.id,
                full_name='Mediscan Diagnostics',
                specialty='Diagnostic Laboratory',
                is_verified=True
            )
            db.session.add(lab_provider2)
            db.session.add(lab_provider)
            print("   ✅ Lab: City Diagnostics (lab@demo.healthvault)")

        # --- ADMIN ---
        admin_user = User.query.filter_by(email='admin@demo.healthvault').first()
        if not admin_user:
            admin_user = User(
                email='admin@demo.healthvault',
                password_hash=generate_password_hash('DemoPassword123!'),
                role='admin',
                is_active=True
            )
            db.session.add(admin_user)
            print("   ✅ Admin: admin@demo.healthvault")

        db.session.commit()

        # ======================================================================
        # HEALTH RECORDS FOR AKSHAT
        # ======================================================================
        # Re-query patient after commit
        patient_user = User.query.filter_by(email='patient@demo.healthvault').first()
        patient = patient_user.patient if patient_user else None

        if patient and not patient.allergies:
            print("\n🏥 Adding health records for Akshat Sharma...")

            # ---- ALLERGIES ----
            allergies_data = [
                Allergy(
                    patient_id=patient.id,
                    allergen='Penicillin',
                    reaction='Mild rash and itching',
                    severity='mild',
                    date_identified=date(2018, 6, 10),
                    notes='Experienced mild rash during antibiotic course in 2018. Documented by Dr. Sharma.',
                    source='provider',
                    source_organization='Sharma Clinic'
                ),
                Allergy(
                    patient_id=patient.id,
                    allergen='Dust mites',
                    reaction='Sneezing, runny nose, watery eyes',
                    severity='mild',
                    date_identified=date(2015, 3, 5),
                    notes='Seasonal allergy, managed with antihistamines when needed.',
                    source='self_entered'
                ),
            ]
            for a in allergies_data:
                db.session.add(a)

            # ---- CONDITIONS ----
            conditions_data = [
                Condition(
                    patient_id=patient.id,
                    condition_name='Vitamin D Deficiency',
                    diagnosis_date=date(2022, 8, 15),
                    status='resolved',
                    severity='mild',
                    treating_doctor='Dr. Ananya Sharma',
                    notes='Serum Vitamin D was 18 ng/mL. Resolved after 6-month supplementation. Follow-up test confirmed normal levels.',
                    source='provider',
                    source_organization='Sharma Clinic'
                ),
                Condition(
                    patient_id=patient.id,
                    condition_name='Pre-diabetes (Impaired Fasting Glucose)',
                    diagnosis_date=date(2024, 1, 5),
                    status='monitoring',
                    severity='mild',
                    treating_doctor='Dr. Ananya Sharma',
                    notes='Fasting glucose 108 mg/dL. HbA1c 6.0%. Diet and lifestyle modifications advised. Annual monitoring recommended.',
                    source='provider',
                    source_organization='Sharma Clinic'
                ),
            ]
            for c in conditions_data:
                db.session.add(c)

            # ---- MEDICATIONS ----
            medications_data = [
                Medication(
                    patient_id=patient.id,
                    medicine_name='Atorvastatin',
                    dosage='10mg',
                    frequency='Once daily at night',
                    start_date=date(2024, 6, 1),
                    prescribing_doctor='Dr. Ananya Sharma',
                    status='active',
                    notes='Prescribed for mildly elevated LDL cholesterol. Annual lipid profile review advised.',
                    source='provider',
                    source_organization='Sharma Clinic'
                ),
                Medication(
                    patient_id=patient.id,
                    medicine_name='Vitamin D3',
                    dosage='60,000 IU',
                    frequency='Once weekly for 8 weeks, then monthly',
                    start_date=date(2022, 8, 16),
                    end_date=date(2023, 2, 16),
                    prescribing_doctor='Dr. Ananya Sharma',
                    status='completed',
                    notes='Course completed. Vitamin D levels normalized.',
                    source='provider',
                    source_organization='Sharma Clinic'
                ),
                Medication(
                    patient_id=patient.id,
                    medicine_name='Metformin',
                    dosage='500mg',
                    frequency='Twice daily with meals',
                    start_date=date(2025, 1, 10),
                    prescribing_doctor='Dr. Ananya Sharma',
                    status='active',
                    notes='Started due to HbA1c reaching 6.2%. Review in 3 months.',
                    source='provider',
                    source_organization='Sharma Clinic'
                ),
            ]
            for m in medications_data:
                db.session.add(m)

            # ---- IMMUNIZATIONS ----
            immunizations_data = [
                Immunization(
                    patient_id=patient.id,
                    vaccine_name='COVID-19 (Covishield)',
                    dose_number='Dose 1',
                    vaccination_date=date(2021, 4, 15),
                    provider='Government Vaccination Centre, Delhi',
                    source='self_entered'
                ),
                Immunization(
                    patient_id=patient.id,
                    vaccine_name='COVID-19 (Covishield)',
                    dose_number='Dose 2',
                    vaccination_date=date(2021, 7, 20),
                    provider='Government Vaccination Centre, Delhi',
                    source='self_entered'
                ),
                Immunization(
                    patient_id=patient.id,
                    vaccine_name='COVID-19 (Precaution Dose)',
                    dose_number='Booster',
                    vaccination_date=date(2022, 2, 10),
                    provider='Apollo Pharmacy, Delhi',
                    source='self_entered'
                ),
                Immunization(
                    patient_id=patient.id,
                    vaccine_name='Hepatitis B',
                    dose_number='Series Complete',
                    vaccination_date=date(2019, 9, 1),
                    provider='Sharma Clinic',
                    source='provider',
                    source_organization='Sharma Clinic'
                ),
                Immunization(
                    patient_id=patient.id,
                    vaccine_name='Tetanus Toxoid (Td)',
                    dose_number='Booster',
                    vaccination_date=date(2018, 3, 22),
                    provider='Example General Hospital',
                    source='provider',
                    source_organization='Example General Hospital'
                ),
            ]
            for i in immunizations_data:
                db.session.add(i)

            # ---- PROCEDURES ----
            procedure = Procedure(
                patient_id=patient.id,
                procedure_name='Laparoscopic Appendectomy',
                procedure_date=date(2020, 11, 8),
                hospital='Example General Hospital',
                surgeon='Dr. Rajesh Mehta (Surgeon)',
                indication='Acute appendicitis — pain and tenderness in right iliac fossa, confirmed by ultrasound.',
                outcome='Procedure successful. Discharged on day 3. No complications. Full recovery within 3 weeks.',
                notes='Laparoscopic approach. 3 small incisions. No drain placed.',
                source='patient_uploaded',
                source_organization='Example General Hospital'
            )
            db.session.add(procedure)

            # ---- IMAGING ----
            imaging = ImagingStudy(
                patient_id=patient.id,
                imaging_type='X-Ray',
                body_region='Chest (PA View)',
                study_date=date(2020, 11, 7),
                facility='Example General Hospital',
                findings='Lungs are clear. Heart size normal. No active cardiopulmonary disease. Pre-operative clearance given.',
                source='patient_uploaded',
                source_organization='Example General Hospital'
            )
            db.session.add(imaging)

            # ---- FAMILY HISTORY ----
            family_history_data = [
                FamilyHistory(
                    patient_id=patient.id,
                    relative='Father',
                    condition='Type 2 Diabetes',
                    age_at_onset='52 years',
                    notes='Managed with oral hypoglycemics.'
                ),
                FamilyHistory(
                    patient_id=patient.id,
                    relative='Paternal Grandfather',
                    condition='Hypertension, Coronary Artery Disease',
                    age_at_onset='60s',
                    notes='Expired due to myocardial infarction at age 72.'
                ),
            ]
            for f in family_history_data:
                db.session.add(f)

            db.session.commit()

            # ---- HOSPITALIZATION (ENCOUNTER) ----
            doctor_user_reload = User.query.filter_by(email='doctor@demo.healthvault').first()
            doctor_provider_reload = doctor_user_reload.provider if doctor_user_reload else None

            hosp_encounter = Encounter(
                patient_id=patient.id,
                provider_id=doctor_provider_reload.id if doctor_provider_reload else None,
                encounter_type='hospitalization',
                encounter_date=date(2020, 11, 6),
                facility='Example General Hospital',
                doctor_name='Dr. Rajesh Mehta',
                specialty='General Surgery',
                reason='Acute Appendicitis — severe right-sided abdominal pain',
                diagnosis='Acute appendicitis',
                clinical_notes='Patient presented with 24-hour history of progressive right iliac fossa pain, nausea, and low-grade fever (37.8°C). Rebound tenderness present. WBC elevated at 14,200. Ultrasound confirmed appendiceal inflammation.',
                admission_date=date(2020, 11, 6),
                discharge_date=date(2020, 11, 9),
                discharge_summary='Laparoscopic appendectomy performed on 08/11/2020 without complications. Patient tolerating oral diet. Pain well controlled. Wound healing satisfactorily. Follow-up in 2 weeks.',
                source='patient_uploaded',
                source_organization='Example General Hospital'
            )
            db.session.add(hosp_encounter)

            # ---- RECENT CONSULTATION ----
            consultation = Encounter(
                patient_id=patient.id,
                provider_id=doctor_provider_reload.id if doctor_provider_reload else None,
                encounter_type='consultation',
                encounter_date=date(2026, 9, 10),
                facility='Sharma Clinic',
                doctor_name='Dr. Ananya Sharma',
                specialty='General Physician',
                reason='Annual health check and review of pre-diabetic state',
                diagnosis='Pre-diabetes (stable, monitoring). Dyslipidemia (controlled on Atorvastatin).',
                clinical_notes='Patient is compliant with medications. Reports no symptoms. BP: 118/76. Weight: 72kg. BMI: 23.4. Fasting glucose: 102 mg/dL (improved from 108). LDL: 112 mg/dL (improved from 148). Continue current management. Lifestyle advice reiterated.',
                prescription='Atorvastatin 10mg — continue. Metformin 500mg BD — continue. Advised regular exercise (30 min/day) and low-glycemic diet.',
                follow_up_date=date(2027, 3, 10),
                source='provider',
                source_organization='Sharma Clinic'
            )
            db.session.add(consultation)

            db.session.commit()

            # ---- LAB REPORTS ----
            # CBC — September 2026
            cbc = DiagnosticReport(
                patient_id=patient.id,
                report_name='Complete Blood Count (CBC)',
                report_date=date(2026, 9, 12),
                laboratory='City Diagnostics',
                ordering_doctor='Dr. Ananya Sharma',
                status='final',
                summary='All values within normal limits. No significant abnormality detected.',
                source='lab',
                source_organization='City Diagnostics'
            )
            db.session.add(cbc)
            db.session.flush()

            cbc_obs = [
                Observation(report_id=cbc.id, test_name='Hemoglobin', value='13.8', unit='g/dL', reference_range='13.0 - 17.0', is_abnormal=False, interpretation='normal'),
                Observation(report_id=cbc.id, test_name='WBC (Total Leukocyte Count)', value='7200', unit='/µL', reference_range='4000 - 11000', is_abnormal=False, interpretation='normal'),
                Observation(report_id=cbc.id, test_name='Platelets', value='250000', unit='/µL', reference_range='150000 - 400000', is_abnormal=False, interpretation='normal'),
                Observation(report_id=cbc.id, test_name='RBC', value='4.8', unit='million/µL', reference_range='4.5 - 5.5', is_abnormal=False, interpretation='normal'),
                Observation(report_id=cbc.id, test_name='PCV / Hematocrit', value='42', unit='%', reference_range='40 - 50', is_abnormal=False, interpretation='normal'),
                Observation(report_id=cbc.id, test_name='MCV', value='88', unit='fL', reference_range='80 - 100', is_abnormal=False, interpretation='normal'),
                Observation(report_id=cbc.id, test_name='Neutrophils', value='62', unit='%', reference_range='40 - 80', is_abnormal=False, interpretation='normal'),
                Observation(report_id=cbc.id, test_name='Lymphocytes', value='30', unit='%', reference_range='20 - 40', is_abnormal=False, interpretation='normal'),
            ]
            for obs in cbc_obs:
                db.session.add(obs)

            # Lipid Profile — June 2026
            lipid = DiagnosticReport(
                patient_id=patient.id,
                report_name='Lipid Profile',
                report_date=date(2026, 6, 4),
                laboratory='City Diagnostics',
                ordering_doctor='Dr. Ananya Sharma',
                status='final',
                summary='LDL cholesterol mildly elevated. On Atorvastatin — showing improvement from previous test.',
                source='lab',
                source_organization='City Diagnostics'
            )
            db.session.add(lipid)
            db.session.flush()

            lipid_obs = [
                Observation(report_id=lipid.id, test_name='Total Cholesterol', value='188', unit='mg/dL', reference_range='< 200', is_abnormal=False, interpretation='normal'),
                Observation(report_id=lipid.id, test_name='LDL Cholesterol', value='112', unit='mg/dL', reference_range='< 100', is_abnormal=True, interpretation='high'),
                Observation(report_id=lipid.id, test_name='HDL Cholesterol', value='48', unit='mg/dL', reference_range='> 40', is_abnormal=False, interpretation='normal'),
                Observation(report_id=lipid.id, test_name='Triglycerides', value='140', unit='mg/dL', reference_range='< 150', is_abnormal=False, interpretation='normal'),
                Observation(report_id=lipid.id, test_name='VLDL', value='28', unit='mg/dL', reference_range='< 30', is_abnormal=False, interpretation='normal'),
            ]
            for obs in lipid_obs:
                db.session.add(obs)

            # Blood Glucose — March 2026
            glucose = DiagnosticReport(
                patient_id=patient.id,
                report_name='Blood Glucose (Fasting & PP)',
                report_date=date(2026, 3, 14),
                laboratory='City Diagnostics',
                ordering_doctor='Dr. Ananya Sharma',
                status='final',
                summary='Fasting glucose improved. Continuing monitoring for pre-diabetic state.',
                source='lab',
                source_organization='City Diagnostics'
            )
            db.session.add(glucose)
            db.session.flush()

            glucose_obs = [
                Observation(report_id=glucose.id, test_name='Fasting Blood Glucose', value='102', unit='mg/dL', reference_range='70 - 100', is_abnormal=True, interpretation='high'),
                Observation(report_id=glucose.id, test_name='Post-Prandial Blood Glucose (2hr)', value='138', unit='mg/dL', reference_range='< 140', is_abnormal=False, interpretation='normal'),
            ]
            for obs in glucose_obs:
                db.session.add(obs)

            # HbA1c — January 2026
            hba1c = DiagnosticReport(
                patient_id=patient.id,
                report_name='HbA1c (Glycated Hemoglobin)',
                report_date=date(2026, 1, 5),
                laboratory='City Diagnostics',
                ordering_doctor='Dr. Ananya Sharma',
                status='final',
                summary='HbA1c at 6.2% — pre-diabetic range. Lifestyle changes and medication review done.',
                source='lab',
                source_organization='City Diagnostics'
            )
            db.session.add(hba1c)
            db.session.flush()

            hba1c_obs = [
                Observation(report_id=hba1c.id, test_name='HbA1c', value='6.2', unit='%', reference_range='< 5.7 (Normal), 5.7-6.4 (Pre-diabetic)', is_abnormal=True, interpretation='high'),
                Observation(report_id=hba1c.id, test_name='Estimated Average Glucose (eAG)', value='131', unit='mg/dL', reference_range='< 117', is_abnormal=True, interpretation='high'),
            ]
            for obs in hba1c_obs:
                db.session.add(obs)

            # Vitamin D — August 2022
            vitd = DiagnosticReport(
                patient_id=patient.id,
                report_name='25-OH Vitamin D (Serum)',
                report_date=date(2022, 8, 15),
                laboratory='City Diagnostics',
                ordering_doctor='Dr. Ananya Sharma',
                status='final',
                summary='Vitamin D deficiency confirmed. Supplementation started.',
                source='lab',
                source_organization='City Diagnostics'
            )
            db.session.add(vitd)
            db.session.flush()

            vitd_obs = [
                Observation(report_id=vitd.id, test_name='Serum 25-OH Vitamin D', value='18', unit='ng/mL', reference_range='30 - 100', is_abnormal=True, interpretation='low'),
            ]
            for obs in vitd_obs:
                db.session.add(obs)

            db.session.commit()

            # ---- NOTIFICATIONS ----
            notifs = [
                Notification(
                    patient_id=patient.id,
                    title='New CBC Report Available',
                    message='City Diagnostics has uploaded your Complete Blood Count (CBC) report dated 12 Sep 2026.',
                    notification_type='new_report',
                    is_read=False
                ),
                Notification(
                    patient_id=patient.id,
                    title='Consultation Record Added',
                    message='Dr. Ananya Sharma added a consultation record for your annual health check on 10 Sep 2026.',
                    notification_type='new_consultation',
                    is_read=True
                ),
                Notification(
                    patient_id=patient.id,
                    title='Lipid Profile Available',
                    message='City Diagnostics has uploaded your Lipid Profile report dated 4 Jun 2026.',
                    notification_type='new_report',
                    is_read=True
                ),
            ]
            for n in notifs:
                db.session.add(n)

            db.session.commit()

            # Generate QR code
            utils.generate_qr_code('HV-IND-8F42-K92P', patient.id)
            print("   ✅ Allergies, Conditions, Medications")
            print("   ✅ Lab Reports (CBC, Lipid Profile, Blood Glucose, HbA1c, Vitamin D)")
            print("   ✅ Vaccinations (COVID-19, Hepatitis B, Tetanus)")
            print("   ✅ Procedures (Appendectomy)")
            print("   ✅ Encounters (Hospitalization, Consultation)")
            print("   ✅ Imaging (Chest X-Ray)")
            print("   ✅ Family History")
            print("   ✅ Notifications")
            print("   ✅ QR Code generated")
        else:
            print("\n   ℹ️  Demo data already exists. Skipping.")

        print("\n" + "=" * 60)
        print("✅ Database seeding complete!")
        print("=" * 60)
        print("\n📋 Demo Accounts:")
        print("   Patient : patient@demo.healthvault  / DemoPassword123!")
        print("   Doctor  : doctor@demo.healthvault   / DemoPassword123!")
        print("   Lab     : lab@demo.healthvault      / DemoPassword123!")
        print("   Admin   : admin@demo.healthvault    / DemoPassword123!")
        print("\n🆔 Patient HealthVault ID: HV-IND-8F42-K92P")
        print("\n🌐 Run the app: python app.py")
        print("   Then open: http://localhost:5000\n")


if __name__ == '__main__':
    seed_database()
