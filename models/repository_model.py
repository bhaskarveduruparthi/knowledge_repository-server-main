from default_settings import db
from datetime import datetime
from models.user_model import User

class KNR(db.Model):
    __tablename__ = 'knr'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_name = db.Column(db.String(255), nullable=False)
    domain = db.Column(db.String(255), nullable=False)
    sector = db.Column(db.String(255), nullable=False)
    module_name = db.Column(db.String(255), nullable=False)
    detailed_requirement = db.Column(db.Text, nullable=False)
    standard_custom = db.Column(db.String(100), nullable=False)
    technical_details = db.Column(db.Text, nullable=False)
    customer_benefit = db.Column(db.Text, nullable=False)
    remarks = db.Column(db.Text, nullable=False)
    attach_code_or_document = db.Column(db.String(255), default="Not Attached")
    attachment_data = db.Column(db.LargeBinary(length=65536))
    attachment_filename = db.Column(db.String(255), nullable=True)
    Approver = db.Column(db.String(100), default="NA", nullable=True)
    Approval_status = db.Column(db.String(100), default="Not Approved")
    Approval_date = db.Column(db.Date)
    business_justification = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    rep_user_id = db.Column(db.Integer, nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    
class DownloadLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80), nullable=True)
    yash_id = db.Column(db.String(80), nullable=True)
    username = db.Column(db.String(255), nullable=True)
    file_id = db.Column(db.Integer, nullable=False)
    filename = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(256))