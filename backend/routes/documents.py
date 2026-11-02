# =============================================================================
# routes/documents.py — Document Upload and Management
# =============================================================================
from flask import Blueprint, render_template, redirect, url_for, request, flash, send_from_directory, current_app
from flask_login import login_required, current_user
from models import db, Document
from functools import wraps
from datetime import datetime
import os
import utils

documents_bp = Blueprint('documents', __name__, url_prefix='/documents')


def patient_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != 'patient':
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@documents_bp.route('/')
@patient_required
def vault():
    patient = current_user.patient
    filter_type = request.args.get('type', 'all')
    query = Document.query.filter_by(patient_id=patient.id, is_archived=False)
    if filter_type != 'all':
        query = query.filter_by(document_type=filter_type)
    documents = query.order_by(Document.document_date.desc()).all()
    return render_template('patient/documents.html', patient=patient, documents=documents, filter_type=filter_type)


@documents_bp.route('/upload', methods=['GET', 'POST'])
@patient_required
def upload():
    patient = current_user.patient
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected.', 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(request.url)
        if not utils.allowed_file(file.filename):
            flash('File type not allowed. Please upload PDF, JPG, or PNG.', 'danger')
            return redirect(request.url)

        filename = utils.secure_filename_custom(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        file_size = os.path.getsize(filepath)
        original_name = file.filename
        file_ext = original_name.rsplit('.', 1)[-1].lower() if '.' in original_name else ''

        title = request.form.get('title', original_name)
        doc_type = request.form.get('document_type', 'other')
        doc_date_str = request.form.get('document_date', '')
        provider = request.form.get('provider', '')
        tags = request.form.get('tags', '')

        doc_date = None
        if doc_date_str:
            try:
                doc_date = datetime.strptime(doc_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        doc = Document(
            patient_id=patient.id,
            title=title,
            document_type=doc_type,
            document_date=doc_date,
            provider=provider,
            file_path=filename,
            file_name=original_name,
            file_type=file_ext,
            file_size=file_size,
            tags=tags,
            source='patient_uploaded'
        )
        db.session.add(doc)

        utils.log_audit_event(
            patient_id=patient.id, actor_id=current_user.id,
            actor_name=patient.full_name, action='uploaded',
            resource_type='document', resource_description=title, status='success'
        )

        db.session.commit()
        flash(f'Document "{title}" uploaded successfully.', 'success')
        return redirect(url_for('documents.vault'))

    return render_template('patient/upload_document.html', patient=patient)


@documents_bp.route('/view/<doc_id>')
@patient_required
def view(doc_id):
    patient = current_user.patient
    doc = Document.query.filter_by(id=doc_id, patient_id=patient.id).first_or_404()
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], doc.file_path)


@documents_bp.route('/download/<doc_id>')
@patient_required
def download(doc_id):
    patient = current_user.patient
    doc = Document.query.filter_by(id=doc_id, patient_id=patient.id).first_or_404()
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], doc.file_path,
                               as_attachment=True, download_name=doc.file_name)


@documents_bp.route('/delete/<doc_id>', methods=['POST'])
@patient_required
def delete(doc_id):
    patient = current_user.patient
    doc = Document.query.filter_by(id=doc_id, patient_id=patient.id).first_or_404()
    # Remove physical file
    try:
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], doc.file_path)
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass
    db.session.delete(doc)
    db.session.commit()
    flash(f'Document "{doc.title}" deleted.', 'success')
    return redirect(url_for('documents.vault'))
