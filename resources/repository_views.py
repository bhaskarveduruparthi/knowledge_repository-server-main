import io
import mimetypes
from flask import Response, request, jsonify, send_file
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user_model import  LoginLog, User
from models.repository_model import KNR, DownloadLog, DownloadRequest
from schemas.repository_schema import knr, knrs
from schemas.user_schema import user, users
from schemas.support_schema import login_log, login_logs, download_log, download_logs
from default_settings import db
from werkzeug.utils import secure_filename
import pandas as pd
from datetime import datetime
from blueprints import rlp
from sqlalchemy import or_
import os
from sqlalchemy import func
import numpy as np
from openpyxl import load_workbook
from io import BytesIO


FILTER_COLUMN_MAP = {
    "Domain": "domain",
    "Module": "module_name",
    "Customer Name": "customer_name",
    "Sector": "sector",
    "Standard/Custom": "standard_custom",
}

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class KNR_Requirements(Resource):

    @rlp.route('/getallrepos', methods=['GET'])
    @jwt_required()
    def getallrepos():
        currentuser = get_jwt_identity()
        checkuser = User.query.filter_by(yash_id=currentuser).first()

        if checkuser is not None and checkuser.type == 'Superadmin':
            page = request.args.get('page', 1, type=int)
            getrepos = KNR.query.filter_by(Approval_status='Approved').paginate(page=page, per_page=10)
            result = []
            for r in getrepos.items:
                result.append({
                    'id': r.id,
                    'customer_name': r.customer_name,
                    'domain': r.domain,
                    'sector': r.sector,
                    'module_name': r.module_name,
                    'detailed_requirement': r.detailed_requirement,
                    'standard_custom': r.standard_custom,
                    'technical_details': r.technical_details,
                    'customer_benefit': r.customer_benefit,
                    'remarks': r.remarks,
                    'attach_code_or_document': r.attach_code_or_document,
                    'attachment_filename': r.attachment_filename,
                    'Approval_status': r.Approval_status,
                    'irm': r.irm,
                    'srm': r.srm,
                    'buh': r.buh,
                    'bgh': r.bgh,
                    'username': r.username,
                    'created_at': r.created_at,
                    'download_approved': True  # Superadmin can always download
                })
            return jsonify(result)

        if checkuser is not None and checkuser.type == 'manager':
            page = request.args.get('page', 1, type=int)
            getrepos = KNR.query.filter_by(Approval_status='Approved').paginate(page=page, per_page=10)
            result = []
            for r in getrepos.items:
                approved_req = DownloadRequest.query.filter_by(
                    knr_id=r.id,
                    requested_by=checkuser.id,
                    status='Approved'
                ).first() is not None
            
                result.append({
                    'id': r.id,
                    'customer_name': r.customer_name,
                    'domain': r.domain,
                    'sector': r.sector,
                    'module_name': r.module_name,
                    'detailed_requirement': r.detailed_requirement,
                    'standard_custom': r.standard_custom,
                    'technical_details': r.technical_details,
                    'customer_benefit': r.customer_benefit,
                    'remarks': r.remarks,
                    'attach_code_or_document': r.attach_code_or_document,
                    'attachment_filename': r.attachment_filename,
                    'Approval_status': r.Approval_status,
                    'irm': r.irm,
                    'srm': r.srm,
                    'buh': r.buh,
                    'bgh': r.bgh,
                    'username': r.username,
                    'created_at': r.created_at,
                    'download_approved': approved_req  
                })
            return jsonify(result)

        elif checkuser is not None and checkuser.type == 'user':
            page = request.args.get('page', 1, type=int)
            getrepos = KNR.query.filter_by(user_id=checkuser.id).paginate(page=page, per_page=10)
            result = []
            for r in getrepos.items:
                approved_req = DownloadRequest.query.filter_by(
                    knr_id=r.id,
                    requested_by=checkuser.id,
                    status='Approved'
                ).first() is not None

                result.append({
                    'id': r.id,
                    'customer_name': r.customer_name,
                    'domain': r.domain,
                    'sector': r.sector,
                    'module_name': r.module_name,
                    'detailed_requirement': r.detailed_requirement,
                    'standard_custom': r.standard_custom,
                    'technical_details': r.technical_details,
                    'customer_benefit': r.customer_benefit,
                    'remarks': r.remarks,
                    'attach_code_or_document': r.attach_code_or_document,
                    'attachment_filename': r.attachment_filename,
                    'Approval_status': r.Approval_status,
                    'irm': r.irm,
                    'srm': r.srm,
                    'buh': r.buh,
                    'bgh': r.bgh,
                    'username': r.username,
                    'created_at': r.created_at,
                    'download_approved': approved_req
                })
            return jsonify(result)

        else:
            return jsonify("Not Authorized"), 401


    @rlp.route('/getapprovalrepos', methods=['GET'])
    @jwt_required()
    def getapprovalrepos():
        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()
        if check_user is not None and check_user.type == 'Superadmin':
            
            get_repos = KNR.query.filter_by(Approval_status='Sent for Approval',Approver=check_user.name).all()
            result = knrs.dump(get_repos)
            return jsonify(result)
        if check_user is not None and check_user.type == 'manager':
            
            get_repos = KNR.query.filter_by(Approval_status='Sent for Approval',Approver=check_user.name).all()
            result = knrs.dump(get_repos)
            return jsonify(result)
        else:
            return jsonify("Not Authorized"), 401
    
    @rlp.route('/getapprovalreposrecords', methods=['GET'])
    @jwt_required()
    def getapprovalreposrecords():
        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()
        if check_user is not None and check_user.type == 'Superadmin':
            get_repos = KNR.query.filter_by(Approval_status='Sent for Approval').all()
            result = knrs.dump(get_repos)
            return jsonify(result)
        else:
            return jsonify("Not Authorized"), 401


    @rlp.route('/createrepo', methods=['POST'])
    @jwt_required()
    def add_repository():
        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()
        if check_user is not None:

            data = request.json
            required_fields = ['customer_name', 'domain', 'sector', 'module_name', 'detailed_requirement',
                            'standard_custom', 'technical_details', 'customer_benefit', 'remarks']
            missing_fields = [field for field in required_fields if field not in data or not data[field]]
            if missing_fields:
                return jsonify({'error': 'Missing required fields', 'fields': missing_fields}), 400

            new_repo = KNR(
                customer_name=data['customer_name'],
                domain=data['domain'],
                sector=data['sector'],
                module_name=data['module_name'],
                detailed_requirement=data['detailed_requirement'],
                standard_custom=data['standard_custom'],
                technical_details=data['technical_details'],
                customer_benefit=data['customer_benefit'],
                remarks=data['remarks'],
                username = check_user.name,
                Approver = check_user.irm,
                Approval_status = 'Sent for Approval',
                irm = check_user.irm,
                srm = check_user.srm,
                buh = check_user.buh,
                bgh = check_user.bgh,

                rep_user_id = check_user.id,
                user_id = check_user.id
            )

            db.session.add(new_repo)
            db.session.commit()
            return jsonify({'message': 'Repository created and saved successfully', 'repository': data}), 201
        else:
           return jsonify({'error': 'Not Authorised'}), 400 

    @rlp.route('/getallreporecords', methods=['GET'])
    @jwt_required()
    def getallreporecords():
        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()
        if check_user is not None and check_user.type == 'Superadmin':
            get_repos = KNR.query.filter_by(Approval_status='Approved').all()
            result = knrs.dump(get_repos)
            return jsonify(result)
        if check_user is not None and check_user.type == 'manager':
            get_repos = KNR.query.filter_by(Approval_status='Approved').all()
            result = knrs.dump(get_repos)
            return jsonify(result)
        elif check_user is not None and check_user.type == 'user':
            get_repos = KNR.query.filter_by(user_id=check_user.id).all()
            result = knrs.dump(get_repos)
            return jsonify(result)
        else:
            return jsonify("Not Authorized"), 401

    @rlp.route('/upload-excel', methods=['POST'])
    @jwt_required()
    def upload_excel():
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        excel_file = request.files['file']
        if excel_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if not allowed_file(excel_file.filename):
            return jsonify({'error': 'Invalid file format'}), 400

        filename = secure_filename(excel_file.filename)
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        excel_file.save(filepath)

        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()
        rep_user_id_value = check_user.id if check_user else 1

        # Read Excel
        df = pd.read_excel(filepath)
        df = df.replace({np.nan: ''})

        relevant_columns = [
            'Customer name', 'Domain', 'Sector', 'Module Name', 'Detailed requirement',
            'Standard/Custom', 'Technical details(Z object name or Process developed/configured)',
            'Customer benefit', 'Remarks'
        ]

        def row_empty(row):
            return all(str(row[col]).strip() == '' for col in relevant_columns)

        df = df.loc[~df.apply(row_empty, axis=1)].reset_index(drop=True)

        records = []
        for _, row in df.iterrows():
            knr = KNR(
                customer_name=row.get('Customer name', ''),
                domain=row.get('Domain', ''),
                sector=row.get('Sector', ''),
                module_name=row.get('Module Name', ''),
                detailed_requirement=row.get('Detailed requirement', ''),
                standard_custom=row.get('Standard/Custom', ''),
                technical_details=row.get('Technical details(Z object name or Process developed/configured)', ''),
                customer_benefit=row.get('Customer benefit', ''),
                remarks=row.get('Remarks', ''),
                attach_code_or_document='UPLOADED',
                username = check_user.name,
                Approver = check_user.irm,
                Approval_status = 'Sent for Approval',
                irm = check_user.irm,
                srm = check_user.srm,
                buh = check_user.buh,
                bgh = check_user.bgh,
                attachment_filename=None,
                attachment_data=None,
                rep_user_id=rep_user_id_value,
                user_id=rep_user_id_value
            )
            records.append(knr)

        if not records:
            return jsonify({'error': 'No valid data rows found in Excel'}), 400

        db.session.add_all(records)
        db.session.commit()
        return jsonify({'message': f"{len(records)} records inserted"}), 200

    @rlp.route('/repoapproval/<int:id>', methods=['PUT'])
    @jwt_required()
    def approvalchange_repo(id):
        check_repo = KNR.query.filter_by(id=id).first()
        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()

        if check_repo is not None:
            check_repo.Approval_status = "Approved"
            check_repo.Approval_date = datetime.utcnow().date()
            db.session.commit()
            return jsonify("Status of the Repo Changed")
        else:
            return jsonify("Form Not Found")
    
    @rlp.route('/reporejection/<int:id>', methods=['PUT'])
    @jwt_required()
    def approvalreject_repo(id):
        check_repo = KNR.query.filter_by(id=id).first()
        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()

        if check_repo is not None and check_user.type == 'Superadmin':
            check_repo.Approval_status = "Rejected"
            check_repo.Approver = check_user.name
            check_repo.Approval_date = datetime.utcnow().date()
            db.session.commit()
            return jsonify("Status of the Repo Changed")
        else:
            return jsonify("Form Not Found")

    @rlp.route('/sendforapproval/<int:id>', methods=['PUT'])
    @jwt_required()
    def sendforapprovalchange_repo(id):
        check_repo = KNR.query.filter_by(id=id).first()
        if check_repo is None:
            return jsonify("Repository Not Found"), 404

        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()
        if check_user is None:
            return jsonify("User Not Found"), 404

        if check_user.type.strip().lower() != 'user':
            return jsonify("Unauthorized"), 403

        data = request.get_json()
        if not data or 'business_justification' not in data:
            return jsonify("Business Justification is required"), 400

        business_justification = data['business_justification']
        check_repo.Approval_status = "Sent for Approval"
        check_repo.business_justification = business_justification
        db.session.commit()
        return jsonify("Status of the Repo Changed and Sent for Approval")

    @rlp.route('/counts', methods=['GET'])
    @jwt_required()
    def get_all_counts():
        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()

        if check_user is not None and check_user.type == 'Superadmin':
            total_repos = KNR.query.count()
            approved_repos = KNR.query.filter_by(Approval_status='Approved').count()
            unapproved_repos = KNR.query.filter_by(Approval_status='Rejected').count()
            sent_for_approval_repos = KNR.query.filter_by(Approval_status='Sent for Approval').count()
            
        elif check_user is not None and check_user.type == 'user':
            total_repos = KNR.query.filter_by(user_id=check_user.id).count()
            approved_repos = KNR.query.filter_by(user_id=check_user.id, Approval_status='Approved').count()
            unapproved_repos = KNR.query.filter_by(user_id=check_user.id, Approval_status='Rejected').count()
            sent_for_approval_repos = KNR.query.filter_by(user_id=check_user.id, Approval_status='Sent for Approval').count()
        elif check_user is not None and check_user.type == 'manager':
            total_repos = KNR.query.filter_by(user_id=check_user.id).count()
            approved_repos = KNR.query.filter_by(user_id=check_user.id, Approval_status='Approved').count()
            unapproved_repos = KNR.query.filter_by(user_id=check_user.id, Approval_status='Rejected').count()
            sent_for_approval_repos = KNR.query.filter_by(user_id=check_user.id, Approval_status='Sent for Approval').count()
        else:
            return jsonify({"msg": "Unauthorized"}), 401

        return jsonify({
            "all_repos_count": total_repos,
            "approved_repos_count": approved_repos,
            "unapproved_repos_count": unapproved_repos,
            "sentforapproval_count": sent_for_approval_repos
        }), 200


    

    @rlp.route('/download-file/<int:id>', methods=['GET'])
    @jwt_required()
    def download_file(id):
        print(f"Requested download for KNR id: {id}")

        knr = KNR.query.get(id)
        if knr is None:
            print(f"DEBUG ERROR: No record found for ID {id}")
            return jsonify({'error': f'No record found for ID {id}'}), 404

        print("KNR Record found:", knr)
        if not knr.attachment_data:
            print(f"DEBUG ERROR: No attachment data found for record ID {id}")
            return jsonify({'error': f'No attachment data found for record ID {id}'}), 404

        data = knr.attachment_data
        print(f"DEBUG: attachment_data size: {len(data)} bytes")
        print(f"DEBUG: First 8 bytes: {data[:8]}")

        ext = ''
        mime_type = 'application/octet-stream'
        # ZIP file signature (PK\x03\x04)
        if data[:4] == b'PK\x03\x04':
            ext = '.zip'
            mime_type = 'application/zip'
            print("DEBUG: ZIP file detected")
        else:
            print("DEBUG: File is not ZIP, using default extension and mime type.")

        filename = knr.attachment_filename or f'attachment_{id}'
        if not filename.endswith(ext):
            filename += ext
        print(f"DEBUG: Download filename set to: {filename}")

        return Response(
            data,
            mimetype=mime_type,
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    
    @rlp.route('/deleterepo/<int:id>', methods=['DELETE'])
    @jwt_required()
    def delete_repo(id):
        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()

        if check_user is not None:

            check_repo = KNR.query.filter_by(id=id).first()
            if check_repo is not None:
                db.session.delete(check_repo)
                db.session.commit()
                return jsonify("Repo Deleted")
            else:
                return jsonify("Repo Not Found")
        else:
            return jsonify("User Not Authorized")


    @rlp.route('upload_ref/<int:id>', methods=['POST'])
    @jwt_required()
    def upload_ref(id):
            
            check_repo = KNR.query.filter_by(id=id).first()
            if check_repo is not None:
                        

                file = request.files['file']
                filename = file.filename
                

                allowed_formats = ['.doc', '.docx', '.xlsx', '.csv', '.pdf', '.png', '.jpg']
                file_format = '.'+ filename.rsplit('.', 1)[1]
                                    
                if file_format in allowed_formats:

                    filename = secure_filename(f"{check_repo.customer_name}_{check_repo.module_name}_{check_repo.domain}.{file.filename.rsplit('.', 1)[1]}")
                    check_repo.attachment_filename= filename
                    check_repo.attachment_data = file.read()
                    check_repo.attach_code_or_document = 'ATTACHED'
                    
                    db.session.commit()
                    return jsonify({'success': 'File uploaded successfully'})

                            
                        
                else:
                    return jsonify({'message':'File Error uploading'}),400
            else:
                return jsonify({'message':'Repository Not Found'}),

    @rlp.route('/refdownload/<int:id>')
    @jwt_required()
    def refdownload(id):
        check_file = KNR.query.filter_by(id=id).first()
        if check_file is None:
            return "File not found", 404

        # Ensure attachment exists
        if not check_file.attachment_data:
            return "No attachment found for this repository", 404

        # Get identity (you store yash_id in the token)
        identity = get_jwt_identity()

        # Fetch user based on yash_id
        user = User.query.filter_by(yash_id=identity).first()

        ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)
        user_agent = request.headers.get("User-Agent")

        # Only log user fields if user exists
        log = DownloadLog(
            user_id=user.id if user else None,
            yash_id=user.yash_id if user else None,
            username=user.name if user else None,
            file_id=check_file.id,
            filename=check_file.attachment_filename or f"repository_{check_file.id}",
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.session.add(log)
        db.session.commit()

        # Prepare filename and data
        filename = check_file.attachment_filename or f"repository_{check_file.id}"
        filedata = check_file.attachment_data

        # Guess mimetype safely
        mimetype, _ = mimetypes.guess_type(filename)
        if mimetype is None:
            mimetype = "application/octet-stream"

        return send_file(
            BytesIO(filedata),
            mimetype=mimetype,
            download_name=filename,
            as_attachment=True,
        )


    @rlp.route('/refview/<int:id>')
    def refview (id):
        check_file = KNR.query.filter_by(id=id).first()
        if check_file is not None:
            filename = check_file.attachment_filename
            filedata = check_file.attachment_data

            # Guess the mimetype based on the filename
            mimetype, _ = mimetypes.guess_type(filename)
            if mimetype is None:
                mimetype = 'application/octet-stream'  # fallback
                    
            return send_file(
                BytesIO(filedata), 
                mimetype=mimetype,
                download_name=filename,
                as_attachment=False   # <-- CHANGED HERE
            )
        # Handle file not found
        return "File not found", 404

    

    @rlp.route('/repodatabymodule', methods=['GET'])
    @jwt_required()
    def data_by_module():
        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()


        if current_user is None:
            return jsonify({"msg": "Unauthorized"}), 401

        # Superadmin: all data
        if check_user.type == 'Superadmin':
            data = (
                db.session.query(KNR.module_name, func.count(KNR.id))
                .group_by(KNR.module_name)
                .all()
            )

        # Manager: only their own data (by user_id)
        elif check_user.type == 'manager':
            data = (
                db.session.query(KNR.module_name, func.count(KNR.id))
                .filter(KNR.user_id == check_user.id)
                .group_by(KNR.module_name)
                .all()
            )
        elif check_user.type == 'user':
            data = (
                db.session.query(KNR.module_name, func.count(KNR.id))
                .filter(KNR.user_id == check_user.id)
                .group_by(KNR.module_name)
                .all()
            )

        # Other types: not allowed (optional)
        else:
            return jsonify({"msg": "Forbidden"}), 403

        result = {module: count for module, count in data}
        return jsonify(result), 200

        

    @rlp.route('/repodatabydomain', methods=['GET'])
    @jwt_required()
    def data_by_domain():
        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()


        if current_user is None:
            return jsonify({"msg": "Unauthorized"}), 401
        
        if check_user.type == 'Superadmin':
            data = db.session.query(KNR.domain, func.count(KNR.id)).group_by(KNR.domain).all()
            
        
        elif check_user.type == 'manager':
            data = db.session.query(KNR.domain, func.count(KNR.id)).filter(KNR.user_id == check_user.id).group_by(KNR.domain).all()
            
        elif check_user.type == 'user':
            data = db.session.query(KNR.domain, func.count(KNR.id)).filter(KNR.user_id == check_user.id).group_by(KNR.domain).all()
            
        else:
            return jsonify({"msg": "Forbidden"}), 403
        
        result = {domain: count for domain, count in data}
        return jsonify(result)
    
    

    @rlp.route("/search", methods=["GET"])
    def search_repositories():
        selected_filter = request.args.get("filter")   # Dropdown selected filter, may be None
        query_text = request.args.get("query")         # Search text

        if not query_text:
            return jsonify({"error": "query is required"}), 400

        # Normalize query once
        q = f"%{query_text}%"

        if selected_filter and selected_filter in FILTER_COLUMN_MAP and selected_filter != "Any":
            # Specific field search
            column_name = FILTER_COLUMN_MAP[selected_filter]
            column = getattr(KNR, column_name)
            results = KNR.query.filter(column.ilike(q)).all()
        else:
            # "any" or no filter -> search in all relevant fields with the whole query string
            results = KNR.query.filter(
                or_(
                    KNR.domain.ilike(q),
                    KNR.module_name.ilike(q),
                    KNR.customer_name.ilike(q),
                    KNR.sector.ilike(q),
                    KNR.standard_custom.ilike(q),
                    KNR.technical_details.ilike(q),
                    KNR.detailed_requirement.ilike(q),
                    KNR.remarks.ilike(q),
                    KNR.customer_benefit.ilike(q),
                    KNR.business_justification.ilike(q),
                    KNR.username.ilike(q),
                )
            ).all()

        data = [
            {
                "id": r.id,
                "customer_name": r.customer_name,
                "domain": r.domain,
                "sector": r.sector,
                "module_name": r.module_name,
                "detailed_requirement": r.detailed_requirement,
                "standard_custom": r.standard_custom,
                "technical_details": r.technical_details,
                "customer_benefit": r.customer_benefit,
                "remarks": r.remarks,
                "attach_code_or_document": r.attach_code_or_document,
                "attachment_filename": r.attachment_filename,
                "Approver": r.Approver,
                "Approval_status": r.Approval_status,
                "Approval_date": r.Approval_date.isoformat() if r.Approval_date else None,
                "business_justification": r.business_justification,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                "rep_user_id": r.rep_user_id,
                "user_id": r.user_id,
                "username": r.username,
            }
            for r in results
        ]

        return jsonify(data), 200



    @rlp.route('/getallapprovedrepos', methods=['GET'])
    @jwt_required()
    def getallapprovedrepos():
        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()
        if check_user is not None and check_user.type == 'Superadmin':
            page = request.args.get('page', 1, type=int)
            get_repos = KNR.query.filter_by(Approval_status='Approved').paginate(page=page, per_page=10)
            result = knrs.dump(get_repos)
            return jsonify(result)
        if check_user is not None and check_user.type == 'manager':
            page = request.args.get('page', 1, type=int)
            get_repos = KNR.query.filter_by(Approval_status='Approved', Approver=check_user.name).paginate(page=page, per_page=10)
            result = knrs.dump(get_repos)
            return jsonify(result)
        elif check_user is not None and check_user.type == 'user':
            page = request.args.get('page', 1, type=int)
            get_repos = KNR.query.filter_by(Approval_status='Approved',user_id=check_user.id).paginate(page=page, per_page=10)
            result = knrs.dump(get_repos)
            return jsonify(result)
        else:
            return jsonify("Not Authorized"), 401
        
    @rlp.route('/getallapprovedreporecords', methods=['GET'])
    @jwt_required()
    def getallapprovedreporecords():
        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()
        if check_user is not None and check_user.type == 'Superadmin':
            get_repos = KNR.query.filter_by(Approval_status='Approved').all()
            result = knrs.dump(get_repos)
            return jsonify(result)
        if check_user is not None and check_user.type == 'manager':
            get_repos = KNR.query.filter_by(Approval_status='Approved', Approver=check_user.name).all()
            result = knrs.dump(get_repos)
            return jsonify(result)
        elif check_user is not None and check_user.type == 'user':
            get_repos = KNR.query.filter_by(Approval_status='Approved',user_id=check_user.id).all()
            result = knrs.dump(get_repos)
            return jsonify(result)
        else:
            return jsonify("Not Authorized"), 401


    @rlp.route('/getallpendingrepos', methods=['GET'])
    @jwt_required()
    def getallpendingrepos():
        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()
        if check_user is not None and check_user.type == 'Superadmin':
            page = request.args.get('page', 1, type=int)
            get_repos = KNR.query.filter_by(Approval_status='Sent for Approval').paginate(page=page, per_page=10)
            result = knrs.dump(get_repos)
            return jsonify(result)
        if check_user is not None and check_user.type == 'manager':
            page = request.args.get('page', 1, type=int)
            get_repos = KNR.query.filter_by(Approval_status='Sent for Approval', Approver=check_user.name).paginate(page=page, per_page=10)
            result = knrs.dump(get_repos)
            return jsonify(result)
        elif check_user is not None and check_user.type == 'user':
            page = request.args.get('page', 1, type=int)
            get_repos = KNR.query.filter_by(Approval_status='Sent for Approval',user_id=check_user.id).paginate(page=page, per_page=10)
            result = knrs.dump(get_repos)
            return jsonify(result)
        else:
            return jsonify("Not Authorized"), 401
        
    @rlp.route('/getallpendingreporecords', methods=['GET'])
    @jwt_required()
    def getallpendingreporecords():
        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()
        if check_user is not None and check_user.type == 'Superadmin':
            get_repos = KNR.query.filter_by(Approval_status='Sent for Approval').all()
            result = knrs.dump(get_repos)
            return jsonify(result)
        if check_user is not None and check_user.type == 'manager':
            get_repos = KNR.query.filter_by(Approval_status='Sent for Approval',Approver=check_user.name).all()
            result = knrs.dump(get_repos)
            return jsonify(result)
        elif check_user is not None and check_user.type == 'user':
            get_repos = KNR.query.filter_by(Approval_status='Sent for Approval',user_id=check_user.id).all()
            result = knrs.dump(get_repos)
            return jsonify(result)
        else:
            return jsonify("Not Authorized"), 401


    @rlp.route('/getallunapprovedrepos', methods=['GET'])
    @jwt_required()
    def getallunapprovedrepos():
        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()
        if check_user is not None and check_user.type == 'Superadmin':
            page = request.args.get('page', 1, type=int)
            get_repos = KNR.query.filter_by(Approval_status='Pending').paginate(page=page, per_page=10)
            result = knrs.dump(get_repos)
            return jsonify(result)
        if check_user is not None and check_user.type == 'manager':
            page = request.args.get('page', 1, type=int)
            get_repos = KNR.query.filter_by(Approval_status='Pending', Approver='check_user.name').paginate(page=page, per_page=10)
            result = knrs.dump(get_repos)
            return jsonify(result)
        elif check_user is not None and check_user.type == 'user':
            page = request.args.get('page', 1, type=int)
            get_repos = KNR.query.filter_by(Approval_status='Pending',user_id=check_user.id).paginate(page=page, per_page=10)
            result = knrs.dump(get_repos)
            return jsonify(result)
        else:
            return jsonify("Not Authorized"), 401
        
    @rlp.route('/getallunapprovedreporecords', methods=['GET'])
    @jwt_required()
    def getallunapprovedreporecords():
        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()
        if check_user is not None and check_user.type == 'Superadmin':
            get_repos = KNR.query.filter_by(Approval_status='Pending').all()
            result = knrs.dump(get_repos)
            return jsonify(result)
        if check_user is not None and check_user.type == 'manager':
            get_repos = KNR.query.filter_by(Approval_status='Pending', Approver='check_user.name').all()
            result = knrs.dump(get_repos)
            return jsonify(result)
        elif check_user is not None and check_user.type == 'user':
            get_repos = KNR.query.filter_by(Approval_status='Pending',user_id=check_user.id).all()
            result = knrs.dump(get_repos)
            return jsonify(result)
        else:
            return jsonify("Not Authorized"), 401
        

    @rlp.route('/getallrejectedrepos', methods=['GET'])
    @jwt_required()
    def getallrejectedrepos():
        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()
        if check_user is not None and check_user.type == 'Superadmin':
            page = request.args.get('page', 1, type=int)
            get_repos = KNR.query.filter_by(Approval_status='Rejected').paginate(page=page, per_page=10)
            result = knrs.dump(get_repos)
            return jsonify(result)
        if check_user is not None and check_user.type == 'manager':
            page = request.args.get('page', 1, type=int)
            get_repos = KNR.query.filter_by(Approval_status='Rejected', Approver=check_user.name).paginate(page=page, per_page=10)
            result = knrs.dump(get_repos)
            return jsonify(result)
        elif check_user is not None and check_user.type == 'user':
            page = request.args.get('page', 1, type=int)
            get_repos = KNR.query.filter_by(Approval_status='Rejected',user_id=check_user.id).paginate(page=page, per_page=10)
            result = knrs.dump(get_repos)
            return jsonify(result)
        else:
            return jsonify("Not Authorized"), 401
        
    @rlp.route('/getallrejectedreporecords', methods=['GET'])
    @jwt_required()
    def getallrejectedreporecords():
        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()
        if check_user is not None and check_user.type == 'Superadmin':
            get_repos = KNR.query.filter_by(Approval_status='Rejected').all()
            result = knrs.dump(get_repos)
            return jsonify(result)
        if check_user is not None and check_user.type == 'manager':
            get_repos = KNR.query.filter_by(Approval_status='Rejected', Approver=check_user.name).all()
            result = knrs.dump(get_repos)
            return jsonify(result)
        elif check_user is not None and check_user.type == 'user':
            get_repos = KNR.query.filter_by(Approval_status='Rejected',user_id=check_user.id).all()
            result = knrs.dump(get_repos)
            return jsonify(result)
        else:
            return jsonify("Not Authorized"), 401

    @rlp.route('/getlogs', methods=['GET'])
    @jwt_required()
    def getlogs():
        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()
        if check_user is not None and check_user.type == 'Superadmin':
            page = request.args.get('page', 1, type=int)
            get_logs = LoginLog.query.paginate(page=page, per_page=10)
            result = login_logs.dump(get_logs)
            return jsonify(result)
        if check_user is not None and check_user.type == 'manager':
            page = request.args.get('page', 1, type=int)
            get_logs = LoginLog.query.paginate(page=page, per_page=10)
            result = login_logs.dump(get_logs)
            return jsonify(result)
        
        else:
            return jsonify("Not Authorized"), 401
        
    @rlp.route('/getlogrecords', methods=['GET'])
    @jwt_required()
    def getlogrecords():
        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()
        if check_user is not None and check_user.type == 'Superadmin':
            get_logs = LoginLog.query.all()
            result = login_logs.dump(get_logs)
            return jsonify(result)
        if check_user is not None and check_user.type == 'manager':
            get_logs = LoginLog.query.all()
            result = login_logs.dump(get_logs)
            return jsonify(result)
        
        else:
            return jsonify("Not Authorized"), 401
        
    @rlp.route('/getdownloadlogs', methods=['GET'])
    @jwt_required()
    def getdownloadlogs():
        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()
        if check_user is not None and check_user.type == 'Superadmin':
            page = request.args.get('page', 1, type=int)
            get_logs = DownloadLog.query.paginate(page=page, per_page=10)
            result = download_logs.dump(get_logs)
            return jsonify(result)
        if check_user is not None and check_user.type == 'manager':
            page = request.args.get('page', 1, type=int)
            get_logs = DownloadLog.query.paginate(page=page, per_page=10)
            result = download_logs.dump(get_logs)
            return jsonify(result)
        
        else:
            return jsonify("Not Authorized"), 401
        
    @rlp.route('/getdownloadlogrecords', methods=['GET'])
    @jwt_required()
    def getdownloadlogrecords():
        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()
        if check_user is not None and check_user.type == 'Superadmin':
            get_logs = DownloadLog.query.all()
            result = download_logs.dump(get_logs)
            return jsonify(result)
        if check_user is not None and check_user.type == 'manager':
            get_logs = DownloadLog.query.all()
            result = download_logs.dump(get_logs)
            return jsonify(result)
        
        else:
            return jsonify("Not Authorized"), 401
        
    @rlp.route('/top-users-solutions', methods=['GET'])
    def top_users_solutions():
        top_users = (
            db.session.query(
                KNR.username,
                func.count(KNR.id).label('solution_count')
            )
            .group_by(KNR.username)
            .order_by(func.count(KNR.id).desc())
            .limit(10)
            .all()
        )
        
        labels = [user.username for user in top_users]
        data = [int(user.solution_count or 0) for user in top_users]
        
        return jsonify({
            'labels': labels,
            'datasets': [{
                'label': 'Solutions',
                'data': data,
                'backgroundColor': ['#3e95cd', '#8e5ea2', '#3cba9f', '#e8c3b9', '#c45850', 
                                '#36a2eb', '#ff6384', '#ffcd56', '#4bc0c0', '#9966ff']
            }]
        })

    @rlp.route('/download-request/<int:id>', methods=['POST'])
    @jwt_required()
    def create_download_request(id):
        # JWT identity is yash_id in your app
        identity = get_jwt_identity()  # e.g. '1100032'
        user = User.query.filter_by(yash_id=identity).first_or_404()

        data = request.get_json() or {}
        justification = data.get('justification', '')

        knr = KNR.query.get_or_404(id)

        existing = DownloadRequest.query.filter_by(
            knr_id=knr.id,
            requested_by=user.id,
            status='Pending'
        ).first()
        if existing:
            return jsonify({'message': 'Request already pending'}), 400

        req = DownloadRequest(
            knr_id=knr.id,
            requested_by=user.id,
            requested_by_name=user.name,
            justification=justification
        )
        db.session.add(req)
        db.session.commit()

        return jsonify({'message': 'Download request sent to Superadmin'}), 200



    @rlp.route('/download-requests', methods=['GET'])
    @jwt_required()
    def list_download_requests():
        identity = get_jwt_identity()  # yash_id
        user = User.query.filter_by(yash_id=identity).first_or_404()
        if user.type != 'Superadmin':
            return jsonify({'message': 'Forbidden'}), 403

        reqs = DownloadRequest.query.order_by(DownloadRequest.requested_at.desc()).all()
        result = []
        for r in reqs:
            result.append({
                'id': r.id,
                'status': r.status,
                'requested_at': r.requested_at.isoformat() if r.requested_at else None,
                'justification': r.justification,
                'knr_id': r.knr_id,
                'repo_customer_name': r.knr.customer_name if r.knr else None,
                'repo_module_name': r.knr.module_name if r.knr else None,
                'requested_by_name': r.requested_by_name,
                'requested_by_email': r.requester.email if r.requester else None,
            })
        return jsonify(result), 200




    @rlp.route('/download-requests/<int:id>/approve', methods=['POST'])
    @jwt_required()
    def approve_download_request(id):
        identity = get_jwt_identity()  # yash_id
        approver = User.query.filter_by(yash_id=identity).first_or_404()

        req = DownloadRequest.query.get_or_404(id)
        if req.status != 'Pending':
            return jsonify({'message': 'Already processed'}), 400

        req.status = 'Approved'
        req.approved_by = approver.id
        req.approved_at = datetime.utcnow()
        db.session.commit()

        return jsonify({'message': 'Request approved'}), 200


    @rlp.route('/download-requests/<int:id>/reject', methods=['POST'])
    @jwt_required()
    def reject_download_request(id):
        identity = get_jwt_identity()  # yash_id
        approver = User.query.filter_by(yash_id=identity).first_or_404()

        req = DownloadRequest.query.get_or_404(id)
        if req.status != 'Pending':
            return jsonify({'message': 'Already processed'}), 400

        req.status = 'Rejected'
        req.approved_by = approver.id
        req.approved_at = datetime.utcnow()
        db.session.commit()

        return jsonify({'message': 'Request rejected'}), 200


    

    @rlp.route('/repos/refdownload/<int:id>', methods=['GET'])
    @jwt_required()
    def download_repo(id):
        # Here identity is yash_id in your current code; fetch user by yash_id
        identity = get_jwt_identity()
        user = User.query.filter_by(yash_id=identity).first_or_404()

        knr = KNR.query.get_or_404(id)

        # Superadmin bypass
        if user.type != 'Superadmin':
            approved_req = DownloadRequest.query.filter_by(
                knr_id=knr.id,
                requested_by=user.id,
                status='Approved'
            ).first()
            if not approved_req:
                return jsonify({'message': 'Download not approved for this repository'}), 403

        if not knr.attachment_data:
            return jsonify({'message': 'No file attached'}, 404)

        # log download
        ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)
        user_agent = request.headers.get("User-Agent")

        log = DownloadLog(
            user_id=user.id,
            yash_id=user.yash_id,
            username=user.name,
            file_id=knr.id,
            filename=knr.attachment_filename or f"repository_{knr.id}",
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(log)
        db.session.commit()

        filename = knr.attachment_filename or f"repository_{knr.id}"
        filedata = knr.attachment_data

        mimetype, _ = mimetypes.guess_type(filename)
        if mimetype is None:
            mimetype = 'application/octet-stream'

        return send_file(
            io.BytesIO(filedata),
            mimetype=mimetype,
            download_name=filename,
            as_attachment=True
        )


