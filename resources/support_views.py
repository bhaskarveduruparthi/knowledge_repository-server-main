from flask import request, json, jsonify
from flask_jwt_extended import create_access_token
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.user_model import User, LoginLog
from models.support_model import AnswerVote, Question, Answer
from schemas.user_schema import user
from schemas.support_schema import questions
from default_settings import db 
import datetime
from datetime import datetime
from blueprints import slp
from sqlalchemy import func,extract
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
    @jwt_required()
    def upvote_answer(answer_id):
        user_id = get_jwt_identity()  # Your auth function to get current user ID
        
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        answer = Answer.query.filter_by(id=answer_id).first()
        if not answer:
            return jsonify({'error': 'Answer not found'}), 404
        
        # Check if user already voted on this answer
        existing_vote = AnswerVote.query.filter_by(answer_id=answer_id, user_id=user_id).first()
        
        if existing_vote:
            if existing_vote.vote_type == 'upvote':
                return jsonify({'message': 'User already upvoted this answer'}), 400
            else:  # User had downvoted, switch to upvote
                existing_vote.vote_type = 'upvote'
                answer.downvotes = max(0, answer.downvotes - 1)  # Remove downvote
                answer.upvotes += 1  # Add upvote
                db.session.commit()
                return jsonify({
                    'message': 'Switched vote to upvote', 
                    'upvotes': answer.upvotes,
                    'downvotes': answer.downvotes
                })
        
        # No prior vote, create new upvote
        new_vote = AnswerVote(
            answer_id=answer_id, 
            user_id=user_id, 
            vote_type='upvote'
        )
        db.session.add(new_vote)
        answer.upvotes += 1
        db.session.commit()
        
        return jsonify({
            'message': 'Answer upvoted', 
            'upvotes': answer.upvotes,
            'downvotes': answer.downvotes
        })

    @slp.route('/downvote/<int:answer_id>', methods=['POST'])
    @jwt_required()
    def downvote_answer(answer_id):
        user_id = get_jwt_identity()  # Your auth function to get current user ID
        
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        answer = Answer.query.filter_by(id=answer_id).first()
        if not answer:
            return jsonify({'error': 'Answer not found'}), 404
        
        # Check if user already voted on this answer
        existing_vote = AnswerVote.query.filter_by(answer_id=answer_id, user_id=user_id).first()
        
        if existing_vote:
            if existing_vote.vote_type == 'downvote':
                return jsonify({'message': 'User already downvoted this answer'}), 400
            else:  # User had upvoted, switch to downvote
                existing_vote.vote_type = 'downvote'
                answer.upvotes = max(0, answer.upvotes - 1)  # Remove upvote
                answer.downvotes += 1  # Add downvote
                db.session.commit()
                return jsonify({
                    'message': 'Switched vote to downvote', 
                    'upvotes': answer.upvotes,
                    'downvotes': answer.downvotes
                })
        
        # No prior vote, create new downvote
        new_vote = AnswerVote(
            answer_id=answer_id, 
            user_id=user_id, 
            vote_type='downvote'
        )
        db.session.add(new_vote)
        answer.downvotes += 1
        db.session.commit()
        
        return jsonify({
            'message': 'Answer downvoted', 
            'upvotes': answer.upvotes,
            'downvotes': answer.downvotes
        })



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

    @slp.route('/top-users-votes', methods=['GET'])
    def top_users_votes():
        user_type = request.args.get('user_type')
        period    = request.args.get('period')   # ← add this

        now = datetime.utcnow()

        query = db.session.query(
            Answer.username,
            func.count(Answer.id).label('answer_count'),
            func.sum(Answer.upvotes - Answer.downvotes).label('net_votes')
        )

        if user_type:
            query = query.join(User, User.name == Answer.username).filter(User.type == user_type)

        # ← add period filter
        if period == 'monthly':
            query = query.filter(
                extract('year',  Answer.created_at) == now.year,
                extract('month', Answer.created_at) == now.month
            )
        elif period == 'quarterly':
            current_quarter_start_month = ((now.month - 1) // 3) * 3 + 1
            query = query.filter(
                extract('year',  Answer.created_at) == now.year,
                extract('month', Answer.created_at) >= current_quarter_start_month,
                extract('month', Answer.created_at) <  current_quarter_start_month + 3
            )
        elif period == 'yearly':
            query = query.filter(
                extract('year', Answer.created_at) == now.year
            )

        top_users = (
            query
            .group_by(Answer.username)
            .order_by(func.sum(Answer.upvotes - Answer.downvotes).desc())
            .limit(10)
            .all()
        )

        labels = [u.username for u in top_users]
        data   = [int(u.net_votes or 0) for u in top_users]

        return jsonify({
            'labels': labels,
            'datasets': [{
                'label': 'Votes',
                'data': data,
                'backgroundColor': ['#3e95cd', '#8e5ea2', '#3cba9f', '#e8c3b9', '#c45850',
                                    '#36a2eb', '#ff6384', '#ffcd56', '#4bc0c0', '#9966ff']
            }]
        })
    
