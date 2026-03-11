from default_settings import db
import datetime
from datetime import datetime, timezone
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
    attach_code_or_document = db.Column(db.String(255), default="Not Attached")
    attachment_data = db.Column(db.LargeBinary(length=65536))
    attachment_filename = db.Column(db.String(255), nullable=True)
    Approver = db.Column(db.String(100), default="NA", nullable=True)
    Approval_status = db.Column(db.String(100), default="Pending")
    Approval_date = db.Column(db.Date)
    business_justification = db.Column(db.Text, nullable=True)
    username = db.Column(db.String(length=100),default="NA", nullable=True)
    irm = db.Column(db.String(length=100),default="NA", nullable=True)
    srm = db.Column(db.String(length=100),default="NA", nullable=True)
    buh = db.Column(db.String(length=100),default="NA", nullable=True)
    bgh = db.Column(db.String(length=100),default="NA", nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    rep_user_id = db.Column(db.Integer, nullable=False)

    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
class Modules(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    module_name = db.Column(db.String(255), nullable=False)
    key_name = db.Column(db.String(255), nullable=False)

class Domain(db.Model):
    __tablename__ = 'domains'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(150), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sectors    = db.relationship('Sector', backref='domain', lazy=True,
                                 cascade='all, delete-orphan')

    def to_dict(self, include_sectors=True):
        d = {
            'id':         self.id,
            'name':       self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_sectors:
            d['sectors'] = [s.to_dict() for s in self.sectors]
        return d


class Sector(db.Model):
    __tablename__ = 'sectors'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(150), nullable=False)
    domain_id  = db.Column(db.Integer, db.ForeignKey('domains.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('name', 'domain_id', name='uq_sector_domain'),
    )

    def to_dict(self):
        return {
            'id':         self.id,
            'name':       self.name,
            'domain_id':  self.domain_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }



    
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

class ViewLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80), nullable=True)
    yash_id = db.Column(db.String(80), nullable=True)
    username = db.Column(db.String(255), nullable=True)
    file_id = db.Column(db.Integer, nullable=False)
    filename = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(256))

class DownloadRequest(db.Model):
    __tablename__ = 'download_request'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    knr_id = db.Column(db.Integer, db.ForeignKey('knr.id'), nullable=False)
    requested_by_name = db.Column(db.String(100), nullable=False)  # NEW
    requested_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(50), default='Pending', nullable=False)  # Pending / Approved / Rejected
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    justification = db.Column(db.Text, nullable=True)

    knr = db.relationship('KNR', backref='download_requests', foreign_keys=[knr_id])
    requester = db.relationship('User', foreign_keys=[requested_by])
    approver = db.relationship('User', foreign_keys=[approved_by])