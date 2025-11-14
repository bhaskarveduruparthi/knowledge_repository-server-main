from marshmallow import Schema, fields
from models.repository_model import KNR

class KNR_Schema(Schema):
    class Meta:
        model = KNR
        ordered = True
        dateformat = '%Y-%m-%d'

    id = fields.Integer()
    customer_name = fields.String(required=True)
    domain = fields.String(required=True)
    sector = fields.String(required=True)
    module_name = fields.String(required=True)
    detailed_requirement = fields.String(required=True)
    standard_custom = fields.String(required=True)
    technical_details = fields.String(required=True)
    customer_benefit = fields.String(required=True)
    remarks = fields.String(required=True)
    attach_code_or_document = fields.String()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    Approver = fields.Str()
    business_justification = fields.Str()
    Approval_status = fields.Str()
    attachment_filename = fields.Str()
    Approval_date = fields.DateTime()
    
knr = KNR_Schema()
knrs = KNR_Schema(many=True)
