import json
import os
import sys
import uuid
import unittest
from datetime import date
from unittest.mock import patch

BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BACKEND_DIR)
os.environ['DATABASE_URL'] = 'sqlite://'
os.environ['SECRET_KEY'] = 'test-only-secret-key-that-is-long-enough'
os.environ['JWT_SECRET_KEY'] = 'test-only-jwt-secret-key-that-is-long-enough'
os.environ['DEMO_MODE'] = 'false'

from app import create_app, _add_missing_profile_columns
from models import db, User, Patient, HealthIdentity, EmergencyProfile, Document, DiagnosticReport, Encounter, Organization
from sqlalchemy import text
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token
import utils
from firebase_auth import FirebaseTokenInvalid


class ApiV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True

    def setUp(self):
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            self.owner_id = None
            self.other_id = None
        self.client = self.app.test_client()

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.session.remove()
            db.engine.dispose()

    # ─── Test helpers ──────────────────────────────────────────────────────────

    def _create_user(self, role='patient', email='person@example.test'):
        """
        Create a User (+ Patient profile when role=='patient') directly in the
        DB and return a dict with tokens and user metadata.

        Bypasses the closed POST /api/v1/auth/register and web POST /register so
        that test setup never depends on a registration route.
        """
        with self.app.app_context():
            user = User(
                email=email,
                password_hash=generate_password_hash('test-pw-long-enough'),
                role=role,
            )
            db.session.add(user)
            db.session.flush()

            hv_id = None
            if role == 'patient':
                patient = Patient(user_id=user.id, full_name='Test Person')
                db.session.add(patient)
                db.session.flush()
                hv_id = utils.generate_hv_id()
                db.session.add(HealthIdentity(patient_id=patient.id, hv_id=hv_id))
                db.session.add(EmergencyProfile(patient_id=patient.id))

            db.session.commit()
            user_id = user.id

        with self.app.test_request_context():
            identity = json.dumps({'user_id': str(user_id), 'role': role})
            access  = create_access_token(identity=identity)
            refresh = create_refresh_token(identity=identity)

        return {
            'access_token': access,
            'refresh_token': refresh,
            'role': role,
            'user': {'id': user_id, 'email': email, 'role': role, 'hv_id': hv_id},
        }

    # =========================================================================
    # Web registration — closed
    # =========================================================================

    def test_web_register_post_is_closed_for_every_role(self):
        """POST /register must return 410 for patient, doctor, lab, admin."""
        for role in ('patient', 'doctor', 'lab', 'admin'):
            with self.subTest(role=role):
                r = self.client.post('/register', data={
                    'role': role,
                    'email': f'{role}@attacker.test',
                    'password': 'long-enough-password',
                    'confirm_password': 'long-enough-password',
                    'full_name': 'Attacker',
                })
                self.assertEqual(r.status_code, 410, f'Expected 410 for role={role!r}')
        with self.app.app_context():
            self.assertEqual(User.query.count(), 0, 'No users should have been created')

    def test_web_register_get_redirects_to_login(self):
        """GET /register is closed — must redirect (302) to /login."""
        r = self.client.get('/register', follow_redirects=False)
        self.assertEqual(r.status_code, 302)
        self.assertIn('/login', r.headers.get('Location', ''))

    def test_web_register_cannot_mint_session_or_create_privileged_account(self):
        """POST /register with doctor/lab role must not create any user."""
        for role in ('doctor', 'lab'):
            with self.subTest(role=role):
                r = self.client.post('/register', data={
                    'role': role,
                    'email': f'{role}@attacker.test',
                    'password': 'long-enough-password',
                    'confirm_password': 'long-enough-password',
                    'full_name': 'Attacker',
                    'organization': 'Fake Clinic',
                    'specialty': 'Cardiology',
                })
                self.assertEqual(r.status_code, 410)
        with self.app.app_context():
            self.assertEqual(User.query.count(), 0)

    # =========================================================================
    # API /register — closed
    # =========================================================================

    def test_unauthenticated_api_register_cannot_create_account_or_mint_tokens(self):
        """POST /api/v1/auth/register must return 410 for every role — no tokens."""
        for role in ('patient', 'doctor', 'lab', 'admin', 'unknown'):
            with self.subTest(role=role):
                r = self.client.post('/api/v1/auth/register', json={
                    'role': role,
                    'email': f'{role}@attacker.test',
                    'password': 'long-enough-password',
                    'confirm_password': 'long-enough-password',
                    'full_name': 'Attacker',
                })
                self.assertEqual(r.status_code, 410)
                body = r.get_json()
                self.assertNotIn('access_token', body)
                self.assertNotIn('refresh_token', body)
        with self.app.app_context():
            self.assertEqual(User.query.count(), 0)

    def test_registration_rejects_privileged_or_unknown_roles(self):
        """The closed /register endpoint returns 410 regardless of role."""
        for role in ('admin', 'unknown', []):
            with self.subTest(role=role):
                email = f'{role}@example.test' if isinstance(role, str) else 'list-role@example.test'
                r = self.client.post('/api/v1/auth/register', json={
                    'role': role, 'email': email,
                    'password': 'long-enough-password',
                    'confirm_password': 'long-enough-password',
                    'full_name': 'Attacker',
                })
                self.assertEqual(r.status_code, 410)
        with self.app.app_context():
            self.assertEqual(User.query.count(), 0)

    # =========================================================================
    # Web login — retired email/password path
    # =========================================================================

    def test_web_login_post_is_rejected(self):
        """POST /login with email+password must not log in — form is retired."""
        self._create_user(email='existing@example.test')
        r = self.client.post('/login', data={
            'email': 'existing@example.test',
            'password': 'test-pw-long-enough',
        }, follow_redirects=False)
        # Must NOT redirect to a dashboard — must stay on /login (200 with warning)
        # OR redirect back to /login.  Either way, no session user set.
        location = r.headers.get('Location', '')
        self.assertNotIn('dashboard', location)
        with self.client.session_transaction() as sess:
            self.assertNotIn('_user_id', sess)

    def test_web_login_get_renders_firebase_page(self):
        """GET /login must return 200 (renders Firebase sign-in)."""
        r = self.client.get('/login')
        self.assertEqual(r.status_code, 200)

    # =========================================================================
    # Retired web OTP routes
    # =========================================================================

    def test_verify_otp_get_redirects_to_login(self):
        """GET /verify-otp must redirect to /login — route is retired."""
        r = self.client.get('/verify-otp', follow_redirects=False)
        self.assertEqual(r.status_code, 302)
        self.assertIn('/login', r.headers.get('Location', ''))

    def test_verify_otp_post_redirects_to_login(self):
        """POST /verify-otp must redirect to /login — route is retired."""
        r = self.client.post('/verify-otp', data={'otp': '123456'}, follow_redirects=False)
        self.assertEqual(r.status_code, 302)
        self.assertIn('/login', r.headers.get('Location', ''))

    def test_resend_otp_redirects_to_login(self):
        """GET /resend-otp must redirect to /login — route is retired."""
        r = self.client.get('/resend-otp', follow_redirects=False)
        self.assertEqual(r.status_code, 302)
        self.assertIn('/login', r.headers.get('Location', ''))

    def test_login_endpoint_is_removed(self):
        """The demo API email/password login endpoint must be 410 Gone."""
        r = self.client.post('/api/v1/auth/login', json={
            'email': 'person@example.test',
            'password': 'long-enough-password',
        })
        self.assertEqual(r.status_code, 410)
        self.assertNotIn('otp_code', r.get_json())

    def test_api_otp_endpoints_cannot_accept_or_reveal_codes(self):
        """/api/v1/auth/verify-otp must be 410 — no tokens or codes returned."""
        r = self.client.post('/api/v1/auth/verify-otp', json={
            'user_id': 'any', 'otp': '123456',
        })
        self.assertEqual(r.status_code, 410)
        body = r.get_json()
        self.assertNotIn('access_token', body)
        self.assertNotIn('otp_code', body)
        self.assertNotIn('code', body)

    # =========================================================================
    # Aadhaar OTP endpoints — unconditionally unavailable
    # =========================================================================

    def test_aadhaar_send_otp_is_unavailable(self):
        """POST /api/aadhaar/send-otp must return 503 — no OTP generated."""
        r = self.client.post('/api/aadhaar/send-otp',
                             json={'aadhaar_number': '123456789012'},
                             content_type='application/json')
        self.assertEqual(r.status_code, 503)
        body = r.get_json()
        self.assertFalse(body.get('success', True))
        # Must never expose an OTP code in any response field
        self.assertNotIn('otp', body)
        self.assertNotIn('code', body)

    def test_aadhaar_verify_otp_is_unavailable(self):
        """POST /api/aadhaar/verify-otp must return 503."""
        r = self.client.post('/api/aadhaar/verify-otp',
                             json={'aadhaar_number': '123456789012', 'otp': '999999'},
                             content_type='application/json')
        self.assertEqual(r.status_code, 503)
        self.assertFalse(r.get_json().get('success', True))

    def test_aadhaar_verify_and_save_is_unavailable(self):
        """POST /api/aadhaar/verify-and-save must return 503."""
        r = self.client.post('/api/aadhaar/verify-and-save',
                             json={'aadhaar_number': '123456789012', 'otp': '999999'},
                             content_type='application/json')
        self.assertEqual(r.status_code, 503)
        self.assertFalse(r.get_json().get('success', True))

    def test_aadhaar_endpoints_return_503_regardless_of_demo_mode(self):
        """Even if DEMO_MODE were True the Aadhaar OTP routes must be 503."""
        original = self.app.config.get('DEMO_MODE')
        try:
            self.app.config['DEMO_MODE'] = True
            for path in ('/api/aadhaar/send-otp', '/api/aadhaar/verify-otp',
                         '/api/aadhaar/verify-and-save'):
                with self.subTest(path=path):
                    r = self.client.post(path,
                                         json={'aadhaar_number': '123456789012', 'otp': '123456'},
                                         content_type='application/json')
                    self.assertEqual(r.status_code, 503)
                    self.assertNotIn('otp', r.get_json())
        finally:
            if original is None:
                self.app.config.pop('DEMO_MODE', None)
            else:
                self.app.config['DEMO_MODE'] = original

    # =========================================================================
    # Firebase token validation
    # =========================================================================

    @patch('routes.api_v1.auth.verify_firebase_token', side_effect=FirebaseTokenInvalid)
    def test_invalid_firebase_token_is_rejected(self, _mock):
        """A garbage Firebase ID token must return 401 — no tokens issued."""
        r = self.client.post('/api/v1/auth/firebase-login', json={'id_token': 'garbage-token'})
        self.assertEqual(r.status_code, 401)
        self.assertNotIn('access_token', r.get_json())

    @patch('routes.api_v1.auth.verify_firebase_token')
    def test_firebase_phone_sign_in_creates_patient_and_mints_jwt(self, verify_token):
        """Valid phone sign-in ID token creates a patient account and returns a JWT."""
        verify_token.return_value = {
            'uid': 'phone-test-uid',
            'phone_number': '+919999999999',
        }
        r = self.client.post('/api/v1/auth/firebase-login', json={
            'id_token': 'mock-firebase-id-token',
            'full_name': 'New Patient',
        })
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertIn('access_token', body)
        self.assertEqual(body['role'], 'patient')
        with self.app.app_context():
            u = User.query.filter_by(firebase_uid='phone-test-uid').one()
            self.assertTrue(u.email.endswith('@healthvault.invalid'))
            self.assertIsNotNone(u.patient)

    @patch('routes.api_v1.auth.verify_firebase_token')
    def test_firebase_login_links_verified_email_to_existing_account(self, verify_token):
        existing = self._create_user(email='linked@example.test')
        verify_token.return_value = {
            'uid': 'firebase-user-123', 'email': 'linked@example.test',
            'email_verified': True, 'name': 'Test Person',
        }
        response = self.client.post('/api/v1/auth/firebase-login', json={
            'id_token': 'mock-firebase-id-token', 'role': 'admin',
        })
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload['user']['id'], existing['user']['id'])
        self.assertEqual(payload['user']['role'], 'patient')
        self.assertTrue(payload['access_token'])
        with self.app.app_context():
            user = db.session.get(User, existing['user']['id'])
            self.assertEqual(user.firebase_uid, 'firebase-user-123')

    @patch('routes.api_v1.auth.verify_firebase_token')
    def test_firebase_phone_login_requires_name_before_creating_patient(self, verify_token):
        verify_token.return_value = {'uid': 'phone-only-user', 'phone_number': '+919876543210'}
        response = self.client.post('/api/v1/auth/firebase-login', json={
            'id_token': 'mock-firebase-id-token',
        })
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.get_json()['error'], 'profile_required')
        with self.app.app_context():
            self.assertEqual(User.query.count(), 0)

    @patch('routes.api_v1.auth.verify_firebase_token')
    def test_phone_signup_ignores_unverified_email_from_client(self, verify_token):
        existing = self._create_user(email='owner@example.test')
        verify_token.return_value = {
            'uid': 'phone-only-user', 'phone_number': '+919876543210',
            'email': 'owner@example.test', 'email_verified': False,
        }
        response = self.client.post('/api/v1/auth/firebase-login', json={
            'id_token': 'mock-firebase-id-token',
            'full_name': 'Phone Patient',
            'email': 'owner@example.test',
        })
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            owner = db.session.get(User, existing['user']['id'])
            phone_user = User.query.filter_by(firebase_uid='phone-only-user').one()
            self.assertIsNone(owner.firebase_uid)
            self.assertNotEqual(phone_user.email, 'owner@example.test')
            self.assertEqual(response.get_json()['user']['email'], '')
            self.assertTrue(phone_user.email.endswith('@healthvault.invalid'))
            self.assertEqual(phone_user.patient.phone, '+919876543210')

    @patch('routes.api_v1.auth.verify_firebase_token')
    def test_firebase_account_without_verified_email_or_phone_is_rejected(self, verify_token):
        verify_token.return_value = {
            'uid': 'unverified-email-user', 'email': 'owner@example.test', 'email_verified': False,
        }
        response = self.client.post('/api/v1/auth/firebase-login', json={
            'id_token': 'mock-firebase-id-token', 'full_name': 'Unverified User',
            'email': 'owner@example.test',
        })
        self.assertEqual(response.status_code, 409)
        with self.app.app_context():
            self.assertEqual(User.query.count(), 0)

    # =========================================================================
    # Schema / infrastructure
    # =========================================================================

    def test_additive_schema_upgrade_preserves_existing_rows(self):
        with self.app.app_context():
            db.session.add(Organization(name='Existing clinic'))
            db.session.commit()
            db.session.execute(text('ALTER TABLE organizations DROP COLUMN pincode'))
            _add_missing_profile_columns()
            db.session.expire_all()
            organization = Organization.query.filter_by(name='Existing clinic').one()
            self.assertIsNone(organization.pincode)

    # =========================================================================
    # AI endpoints
    # =========================================================================

    def test_ai_clear_history_accepts_patient_json_jwt_identity(self):
        payload = self._create_user()
        response = self.client.post(
            '/api/v1/ai/clear-history',
            headers={'Authorization': f"Bearer {payload['access_token']}"},
        )
        self.assertEqual(response.status_code, 200)

    def test_ai_clear_history_rejects_non_patient(self):
        payload = self._create_user(role='doctor', email='doc@example.test')
        response = self.client.post(
            '/api/v1/ai/clear-history',
            headers={'Authorization': f"Bearer {payload['access_token']}"},
        )
        self.assertEqual(response.status_code, 403)

    # =========================================================================
    # File privacy
    # =========================================================================

    def test_patient_record_files_are_private_and_owner_accessible(self):
        owner = self._create_user(email='owner@example.test')
        other = self._create_user(email='other@example.test')
        filename = f'{uuid.uuid4().hex}.pdf'
        encounter_filename = f'{uuid.uuid4().hex}.pdf'
        upload_dir = self.app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)
        encounter_file_path = os.path.join(upload_dir, encounter_filename)
        with open(file_path, 'wb') as f:
            f.write(b'private medical record')
        with open(encounter_file_path, 'wb') as f:
            f.write(b'private encounter record')
        try:
            with self.app.app_context():
                patient = User.query.filter_by(email='owner@example.test').first().patient
                self.owner_id = patient.user_id
                self.other_id = User.query.filter_by(email='other@example.test').first().id
                report = DiagnosticReport(
                    patient_id=patient.id, report_name='Test report',
                    report_date=date.today(), document_path=filename,
                )
                db.session.add(Document(
                    patient_id=patient.id, title='Test record',
                    file_path=filename, file_name=filename,
                ))
                db.session.add(report)
                db.session.add(Encounter(
                    patient_id=patient.id, encounter_date=date.today(),
                    document_path=encounter_filename,
                ))
                db.session.commit()
                report_id = report.id

            self.assertEqual(self.client.get(f'/uploads/{filename}').status_code, 404)
            self.assertEqual(self.client.get(f'/uploads/{encounter_filename}').status_code, 404)

            # Token alone does not authenticate web file routes (session cookie needed)
            self.assertEqual(
                self.client.get(f'/patient/records/file/{filename}',
                                headers={'Authorization': f"Bearer {owner['access_token']}"}).status_code,
                302,
            )
            with self.client.session_transaction() as sess:
                sess['_user_id'] = self.owner_id
                sess['_fresh'] = True
            resp = self.client.get(f'/patient/records/file/{filename}')
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.data, b'private medical record')
            resp.close()

            enc_resp = self.client.get(f'/patient/records/file/{encounter_filename}')
            self.assertEqual(enc_resp.status_code, 200)
            self.assertEqual(enc_resp.data, b'private encounter record')
            enc_resp.close()

            api_dl = self.client.get(
                f'/api/v1/patient/records/lab/{report_id}/download',
                headers={'Authorization': f"Bearer {owner['access_token']}"},
            )
            self.assertEqual(api_dl.status_code, 200)
            self.assertEqual(api_dl.data, b'private medical record')
            api_dl.close()

            other_dl = self.client.get(
                f'/api/v1/patient/records/lab/{report_id}/download',
                headers={'Authorization': f"Bearer {other['access_token']}"},
            )
            self.assertEqual(other_dl.status_code, 404)

            with self.client.session_transaction() as sess:
                sess['_user_id'] = self.other_id
                sess['_fresh'] = True
            self.assertEqual(self.client.get(f'/patient/records/file/{filename}').status_code, 404)
            self.assertEqual(self.client.get(f'/patient/records/file/{encounter_filename}').status_code, 404)
        finally:
            for p in (file_path, encounter_file_path):
                if os.path.exists(p):
                    os.remove(p)


if __name__ == '__main__':
    unittest.main()
