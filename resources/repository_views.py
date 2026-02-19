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
from sqlalchemy import or_, func, extract, case
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
}

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _serialize_with_access(results, user):
    """
    Serializes KNR records and sets download_approved correctly per user type:
      - Superadmin : always True
      - Everyone else: True only if an Approved DownloadRequest exists for that user
    """
    is_superadmin = user.type == 'Superadmin'

    # For non-superadmins, fetch all their approved request knr_ids in one query
    # instead of hitting the DB once per row
    approved_ids = set()
    if not is_superadmin:
        approved_requests = DownloadRequest.query.filter_by(
            requested_by=user.id,
            status='Approved'
        ).all()
        approved_ids = {r.knr_id for r in approved_requests}

    return [
        {
            'id':                     r.id,
            'customer_name':          r.customer_name,
            'domain':                 r.domain,
            'sector':                 r.sector,
            'module_name':            r.module_name,
            'detailed_requirement':   r.detailed_requirement,
            'standard_custom':        r.standard_custom,
            'technical_details':      r.technical_details,
            'customer_benefit':       r.customer_benefit,
            'attach_code_or_document': r.attach_code_or_document,
            'attachment_filename':    r.attachment_filename,
            'Approver':               r.Approver,
            'Approval_status':        r.Approval_status,
            'Approval_date':          r.Approval_date.isoformat() if r.Approval_date else None,
            'business_justification': r.business_justification,
            'created_at':             r.created_at.isoformat() if r.created_at else None,
            'updated_at':             r.updated_at.isoformat() if r.updated_at else None,
            'rep_user_id':            r.rep_user_id,
            'user_id':                r.user_id,
            'username':               r.username,
            # Superadmin always True; others only if they have an approved request
            'download_approved':      True if is_superadmin else (r.id in approved_ids),
        }
        for r in results
    ]



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
                    'attach_code_or_document': r.attach_code_or_document,
                    'attachment_filename': r.attachment_filename,
                    'Approval_status': r.Approval_status,
                    'Approver': r.Approver,
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
                    'attach_code_or_document': r.attach_code_or_document,
                    'attachment_filename': r.attachment_filename,
                    'Approval_status': r.Approval_status,
                    'Approver': r.Approver,
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
                    'attach_code_or_document': r.attach_code_or_document,
                    'attachment_filename': r.attachment_filename,
                    'Approval_status': r.Approval_status,
                    'Approver': r.Approver,
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
            
            get_repos = KNR.query.filter_by(Approval_status='Sent for Approval').all()
            result = knrs.dump(get_repos)
            return jsonify(result)
        if check_user is not None and check_user.type == 'manager':
            
            get_repos = KNR.query.filter_by(Approval_status='Sent for Approval',Approver=check_user.name).all()
            result = knrs.dump(get_repos)
            return jsonify(result)
        if check_user is not None and check_user.type == 'user':
            
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
        if check_user is not None and check_user.type == 'manager':
            
            get_repos = KNR.query.filter_by(Approval_status='Sent for Approval',Approver=check_user.name).all()
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
                            'standard_custom', 'technical_details', 'customer_benefit']
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
                username = check_user.name,
                Approver = check_user.irm,
                Approval_status = 'Sent for Approval',
                irm = check_user.irm,
                srm = check_user.srm,
                buh = check_user.buh,
                bgh = check_user.bgh,
                attach_code_or_document='UPLOADED',
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
            get_repos = KNR.query.filter_by(Approval_status='Approved').all()
            result = knrs.dump(get_repos)
            return jsonify(result)
        else:
            return jsonify("Not Authorized"), 401

    @rlp.route('/upload-excel', methods=['POST'])
    @jwt_required()
    def upload_excel():
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 401

        excel_file = request.files['file']
        if excel_file.filename == '':
            return jsonify({'error': 'No selected file'}), 402
        if not allowed_file(excel_file.filename):
            return jsonify({'error': 'Invalid file format'}), 403

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
            'Customer benefit'
        ]

        def row_empty(row):
            return all(str(row[col]).strip() == '' for col in relevant_columns)

        df = df.loc[~df.apply(row_empty, axis=1)].reset_index(drop=True)

        # Validation lists
        module_options = [
            'FI: Financial Accounting', 'CO: Controlling', 'MM: Materials Management',
            'SD: Sales and Distribution', 'HCM: Human Capital Management', 'PP: Production Planning',
            'PM: Plant Maintenance', 'QM: Quality Management', 'PS: Project System',
            'FSCM: Financial Supply Chain Management', 'SRM: Supplier Relationship Management',
            'CRM: Customer Relationship Management', 'LE: Logistics Execution', 'WM: Warehouse Management',
            'EWM: Extended Warehouse Management', 'TRM: Treasury and Risk Management', 'FM: Funds Management',
            'IM: Investment Management', 'PLM: Product Lifecycle Management',
            'BI/BW: Business Intelligence / Business Warehouse', 'GRC: Governance, Risk, and Compliance',
            'MDM: Master Data Management', 'EHS: Environment, Health, and Safety',
            'SEM: Strategic Enterprise Management', 'BASIS: SAP Basis (technical administration)',
            'ABAP: Advanced Business Application Programming (development)',
            'PI/XI: Process Integration / Exchange Infrastructure (middleware)', 'EP: Enterprise Portal',
            'SOLMAN: SAP Solution Manager', 'Fiori: SAP Fiori (UX and apps)', 'FLM: File Lifecycle Management',
            'CPI: Cloud Platform Integration', 'BTP: Business Technology Platform', 'AI: Artificial Intelligence',
            'Cloud ALM: Cloud Application Lifecycle Management', 'API: Application Programming Interface',
            'SAC: SAP Analytics Cloud', 'Python: Python Programming Language',
            'Salesforce: Salesforce Customer 360 Platform'
        ]

        valid_domains = [
        'Technology', 'Healthcare', 'Finance', 'Education', 'Manufacturing', 'Energy', 'Retail',
        'Agriculture', 'Transport', 'Media & Entertainment', 'Government & Public Sector', 'Telecommunications',
        'Real Estate', 'Hospitality', 'Legal', 'Environmental Services', 'Construction',
        'Fashion', 'Sports', 'Food & Beverage', 'Aerospace', 'Chemicals', 'Logistics & Supply Chain',
        'Non-Profit & NGOs', 'Cybersecurity', 'Human Resources', 'Art & Culture', 'Mining & Metals', 'Electronics',
        'Insurance', 'Publishing', 'Consulting', 'Transportation Services', 'Marine', 'Luxury',
        'Automation & Robotics', 'Biotechnology', 'Tourism', 'Gaming', 'Advertising & Marketing',
        'Security Services', 'Transportation Infrastructure', 'Pharmaceuticals', 'Veterinary',
        'Renewables', 'Cloud Computing', 'Artificial Intelligence', 'Blockchain', 'Space Industry'
        ]


        valid_sectors = [
            'Software', 'Hardware', 'IT Services', 'AI & Data Science', 'Hospitals', 'Pharmaceuticals',
            'Biotechnology', 'Medical Devices', 'Banking', 'Insurance', 'Investment', 'FinTech',
            'Schools', 'Universities', 'EdTech', 'Vocational Training', 'Automotive', 'Electronics',
            'Textiles', 'Machinery', 'Oil & Gas', 'Renewables', 'Utilities', 'Mining', 'E-commerce',
            'FMCG', 'Luxury Goods', 'Consumer Electronics', 'Farming', 'AgriTech', 'Food Processing',
            'Dairy', 'Aviation', 'Shipping', 'Railways', 'Logistics', 'Film', 'Television', 'Gaming',
            'Publishing', 'Defense', 'Administration', 'Infrastructure', 'Policy',
            'Mobile Networks', 'Broadband', 'Satellite', 'IoT', 'Residential', 'Commercial', 'Industrial',
            'Smart Cities', 'Hotels', 'Restaurants', 'Travel Agencies', 'Tourism', 'Law Firms',
            'Corporate Law', 'Intellectual Property', 'Compliance', 'Waste Management', 'Recycling',
            'Water Treatment', 'Sustainability Consulting', 'Civil Engineering', 'Urban Development',
            'Smart Infrastructure', 'Housing Projects', 'Apparel', 'Footwear', 'Accessories',
            'Luxury Brands', 'Professional Teams', 'Sportswear', 'Events Management', 'Fitness','Restaurants'
            'Packaged Foods', 'Beverages', 'Nutrition','Defense Aviation', 'Commercial Airlines', 'Space Exploration',
            'Drones', 'Industrial Chemicals', 'Petrochemicals', 'Agrochemicals', 'Specialty Chemicals',
            'Warehousing', 'Distribution', 'Freight Forwarding', 'Cold Chain', 'Charities',
            'Foundations', 'Social Work', 'Community Development', 'Network Security', 'Data Protection',
            'Cloud Security', 'Risk Management', 'Recruitment', 'Training', 'Payroll', 'Employee Engagement',
            'Museums', 'Performing Arts', 'Heritage Conservation', 'Design', 'Iron & Steel',
            'Precious Metals', 'Rare Earths', 'Industrial Minerals','Consumer Electronics', 'Semiconductors', 'Wearables',
            'Smart Devices', 'Life Insurance', 'Health Insurance', 'Property Insurance', 'Reinsurance',
            'Books', 'Magazines', 'Digital Media', 'Academic Journals', 'Management Consulting',
            'IT Consulting', 'Strategy', 'Operations', 'Ride-Sharing', 'Public Transit',
            'Courier Services', 'Fleet Management','Shipping', 'Fishing', 'Ports', 'Marine Engineering',
            'Jewelry', 'High-End Fashion', 'Luxury Cars', 'Exclusive Travel', 'Industrial Robots',
            'Service Robots', 'AI Robotics', 'Automation Systems', 'Genomics', 'Stem Cell Research',
            'Bioinformatics', 'Medical Research', 'Adventure Tourism', 'Eco-Tourism',
            'Cultural Tourism', 'Cruises', 'Esports', 'Mobile Games', 'Console Games',
            'VR/AR Gaming', 'Digital Marketing', 'Branding', 'Market Research', 'Public Relations',
            'Private Security', 'Surveillance', 'Risk Assessment', 'Emergency Response',
            'Highways','Railways', 'Airports','Ports', 'Drug Development', 'Generic Drugs', 'Clinical Trials',
            'Distribution', 'Animal Healthcare', 'Pet Products', 'Livestock Services', 'Research',
            'Solar', 'Wind', 'Hydropower', 'Geothermal', 'SaaS', 'PaaS', 'IaaS', 'Hybrid Cloud',
            'Machine Learning', 'Natural Language Processing', 'Computer Vision', 'Robotics',
            'Cryptocurrency', 'Smart Contracts', 'Supply Chain Blockchain', 'DeFi',
            'Satellites', 'Space Tourism', 'Asteroid Mining', 'Rocket Manufacturing'
        ]


        def is_valid_value(value, valid_list):
            return str(value).strip() in valid_list

        # Validate each row
        invalid_rows = []
        records = []
        for idx, row in df.iterrows():
            domain_val = row.get('Domain', '').strip()
            sector_val = row.get('Sector', '').strip()
            module_val = row.get('Module Name', '').strip()

            validation_errors = []
            if domain_val and not is_valid_value(domain_val, valid_domains):
                validation_errors.append(f"Invalid Domain: '{domain_val}' (Row {idx+2})")
            if sector_val and not is_valid_value(sector_val, valid_sectors):
                validation_errors.append(f"Invalid Sector: '{sector_val}' (Row {idx+2})")
            if module_val and not is_valid_value(module_val, module_options):
                validation_errors.append(f"Invalid Module: '{module_val}' (Row {idx+2})")

            if validation_errors:
                invalid_rows.extend(validation_errors)
            else:
                knr = KNR(
                    customer_name=row.get('Customer name', ''),
                    domain=row.get('Domain', ''),
                    sector=row.get('Sector', ''),
                    module_name=row.get('Module Name', ''),
                    detailed_requirement=row.get('Detailed requirement', ''),
                    standard_custom=row.get('Standard/Custom', ''),
                    technical_details=row.get('Technical details(Z object name or Process developed/configured)', ''),
                    customer_benefit=row.get('Customer benefit', ''),
                    attach_code_or_document='UPLOADED',
                    username=check_user.name,
                    Approver=check_user.irm,
                    Approval_status='Sent for Approval',
                    irm=check_user.irm,
                    srm=check_user.srm,
                    buh=check_user.buh,
                    bgh=check_user.bgh,
                    attachment_filename=None,
                    attachment_data=None,
                    rep_user_id=rep_user_id_value,
                    user_id=rep_user_id_value
                )
                records.append(knr)

        if invalid_rows:
            return jsonify({
                'error': 'Validation failed for the following rows:',
                'details': invalid_rows
            }), 404

        if not records:
            return jsonify({'error': 'No valid data rows found in Excel'}), 405

        db.session.add_all(records)
        db.session.commit()
        return jsonify({'message': f"{len(records)} records inserted successfully"}), 200


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
            total_repos = KNR.query.filter_by(Approval_status='Approved').count()
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

        if check_user is not None and check_user.type == 'Superadmin':

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
    @jwt_required()
    def refview(id):
        # ── Identify the requesting user ──────────────────────────────────────
        identity = get_jwt_identity()
        user     = User.query.filter_by(yash_id=identity).first()

        if user is None:
            return jsonify({'error': 'User not found'}), 401

        # ── Fetch the repository ──────────────────────────────────────────────
        check_file = KNR.query.filter_by(id=id).first()

        if check_file is None:
            return jsonify({'error': 'Repository not found'}), 404

        if not check_file.attachment_data:
            return jsonify({'error': 'No attachment found for this repository'}), 404

        # ── Superadmin bypasses the approval gate ─────────────────────────────
        if user.type != 'Superadmin':
            approved = DownloadRequest.query.filter_by(
                knr_id=id,
                requested_by=user.id,
                status='Approved'
            ).first()

            if not approved:
                return jsonify({
                    'error': 'Access denied. Request approval from a Superadmin before viewing this attachment.'
                }), 403

        # ── Detect MIME type ──────────────────────────────────────────────────
        filename = check_file.attachment_filename or f'repository_{id}'
        filedata = check_file.attachment_data

        mimetype, _ = mimetypes.guess_type(filename)

        if mimetype is None:
            if filedata[:4] == b'%PDF':
                mimetype = 'application/pdf'
            elif filedata[:8] == b'\x89PNG\r\n\x1a\n':
                mimetype = 'image/png'
            elif filedata[:3] == b'\xff\xd8\xff':
                mimetype = 'image/jpeg'
            elif filedata[:4] == b'PK\x03\x04':
                ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
                mime_map = {
                    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                    'zip' : 'application/zip',
                }
                mimetype = mime_map.get(ext, 'application/octet-stream')
            else:
                mimetype = 'application/octet-stream'

        # ── Log the access ────────────────────────────────────────────────────
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent')

        log = DownloadLog(
            user_id=user.id,
            yash_id=user.yash_id,
            username=user.name,
            file_id=check_file.id,
            filename=filename,
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.session.add(log)
        db.session.commit()

        # ── Serve inline ──────────────────────────────────────────────────────
        response = send_file(
            BytesIO(filedata),
            mimetype=mimetype,
            download_name=filename,
            as_attachment=False
        )
        response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
        return response


    

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
                .filter(KNR.Approval_status == 'Approved')
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
            data = db.session.query(KNR.domain, func.count(KNR.id)).filter(KNR.Approval_status == 'Approved').group_by(KNR.domain).all()
            
        
        elif check_user.type == 'manager':
            data = db.session.query(KNR.domain, func.count(KNR.id)).filter(KNR.user_id == check_user.id).group_by(KNR.domain).all()
            
        elif check_user.type == 'user':
            data = db.session.query(KNR.domain, func.count(KNR.id)).filter(KNR.user_id == check_user.id).group_by(KNR.domain).all()
            
        else:
            return jsonify({"msg": "Forbidden"}), 403
        
        result = {domain: count for domain, count in data}
        return jsonify(result)
    
    

    @rlp.route('/search', methods=['GET'])
    @jwt_required()
    def search_repositories():
        identity   = get_jwt_identity()
        user       = User.query.filter_by(yash_id=identity).first()

        if user is None:
            return jsonify({'error': 'User not found'}), 401

        selected_filter = (request.args.get('filter') or 'Any').strip()
        query_text      = (request.args.get('query')  or '').strip()

        if not query_text:
            return jsonify({'error': 'query is required'}), 400

        q          = f'%{query_text}%'
        base_query = KNR.query.filter_by(Approval_status='Approved')

        if selected_filter in FILTER_COLUMN_MAP:
            column  = getattr(KNR, FILTER_COLUMN_MAP[selected_filter])
            results = base_query.filter(column.ilike(q)).all()
        else:
            results = base_query.filter(
                or_(
                    KNR.domain.ilike(q),
                    KNR.module_name.ilike(q),
                    KNR.customer_name.ilike(q),
                    KNR.sector.ilike(q),
                    KNR.standard_custom.ilike(q),
                    KNR.technical_details.ilike(q),
                    KNR.detailed_requirement.ilike(q),
                    KNR.customer_benefit.ilike(q),
                    KNR.business_justification.ilike(q),
                    KNR.username.ilike(q),
                )
            ).all()

        return jsonify(_serialize_with_access(results, user)), 200



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
            get_repos = KNR.query.filter_by(Approval_status='Approved', user_id=check_user.id).paginate(page=page, per_page=10)
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
            get_repos = KNR.query.filter_by(Approval_status='Approved', user_id=check_user.id).all()
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
            get_repos = KNR.query.filter_by(Approval_status='Sent for Approval', user_id=check_user.id).paginate(page=page, per_page=10)
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
            get_repos = KNR.query.filter_by(Approval_status='Sent for Approval',user_id=check_user.id).all()
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
            get_repos = KNR.query.filter_by(Approval_status='Pending', user_id=check_user.id).paginate(page=page, per_page=10)
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
            get_repos = KNR.query.filter_by(Approval_status='Pending', user_id=check_user.id).all()
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
            get_repos = KNR.query.filter_by(Approval_status='Rejected', user_id=check_user.id).paginate(page=page, per_page=10)
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
            get_repos = KNR.query.filter_by(Approval_status='Rejected', user_id=check_user.id).all()
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


    @rlp.route("/delegate", methods=["POST"])
    @jwt_required()
    def delegate_repository():
        data = request.get_json() or {}
        repo_id = data.get("id")
        print(repo_id)
        delegate_user_id = data.get("delegateUserId")
        print(delegate_user_id)
        if not repo_id or not delegate_user_id:
            return jsonify({"success": False, "message": "repoId and delegateUserId are required"}), 400

        current_user_id = get_jwt_identity()

        repo = KNR.query.get(repo_id)
        if not repo:
            return jsonify({"success": False, "message": "Repository not found"}), 404

        if getattr(repo, "Approval_status", None) == "Approved":
            return jsonify({"success": False, "message": "Already approved, cannot delegate"}), 400

        delegate_user = User.query.get(delegate_user_id)
        if not delegate_user:
            return jsonify({"success": False, "message": "Delegate user not found"}), 404

        # Update repo fields (use your real column names)
        repo.Approval_status = "Sent for Approval"
        repo.Approver = delegate_user.name
        

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Repository delegated successfully",
            
        }), 200

    @rlp.route('/download-all-logs', methods=['GET'])
    def download_all_logs():
        """
        Endpoint to fetch all login logs without pagination
        Returns all records from the database
        """
        try:
            # Query all login logs from the database
            # Order by timestamp descending to get newest first
            all_logs = LoginLog.query.order_by(LoginLog.timestamp.desc()).all()
            
            # Convert to JSON serializable format
            logs_data = []
            for log in all_logs:
                logs_data.append({
                    'id': log.id,
                    'yash_id': log.yash_id,
                    'ip_address': log.ip_address,
                    'user_agent': log.user_agent,
                    'success': log.success,
                    'message': log.message,
                    'timestamp': log.timestamp.isoformat() if log.timestamp else None
                })
            
            return jsonify(logs_data), 200
            
        except Exception as e:
            print(f"Error fetching all logs: {str(e)}")
            return jsonify({'error': 'Failed to fetch logs'}), 500


    @rlp.route('/manager-stats/monthly', methods=['GET'])
    @jwt_required()
    def get_manager_stats_monthly():
        try:
            current_user = get_jwt_identity()
            check_user = User.query.filter_by(yash_id=current_user).first()

            # Superadmin only
            if not check_user or check_user.type != 'Superadmin':
                return jsonify({'success': False, 'error': 'Unauthorized'}), 403

            year = request.args.get('year', type=int)
            month = request.args.get('month', type=int)
            manager_type = request.args.get('manager_type', 'irm')

            manager_field_map = {
                'irm': KNR.irm,
                'srm': KNR.srm,
                'buh': KNR.buh,
                'bgh': KNR.bgh
            }

            manager_field = manager_field_map.get(manager_type, KNR.irm)

            query = db.session.query(
                manager_field.label('manager_name'),
                extract('year', KNR.created_at).label('year'),
                extract('month', KNR.created_at).label('month'),
                func.sum(case((KNR.Approval_status == 'Approved', 1), else_=0)).label('approved_count'),
                func.sum(case((KNR.Approval_status == 'Sent for Approval', 1), else_=0)).label('pending_count'),
                func.sum(case((KNR.Approval_status == 'Rejected', 1), else_=0)).label('rejected_count'),
                func.count(KNR.id).label('total_count')
            ).filter(
                manager_field != 'NA',
                manager_field.isnot(None),
                manager_field != ''
            )

            if year:
                query = query.filter(extract('year', KNR.created_at) == year)
            if month:
                query = query.filter(extract('month', KNR.created_at) == month)

            results = query.group_by(
                manager_field,
                extract('year', KNR.created_at),
                extract('month', KNR.created_at)
            ).order_by(
                extract('year', KNR.created_at).desc(),
                extract('month', KNR.created_at).desc(),
                manager_field
            ).all()

            data = []
            for row in results:
                data.append({
                    'manager_name': row.manager_name,
                    'year': int(row.year) if row.year else None,
                    'month': int(row.month) if row.month else None,
                    'approved': int(row.approved_count or 0),
                    'pending': int(row.pending_count or 0),
                    'rejected': int(row.rejected_count or 0),
                    'total': int(row.total_count or 0)
                })

            return jsonify({'success': True, 'data': data, 'manager_type': manager_type}), 200

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500


    @rlp.route('/manager-stats/years', methods=['GET'])
    @jwt_required()
    def get_available_years():
        try:
            current_user = get_jwt_identity()
            check_user = User.query.filter_by(yash_id=current_user).first()

            if not check_user or check_user.type != 'Superadmin':
                return jsonify({'success': False, 'error': 'Unauthorized'}), 403

            years = db.session.query(
                extract('year', KNR.created_at).label('year')
            ).distinct().order_by(
                extract('year', KNR.created_at).desc()
            ).all()

            year_list = [int(y.year) for y in years if y.year]

            return jsonify({'success': True, 'years': year_list}), 200

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @rlp.route('/all-approved', methods=['GET'])
    @jwt_required()
    def get_all_approved():
        identity   = get_jwt_identity()
        user       = User.query.filter_by(yash_id=identity).first()

        if user is None:
            return jsonify({'error': 'User not found'}), 401

        results = KNR.query.filter_by(Approval_status='Approved').all()
        return jsonify(_serialize_with_access(results, user)), 200
    
    @rlp.route('/getalladdedrepos', methods=['GET'])
    @jwt_required()
    def getalladdedrepos():
        currentuser = get_jwt_identity()
        checkuser = User.query.filter_by(yash_id=currentuser).first()

        if checkuser is not None and checkuser.type == 'Superadmin':
            page = request.args.get('page', 1, type=int)
            getrepos = KNR.query.filter_by(user_id=checkuser.id).paginate(page=page, per_page=10)
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
                    'attach_code_or_document': r.attach_code_or_document,
                    'attachment_filename': r.attachment_filename,
                    'Approval_status': r.Approval_status,
                    'Approver': r.Approver,
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
                    'attach_code_or_document': r.attach_code_or_document,
                    'attachment_filename': r.attachment_filename,
                    'Approval_status': r.Approval_status,
                    'Approver': r.Approver,
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
                    'attach_code_or_document': r.attach_code_or_document,
                    'attachment_filename': r.attachment_filename,
                    'Approval_status': r.Approval_status,
                    'Approver': r.Approver,
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
        
    @rlp.route('/getalladdedreporecords', methods=['GET'])
    @jwt_required()
    def getalladdedreporecords():
        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()
        if check_user is not None and check_user.type == 'Superadmin':
            get_repos = KNR.query.filter_by(user_id=check_user.id).all()
            result = knrs.dump(get_repos)
            return jsonify(result)
        if check_user is not None and check_user.type == 'manager':
            get_repos = KNR.query.filter_by(user_id=check_user.id).all()
            result = knrs.dump(get_repos)
            return jsonify(result)
        elif check_user is not None and check_user.type == 'user':
            get_repos = KNR.query.filter_by(user_id=check_user.id).all()
            result = knrs.dump(get_repos)
            return jsonify(result)
        else:
            return jsonify("Not Authorized"), 401