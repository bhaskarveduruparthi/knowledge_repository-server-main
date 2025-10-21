from default_settings import db 




class User(db.Model):

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    yash_id = db.Column(db.String(length=10), unique=True, nullable=False)
    name = db.Column(db.String(length=100), nullable=False)
    email = db.Column(db.String(length=200), unique=True, nullable=False)
    b_unit = db.Column(db.String(length=40), nullable=False)
    active = db.Column(db.String(length=1), default='Y',  nullable=False)
    type = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(length=100), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    kn_repository = db.relationship('KNR', backref='user')
    


    def  __init__(self,name, email, password, type, active, b_unit, yash_id):

       
        self.email = email,
        self.name = name,
        self.password = password
        self.type = type
        self.active = active
        self.b_unit = b_unit
        self.yash_id = yash_id