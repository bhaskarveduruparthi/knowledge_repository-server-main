from marshmallow import Schema , fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models.support_model import Question, Answer



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






question = Question_Schema()
questions = Question_Schema(many=True)   

answer = AnswerSchema()
answers = AnswerSchema(many=True)
