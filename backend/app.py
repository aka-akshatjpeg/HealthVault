# =============================================================================
# app.py — Main Flask Application
# =============================================================================
#
# WHAT IS THIS FILE?
# This is the entry point of the entire application.
# When you run "python app.py", Python reads this file and starts the web server.
#
# Think of this as the "main switch" that:
# 1. Creates the Flask app
# 2. Connects it to the database
# 3. Sets up login/logout handling
# 4. Registers all the URL routes (which URL shows which page)
# 5. Starts the web server
# =============================================================================

from flask import Flask, redirect, url_for
from flask_login import LoginManager
from dotenv import load_dotenv
from sqlalchemy import inspect, text
from models import db, User
from utils import utcnow
import os
import secrets

# Load this backend's settings regardless of the directory used to launch it.
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))


def create_app():
    """
    This function creates and configures the Flask application.
    We put it in a function so it's easy to test and import.
    """

    # Create the Flask app
    # __name__ tells Flask where to look for templates and static files
    app = Flask(__name__)

    # ==========================================================================
    # CONFIGURATION
    # These settings control how Flask behaves
    # ==========================================================================
    # A random fallback keeps first-run local use safe; deployments should set a
    # persistent SECRET_KEY so sessions survive restarts.
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or secrets.token_hex(32)
    # This is where the SQLite database file will be saved
    # Keep SQLite as the zero-configuration default, while allowing tests and
    # deployments to point at an explicit database without editing source code.
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///healthvault.db')
    # Turn off a feature we don't need (saves memory)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # Where uploaded files are stored
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
    app.config['PUBLIC_BASE_URL'] = os.getenv('PUBLIC_BASE_URL', 'http://localhost:5000').rstrip('/')
    # Maximum file size: 16 megabytes
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    # JWT configuration for mobile API
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.config['SECRET_KEY'])
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600       # 1 hour
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 2592000   # 30 days
    app.config['DEMO_MODE'] = os.getenv('DEMO_MODE', '').strip().lower() in {'1', 'true', 'yes'}
    app.config['FIREBASE_PROJECT_ID'] = os.getenv('FIREBASE_PROJECT_ID', '').strip()
    app.config['FIREBASE_WEB_CONFIG'] = {
        'apiKey': os.getenv('FIREBASE_WEB_API_KEY', '').strip(),
        'authDomain': os.getenv('FIREBASE_WEB_AUTH_DOMAIN', '').strip(),
        'projectId': os.getenv('FIREBASE_PROJECT_ID', '').strip(),
        'appId': os.getenv('FIREBASE_WEB_APP_ID', '').strip(),
    }

    # Make sure uploads folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # ==========================================================================
    # DATABASE SETUP
    # Connect Flask to the database
    # ==========================================================================
    db.init_app(app)

    # JWT — stateless token auth for the mobile API
    from flask_jwt_extended import JWTManager
    jwt = JWTManager(app)
    # CORS — allow mobile app requests to /api/v1/* from any origin
    from flask_cors import CORS
    CORS(app, resources={r'/api/v1/*': {'origins': '*'}}, supports_credentials=False)

    # ==========================================================================
    # LOGIN MANAGER SETUP
    # Flask-Login handles "who is currently logged in"
    # ==========================================================================
    login_manager = LoginManager()
    login_manager.init_app(app)
    # If a user tries to visit a protected page without being logged in,
    # redirect them to the login page
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access HealthVault.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        """
        Flask-Login calls this function on every request to load the current user.
        It takes the user_id from the session cookie and returns the User object.
        """
        return db.session.get(User, user_id)

    # ==========================================================================
    # REGISTER ROUTES (BLUEPRINTS)
    # Each routes/*.py file is a "Blueprint" — a group of related URLs
    # We import them here and attach them to the app
    # ==========================================================================
    @app.context_processor
    def inject_firebase_web_settings():
        return {'firebase_web_config': app.config['FIREBASE_WEB_CONFIG']}

    from routes.auth import auth_bp
    from routes.patient import patient_bp
    from routes.doctor import doctor_bp
    from routes.lab import lab_bp
    from routes.consent import consent_bp
    from routes.documents import documents_bp
    from routes.api import api_bp
    from routes.ai import ai_bp
    from routes.admin import admin_bp
    from routes.aadhaar import aadhaar_bp

    app.register_blueprint(auth_bp)           # /login, /register, /logout
    app.register_blueprint(patient_bp)        # /dashboard, /timeline, /records, etc.
    app.register_blueprint(doctor_bp)         # /doctor/dashboard, /doctor/patients, etc.
    app.register_blueprint(lab_bp)            # /lab/dashboard, /lab/report, etc.
    app.register_blueprint(consent_bp)        # /consent/requests, /consent/approve, etc.
    app.register_blueprint(documents_bp)      # /documents/upload, /documents/view, etc.
    app.register_blueprint(api_bp)            # /api/... (JSON data for charts)
    app.register_blueprint(ai_bp)             # /ai/...
    app.register_blueprint(admin_bp)          # /admin/...
    app.register_blueprint(aadhaar_bp)        # /api/aadhaar/...

    # ── Mobile JSON API (v1) ──────────────────────────────────────────────────
    from routes.api_v1.auth import auth_v1_bp
    from routes.api_v1.patient import patient_v1_bp
    from routes.api_v1.consent import consent_v1_bp
    from routes.api_v1.documents import docs_v1_bp
    from routes.api_v1.ai import ai_v1_bp
    app.register_blueprint(auth_v1_bp,    url_prefix='/api/v1/auth')
    app.register_blueprint(patient_v1_bp, url_prefix='/api/v1/patient')
    app.register_blueprint(consent_v1_bp, url_prefix='/api/v1/consent')
    app.register_blueprint(docs_v1_bp,    url_prefix='/api/v1/documents')
    app.register_blueprint(ai_v1_bp,      url_prefix='/api/v1/ai')

    # ==========================================================================
    # ROOT URL — redirect to portal selector
    @app.route('/')
    def index():
        from flask_login import current_user
        if current_user.is_authenticated:
            from routes.auth import _redirect_by_role
            return _redirect_by_role(current_user.role)
        return redirect(url_for('auth.portal_select'))

    # ==========================================================================
    # SERVE UPLOADED FILES (QR codes, documents)
    # When a template references /uploads/filename, this serves the file
    # ==========================================================================
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        # This legacy URL is used for public QR cards and organization portraits.
        # Never let it bypass the authenticated document/report download routes.
        from flask import abort
        from models import Document, DiagnosticReport, Procedure, Immunization, ImagingStudy, Encounter
        private_references = (
            Document.query.filter_by(file_path=filename).first(),
            DiagnosticReport.query.filter_by(document_path=filename).first(),
            Procedure.query.filter_by(document_path=filename).first(),
            Immunization.query.filter_by(document_path=filename).first(),
            ImagingStudy.query.filter_by(document_path=filename).first(),
            Encounter.query.filter_by(document_path=filename).first(),
        )
        if any(private_references):
            abort(404)
        from flask import send_from_directory
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # ==========================================================================
    # CONTEXT PROCESSOR
    # Makes variables available in ALL templates automatically
    # So we don't need to pass them manually to every render_template() call
    # ==========================================================================
    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        from datetime import datetime, date
        unread_count = 0
        if current_user.is_authenticated and current_user.role == 'patient' and current_user.patient:
            from models import Notification
            unread_count = Notification.query.filter_by(
                patient_id=current_user.patient.id, is_read=False
            ).count()
        return {
            'unread_count': unread_count,
            'now': utcnow(),
            'today': date.today().isoformat()
        }

    # ==========================================================================
    # NO-CACHE HEADERS — prevent browser back-button restoring logged-in pages
    # after logout. Every response gets Cache-Control: no-store so the browser
    # never serves a stale authenticated page from its cache.
    # ==========================================================================
    @app.after_request
    def set_no_cache(response):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma']        = 'no-cache'
        response.headers['Expires']       = '0'
        return response

    # ==========================================================================
    # CREATE DATABASE TABLES
    # This runs once when the app starts — creates all tables if they don't exist
    # ==========================================================================
    with app.app_context():
        db.create_all()
        _add_missing_profile_columns()

    return app


def _add_missing_profile_columns():
    """Apply safe, additive compatibility changes to existing SQL databases."""
    additions = {
        'users': {'firebase_uid': 'VARCHAR(128)'},
        'organizations': {
            'pincode': 'VARCHAR(20)',
            'website': 'VARCHAR(255)',
            'opening_hours': 'VARCHAR(100)',
            'closing_hours': 'VARCHAR(100)',
            'working_days': 'VARCHAR(100)',
            'emergency_hours': 'VARCHAR(100)',
            'services_offered': 'TEXT',
            'tests_available': 'TEXT',
        },
        'providers': {
            'profile_photo': 'VARCHAR(255)',
            'gender': 'VARCHAR(30)',
            'qualifications': 'TEXT',
            'experience_years': 'INTEGER',
            'consultation_fee': 'INTEGER',
            'consultation_type': 'VARCHAR(50)',
            'working_days': 'VARCHAR(100)',
            'working_hours': 'VARCHAR(200)',
            'slot_duration': 'INTEGER',
            'services': 'TEXT',
            'bio': 'TEXT',
            'languages': 'VARCHAR(255)',
        },
    }
    engine = db.engine
    inspector = inspect(engine)
    quote = engine.dialect.identifier_preparer.quote
    with engine.begin() as connection:
        for table, columns in additions.items():
            if not inspector.has_table(table):
                continue
            existing = {column['name'] for column in inspector.get_columns(table)}
            for name, sql_type in columns.items():
                if name not in existing:
                    connection.execute(text(
                        f'ALTER TABLE {quote(table)} ADD COLUMN {quote(name)} {sql_type}'
                    ))
    if inspector.has_table('users'):
        current_indexes = {
            index['name'] for index in inspect(engine).get_indexes('users')
        }
        if 'ix_users_firebase_uid' not in current_indexes:
            with engine.begin() as connection:
                connection.execute(text(
                    f'CREATE UNIQUE INDEX {quote("ix_users_firebase_uid")} '
                    f'ON {quote("users")} ({quote("firebase_uid")})'
                ))


# =============================================================================
# RUN THE APP
# This block only runs when you execute: python app.py
# (It doesn't run if this file is imported by another file)
# =============================================================================
if __name__ == '__main__':
    app = create_app()
    print("\n" + "="*60)
    print("  HealthVault is running!")
    print("  Open your browser and go to: http://localhost:5000")
    print("="*60 + "\n")
    # debug=True means the server auto-restarts when you change code
    # NEVER use debug=True in production
    debug = os.getenv('FLASK_DEBUG', '').strip().lower() in {'1', 'true', 'yes'}
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '5000'))
    app.run(debug=debug, host=host, port=port)
