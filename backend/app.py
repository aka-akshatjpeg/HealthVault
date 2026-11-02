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
from models import db, User
import os

# Load settings from the .env file (like SECRET_KEY, database path)
load_dotenv()


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
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'healthvault-dev-secret-change-in-production')
    # This is where the SQLite database file will be saved
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///healthvault.db'
    # Turn off a feature we don't need (saves memory)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # Where uploaded files are stored
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
    # Maximum file size: 16 megabytes
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    # JWT configuration for mobile API
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.config['SECRET_KEY'])
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600       # 1 hour
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 2592000   # 30 days

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
            'now': datetime.utcnow(),
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

    return app


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
    app.run(debug=True, host='0.0.0.0', port=5000)
