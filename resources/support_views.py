from flask import request, json, jsonify
from flask_jwt_extended import create_access_token
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user_model import User, LoginLog
from models.support_model import Question, Answer
from schemas.user_schema import user
from schemas.support_schema import questions
from default_settings import db 
import datetime
from blueprints import slp
from sqlalchemy.orm import joinedload
from extensions.BCRYPT import bcrypt


def get_username(user_id):
        user = User.query.get(user_id)
        return user.name if user else 'Unknown'

class Support(Resource):
    
    @slp.route('/getquestions', methods=['GET'])
    def get_all_questions():
        all_questions = Question.query.options(db.joinedload(Question.answers)).all()
        result = questions.dump(all_questions)
        print("Serialized questions data:", result) 
        return jsonify(result)

    @slp.route('/createquestion', methods=['POST'])
    def create_question():
        data = request.json
        if not data or 'description' not in data or 'user_created_id' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
        username = get_username(data['user_created_id'])
        question = Question(
            question=data['question'],
            description=data['description'],
            username = username,
            business_justification=data.get('business_justification'),
            user_created_id=data['user_created_id']
        )
        db.session.add(question)
        db.session.commit()
        return jsonify({'message': 'Question created', 'question_id': question.id}), 201

    @slp.route('/upvote/<int:answer_id>', methods=['POST'])
    def upvote_answer(answer_id):
        answer = Answer.query.filter_by(id=answer_id).first()

        answer.upvotes = (answer.upvotes or 0) + 1
        db.session.commit()
        return jsonify({'message': 'Answer upvoted', 'upvotes': answer.upvotes})


    @slp.route('/downvote/<int:answer_id>', methods=['POST'])
    def downvote_answer(answer_id):
        answer = Answer.query.filter_by(id=answer_id).first()
        answer.downvotes = (answer.downvotes or 0) + 1
        db.session.commit()
        return jsonify({'message': 'Answer downvoted', 'downvotes': answer.downvotes})

    @slp.route('/createanswer', methods=['POST'])
    def create_answer():
        data = request.json
        if not data or 'description' not in data or 'user_created_id' not in data or 'question_id' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        username = get_username(data['user_created_id'])
        answer = Answer(
            description=data['description'],
            username=username,
            upvotes=data.get('upvotes', 0),
            downvotes=data.get('downvotes', 0),
            user_created_id=data['user_created_id'],
            question_id=data['question_id']
        )
        db.session.add(answer)
        db.session.commit()
        return jsonify({'message': 'Answer created', 'answer_id': answer.id}), 201

    