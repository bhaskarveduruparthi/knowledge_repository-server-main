from default_settings import db

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255),nullable=False)
    description = db.Column(db.Text, nullable=False)
    attachment_data = db.Column(db.LargeBinary(length=65536))
    business_justification = db.Column(db.Text)
    user_created_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_status = db.Column(db.String(100), default="Open")
    username = db.Column(db.String(80), nullable=False)  # Store username here
    answers = db.relationship('Answer', backref='question')
    
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    attachment_data = db.Column(db.LargeBinary(length=65536))
    username = db.Column(db.String(80), nullable=False)
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    user_created_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Add relationship to AnswerVote
    votes = db.relationship('AnswerVote', backref='answer', lazy=True, cascade='all, delete-orphan')


class AnswerVote(db.Model):
    __tablename__ = 'answer_votes'
    
    id = db.Column(db.Integer, primary_key=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)  # Matches your user_created_id pattern
    vote_type = db.Column(db.String(10), nullable=False)  # 'upvote' or 'downvote'
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationship back to Answer (already defined above)
    
    __table_args__ = (
        db.UniqueConstraint('answer_id', 'user_id', name='unique_user_answer_vote'),
    )
