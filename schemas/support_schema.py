from marshmallow import Schema , fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models.repository_model import DownloadLog
from models.support_model import Question, Answer
from models.user_model import LoginLog



class AnswerSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Answer
        include_relationships = True
        load_instance = True


class Question_Schema(SQLAlchemyAutoSchema):
    
    answers = fields.Nested(AnswerSchema, many=True)

    class Meta:
        model = Question
        include_relationships = True
        load_instance = True




class DownloadLogSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = DownloadLog
        load_instance = True

# Usage example
download_log = DownloadLogSchema()
download_logs = DownloadLogSchema(many=True)



class LoginLogSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = LoginLog
        load_instance = True

# Usage example
login_log = LoginLogSchema()
login_logs = LoginLogSchema(many=True)



question = Question_Schema()
questions = Question_Schema(many=True)   

answer = AnswerSchema()
answers = AnswerSchema(many=True)
