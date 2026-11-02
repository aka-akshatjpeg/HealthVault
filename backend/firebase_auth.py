"""Firebase ID-token verification and safe HealthVault account mapping."""
import hashlib
import secrets
from flask import current_app
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash
from models import db, User, Patient, HealthIdentity, EmergencyProfile
import utils


class FirebaseAuthUnavailable(Exception): pass
class FirebaseTokenInvalid(Exception): pass
class FirebaseAccountConflict(Exception): pass
class FirebaseAccountInactive(Exception): pass
class FirebaseLinkRejected(Exception): pass


class FirebaseProfileRequired(Exception):
    def __init__(self, fields):
        self.fields = fields


def verify_firebase_token(id_token):
    project_id = current_app.config.get('FIREBASE_PROJECT_ID', '').strip()
    if not project_id:
        raise FirebaseAuthUnavailable('FIREBASE_PROJECT_ID is missing.')
    try:
        import firebase_admin
        from firebase_admin import auth as firebase_auth
        from firebase_admin import credentials
    except ImportError as exc:
        raise FirebaseAuthUnavailable('Install firebase-admin on the backend.') from exc
    app_name = 'healthvault-auth'
    try:
        admin_app = firebase_admin.get_app(app_name)
    except ValueError:
        try:
            admin_app = firebase_admin.initialize_app(
                credentials.ApplicationDefault(),
                options={'projectId': project_id},
                name=app_name,
            )
        except Exception as exc:
            raise FirebaseAuthUnavailable('Firebase Admin credentials are unavailable.') from exc
    if getattr(admin_app, 'project_id', None) not in (None, project_id):
        raise FirebaseAuthUnavailable('Firebase Admin is initialized for another project.')
    try:
        claims = firebase_auth.verify_id_token(id_token, app=admin_app, check_revoked=True)
    except Exception as exc:
        if type(exc).__name__ in {'InvalidIdTokenError', 'ExpiredIdTokenError', 'RevokedIdTokenError'}:
            raise FirebaseTokenInvalid() from exc
        raise FirebaseAuthUnavailable('Firebase token verification failed.') from exc
    if claims.get('aud') != project_id or not claims.get('uid'):
        raise FirebaseTokenInvalid()
    return claims


def _verified_email(claims):
    verified = claims.get('email_verified')
    if verified is True or (isinstance(verified, str) and verified.lower() == 'true'):
        value = claims.get('email')
        return value.strip().lower() if isinstance(value, str) else ''
    return ''


def _find_user_by_email(email):
    if not email:
        return None
    return User.query.filter(db.func.lower(User.email) == email.lower()).first()


def link_firebase_phone_account(claims, email, password):
    """Link a verified Firebase phone identity after proving the existing password."""
    uid = claims.get('uid')
    phone = claims.get('phone_number')
    if not isinstance(uid, str) or not uid or not isinstance(phone, str) or not phone.strip():
        raise FirebaseTokenInvalid()
    firebase_claim = claims.get('firebase')
    if not isinstance(firebase_claim, dict) or firebase_claim.get('sign_in_provider') != 'phone':
        raise FirebaseTokenInvalid()
    if not isinstance(email, str) or not isinstance(password, str):
        raise FirebaseLinkRejected()

    user = _find_user_by_email(email.strip().lower())
    if not user or not check_password_hash(user.password_hash, password):
        # Keep the response the same for unknown emails and incorrect passwords.
        raise FirebaseLinkRejected()
    if not user.is_active:
        raise FirebaseAccountInactive()

    uid_owner = User.query.filter_by(firebase_uid=uid).first()
    if uid_owner and uid_owner.id != user.id:
        raise FirebaseAccountConflict('This Firebase identity is already linked to another HealthVault account.')
    if user.firebase_uid and user.firebase_uid != uid:
        raise FirebaseAccountConflict('This HealthVault account is already linked to another sign-in identity.')

    user.firebase_uid = uid
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise FirebaseAccountConflict('This Firebase identity is already linked to another HealthVault account.') from exc
    return user


def authenticate_firebase_user(claims, profile=None):
    profile = profile if isinstance(profile, dict) else {}
    uid = claims.get('uid')
    if not isinstance(uid, str) or not uid:
        raise FirebaseTokenInvalid()

    verified_email = _verified_email(claims)
    if verified_email and (len(verified_email) > 120 or '@' not in verified_email):
        raise FirebaseTokenInvalid()
    phone = claims.get('phone_number')
    if not isinstance(phone, str) or not phone.strip():
        phone = None
    else:
        phone = phone.strip()

    user = User.query.filter_by(firebase_uid=uid).first()
    if user:
        if not user.is_active:
            raise FirebaseAccountInactive()
        if verified_email and user.email.endswith('@healthvault.invalid'):
            other_user = _find_user_by_email(verified_email)
            if other_user and other_user.id != user.id:
                raise FirebaseAccountConflict('That verified email is already attached to another HealthVault account.')
            user.email = verified_email
            try:
                db.session.commit()
            except IntegrityError as exc:
                db.session.rollback()
                raise FirebaseAccountConflict('That verified email is already attached to another HealthVault account.') from exc
        return user

    if verified_email:
        user = _find_user_by_email(verified_email)
        if user:
            if not user.is_active:
                raise FirebaseAccountInactive()
            if user.firebase_uid and user.firebase_uid != uid:
                raise FirebaseAccountConflict('This HealthVault account is linked to another sign-in identity.')
            user.firebase_uid = uid
            try:
                db.session.commit()
            except IntegrityError as exc:
                db.session.rollback()
                raise FirebaseAccountConflict('This Firebase identity is already linked to another account.') from exc
            return user
    elif not phone:
        raise FirebaseAccountConflict('Firebase must provide a verified email address or verified phone number.')

    claim_name = claims.get('name')
    supplied_name = profile.get('full_name')
    full_name = claim_name.strip() if isinstance(claim_name, str) else ''
    if not full_name and isinstance(supplied_name, str):
        full_name = supplied_name.strip()
    if not full_name or len(full_name) > 200:
        raise FirebaseProfileRequired(['full_name'])

    # Phone-only accounts have no verified email. Use a deterministic, non-routable
    # address so a client-supplied email cannot reserve or impersonate another user.
    email = verified_email or f'phone-{hashlib.sha256(uid.encode("utf-8")).hexdigest()}@healthvault.invalid'
    user = User(
        email=email,
        password_hash=generate_password_hash(secrets.token_urlsafe(48)),
        role='patient',
        firebase_uid=uid,
    )
    try:
        db.session.add(user)
        db.session.flush()
        patient = Patient(user_id=user.id, full_name=full_name, phone=phone)
        db.session.add(patient)
        db.session.flush()
        hv_id = utils.generate_hv_id()
        db.session.add(HealthIdentity(patient_id=patient.id, hv_id=hv_id))
        db.session.add(EmergencyProfile(patient_id=patient.id))
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raced = User.query.filter_by(firebase_uid=uid).first()
        if raced and raced.is_active:
            return raced
        raise FirebaseAccountConflict('An account already uses this email or Firebase identity.') from exc
    return user


def record_firebase_login(user, source, ip_address=''):
    user.last_login = utils.utcnow()
    db.session.commit()
    if user.role == 'patient' and user.patient:
        utils.log_audit_event(
            patient_id=user.patient.id,
            actor_id=user.id,
            actor_name=user.patient.full_name,
            action='login',
            resource_type='account',
            resource_description=f'{source.capitalize()} login via Firebase',
            status='success',
            ip_address=ip_address,
        )
