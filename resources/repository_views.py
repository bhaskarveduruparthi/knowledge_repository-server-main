import mimetypes
from flask import Response, request, jsonify, send_file
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user_model import User
from models.repository_model import KNR
from schemas.repository_schema import knr, knrs
from schemas.user_schema import user, users
from default_settings import db
from werkzeug.utils import secure_filename
import pandas as pd
from datetime import datetime
from blueprints import rlp
import os
from sqlalchemy import func
import numpy as np
from openpyxl import load_workbook
from io import BytesIO

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class KNR_Requirements(Resource):

    @rlp.route('/getallrepos', methods=['GET'])
    @jwt_required()
    def getallrepos():
        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()
        if check_user is not None and check_user.type == 'Superadmin':
            page = request.args.get('page', 1, type=int)
            get_repos = KNR.query.paginate(page=page, per_page=10)
            result = knrs.dump(get_repos)
            return jsonify(result)
        if check_user is not None and check_user.type == 'manager':
            page = request.args.get('page', 1, type=int)
            get_repos = KNR.query.paginate(page=page, per_page=10)
            result = knrs.dump(get_repos)
            return jsonify(result)
        elif check_user is not None and check_user.type == 'user':
            page = request.args.get('page', 1, type=int)
            get_repos = KNR.query.filter_by(user_id=check_user.id).paginate(page=page, per_page=10)
            result = knrs.dump(get_repos)
            return jsonify(result)
        else:
            return jsonify("Not Authorized"), 401

    @rlp.route('/getapprovalrepos', methods=['GET'])
    @jwt_required()
    def getapprovalrepos():
        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()
        if check_user is not None and check_user.type == 'Superadmin':
            page = request.args.get('page', 1, type=int)
            get_repos = KNR.query.filter_by(Approval_status='Sent for Approval').paginate(page=page, per_page=10)
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
            get_repos = KNR.query.all()
            result = knrs.dump(get_repos)
            return jsonify(result)
        if check_user is not None and check_user.type == 'manager':
            get_repos = KNR.query.all()
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
            'Customer benefit', 'Remarks', 'Attach the code or process document'
        ]

        def row_empty(row):
            return all(str(row[col]).strip() == '' for col in relevant_columns)

        df = df.loc[~df.apply(row_empty, axis=1)].reset_index(drop=True)

        # Extract embedded worksheets
        workbook = load_workbook(filepath, data_only=True)
        embedded_data = {}
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            # Convert sheet to DataFrame
            data = sheet.values
            cols = next(data)
            data = list(data)
            df_sheet = pd.DataFrame(data, columns=cols)
            # Convert DataFrame to Excel bytes
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_sheet.to_excel(writer, sheet_name=sheet_name, index=False)
            embedded_data[sheet_name] = output.getvalue()

        # Process additional attached files
        attachment_files = request.files.getlist('attachments')
        attachment_map = {}
        for f in attachment_files:
            fname = secure_filename(f.filename)
            attachment_map[fname] = f.read()

        records = []
        for _, row in df.iterrows():
            # Save embedded worksheet
            for sheet_name, sheet_data in embedded_data.items():
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
                    attach_code_or_document=sheet_name,
                    attachment_filename=sheet_name,
                    attachment_data=sheet_data,
                    rep_user_id=rep_user_id_value,
                    user_id=rep_user_id_value
                )
                records.append(knr)

            # Save additional attachments
            for fname, fdata in attachment_map.items():
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
                    attach_code_or_document=fname,
                    attachment_filename=fname,
                    attachment_data=fdata,
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

        if check_repo is not None and check_user.type == 'Superadmin':
            check_repo.Approval_status = "Approved"
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
            unapproved_repos = KNR.query.filter_by(Approval_status='Not Approved').count()
            total_users = User.query.count()
        elif check_user is not None and check_user.type == 'user':
            total_repos = KNR.query.filter_by(user_id=check_user.id).count()
            approved_repos = KNR.query.filter_by(user_id=check_user.id, Approval_status='Approved').count()
            unapproved_repos = KNR.query.filter_by(user_id=check_user.id, Approval_status='Not Approved').count()
            total_users = User.query.count()
        else:
            return jsonify({"msg": "Unauthorized"}), 401

        return jsonify({
            "all_repos_count": total_repos,
            "approved_repos_count": approved_repos,
            "unapproved_repos_count": unapproved_repos,
            "users_count": total_users
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
    def refdownload(id):
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
                as_attachment=True
            )
        # Handle file not found
        return "File not found", 404
    

    @rlp.route('/repodatabymodule',methods=['GET'])
    def data_by_module():
        data = db.session.query(KNR.module_name, func.count(KNR.id)).group_by(KNR.module_name).all()
        result = {module: count for module, count in data}
        return jsonify(result)

    @rlp.route('/repodatabydomain', methods=['GET'])
    def data_by_domain():
        data = db.session.query(KNR.domain, func.count(KNR.id)).group_by(KNR.domain).all()
        result = {domain: count for domain, count in data}
        return jsonify(result)