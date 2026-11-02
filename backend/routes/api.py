# =============================================================================
# routes/api.py — JSON API endpoints for Chart.js
# =============================================================================
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from models import DiagnosticReport, Observation

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/charts/lab-trend/<test_name>')
@login_required
def lab_trend(test_name):
    """Return historical values of a specific lab test for charting."""
    if current_user.role != 'patient':
        return jsonify({'error': 'Unauthorized'}), 403
    patient = current_user.patient
    observations = Observation.query.join(DiagnosticReport).filter(
        DiagnosticReport.patient_id == patient.id,
        Observation.test_name.ilike(f'%{test_name}%')
    ).order_by(DiagnosticReport.report_date.asc()).all()
    data = [
        {
            'date': obs.report.report_date.strftime('%d %b %Y'),
            'value': float(obs.value) if obs.value and obs.value.replace('.','',1).isdigit() else None,
            'unit': obs.unit,
            'is_abnormal': obs.is_abnormal
        }
        for obs in observations
    ]
    return jsonify({'test_name': test_name, 'data': data})


@api_bp.route('/notifications/count')
@login_required
def notification_count():
    if current_user.role != 'patient':
        return jsonify({'count': 0})
    from models import Notification
    count = Notification.query.filter_by(
        patient_id=current_user.patient.id, is_read=False
    ).count()
    return jsonify({'count': count})

@api_bp.route("/search/live")
@login_required
def live_search():
    import datetime
    from flask import request
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"results": []})
    results = []
    
    def get_date(obj, field):
        d = getattr(obj, field, None)
        if not d:
            d = getattr(obj, 'created_at', None)
        if isinstance(d, datetime.datetime) or isinstance(d, datetime.date):
            return d
        return datetime.date.min

    if current_user.role == "patient":
        from models import DiagnosticReport, Medication, Condition
        search_term = f"%{q}%"
        for r in DiagnosticReport.query.filter(DiagnosticReport.patient_id == current_user.patient.id, DiagnosticReport.report_name.ilike(search_term)).limit(10).all():
            results.append({"title": r.report_name, "type": "Lab Report", "url": f"/patient/records/lab/{r.id}", "icon": "bi-file-text", "date": get_date(r, 'report_date')})
        for m in Medication.query.filter(Medication.patient_id == current_user.patient.id, Medication.medicine_name.ilike(search_term)).limit(10).all():
            results.append({"title": m.medicine_name, "type": "Medication", "url": "/patient/medications", "icon": "bi-capsule", "date": get_date(m, 'start_date')})
        for c in Condition.query.filter(Condition.patient_id == current_user.patient.id, Condition.condition_name.ilike(search_term)).limit(10).all():
            results.append({"title": c.condition_name, "type": "Condition", "url": "/patient/conditions", "icon": "bi-heart-pulse", "date": get_date(c, 'diagnosis_date')})
            
        results.sort(key=lambda x: x['date'], reverse=True)
        for res in results:
            if hasattr(res['date'], 'strftime') and res['date'].year > 1900:
                res['type'] += f" • {res['date'].strftime('%d %b %Y')}"
            del res['date']
            
    elif current_user.role in ["doctor", "lab"]:
        from models import HealthIdentity
        for i in HealthIdentity.query.filter(HealthIdentity.hv_id.ilike(f"%{q}%")).limit(5).all():
            results.append({"title": i.patient.full_name if i.patient else "Unknown Patient", "type": f"HV-ID: {i.hv_id}", "action_id": i.hv_id, "icon": "bi-person-badge"})
            
    return jsonify({"results": results[:8]})
