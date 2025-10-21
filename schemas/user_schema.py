from marshmallow import Schema , fields
from models.user_model import User

class User_Schema(Schema):
    class Meta:
        model = User
        ordered = True
        dateformat = '%Y-%m-%d'
        exclude = ("password",  )

    id = fields.Integer()
    name = fields.String(required=True)
    password = fields.String(required=True)
    email = fields.String()
    type = fields.String(required=True)
    b_unit = fields.String(required=True)
    active = fields.String()
    yash_id = fields.Integer(required=True)


user = User_Schema()
users = User_Schema(many=True)