# routes/api_v1/documents.py — Document Vault JSON API
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Document, User
from datetime import datetime
import utils, os

docs_v1_bp = Blueprint('docs_v1', __name__)


def _get_patient():
    import json
    raw = get_jwt_identity()
    try:
        identity = json.loads(raw) if isinstance(raw, str) else raw
    except:
        identity = {'role': 'patient', 'user_id': raw}
        
    if identity.get('role') != 'patient':
        return None, (jsonify({'error': 'Patient account required.'}), 403)
    user = User.query.get(identity['user_id'])
    if not user or not user.patient:
        return None, (jsonify({'error': 'Patient not found.'}), 404)
    return user.patient, None


@docs_v1_bp.route('/', methods=['GET'])
@jwt_required()
def list_documents():
    patient, err = _get_patient()
    if err: return err
    filter_type = request.args.get('type', 'all')
    query = Document.query.filter_by(patient_id=patient.id, is_archived=False)
    if filter_type != 'all':
        query = query.filter_by(document_type=filter_type)
    docs = query.order_by(Document.document_date.desc()).all()
    return jsonify({'documents': [{
        'id': d.id, 'title': d.title, 'document_type': d.document_type,
        'document_date': str(d.document_date) if d.document_date else None,
        'provider': d.provider, 'file_name': d.file_name,
        'file_type': d.file_type,
        'file_size': d.file_size,
        'tags': d.tags, 'source': d.source,
        'upload_date': d.upload_date.isoformat() if d.upload_date else None,
        'download_url': f'/api/v1/documents/{d.id}/download'
    } for d in docs]})


@docs_v1_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload():
    patient, err = _get_patient()
    if err: return err
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided.'}), 400
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400
    if not utils.allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed. Upload PDF, JPG, or PNG.'}), 400
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
        patient_id=patient.id, title=title, document_type=doc_type,
        document_date=doc_date, provider=provider,
        file_path=filename, file_name=original_name,
        file_type=file_ext, file_size=file_size,
        tags=tags, source='patient_uploaded'
    )
    db.session.add(doc)
    utils.log_audit_event(
        patient_id=patient.id, actor_id=patient.user_id,
        actor_name=patient.full_name, action='uploaded',
        resource_type='document', resource_description=title, status='success'
    )
    db.session.commit()
    return jsonify({'success': True, 'doc_id': doc.id, 'title': doc.title}), 201


@docs_v1_bp.route('/<doc_id>/download', methods=['GET'])
@jwt_required()
def download(doc_id):
    patient, err = _get_patient()
    if err: return err
    doc = Document.query.filter_by(id=doc_id, patient_id=patient.id).first()
    if not doc:
        return jsonify({'error': 'Document not found.'}), 404
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], doc.file_path,
                               as_attachment=True, download_name=doc.file_name)


@docs_v1_bp.route('/<doc_id>', methods=['DELETE'])
@jwt_required()
def delete(doc_id):
    patient, err = _get_patient()
    if err: return err
    doc = Document.query.filter_by(id=doc_id, patient_id=patient.id).first()
    if not doc:
        return jsonify({'error': 'Document not found.'}), 404
    try:
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], doc.file_path)
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass
    title = doc.title
    db.session.delete(doc)
    db.session.commit()
    return jsonify({'success': True, 'message': f'Document "{title}" deleted.'})
