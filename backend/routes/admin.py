from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import db, User, Patient, Provider, AuditEvent

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        return "Access Denied", 403
        
    stats = {
        'total_users': User.query.count(),
        'total_patients': Patient.query.count(),
        'total_doctors': Provider.query.filter_by(provider_type='doctor').count(),
        'total_events': AuditEvent.query.count()
    }
    
    recent_events = AuditEvent.query.order_by(AuditEvent.timestamp.desc()).limit(20).all()
    
    return render_template('admin/dashboard.html', stats=stats, recent_events=recent_events)
