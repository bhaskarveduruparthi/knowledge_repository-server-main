from flask import request, json, jsonify
from flask_jwt_extended import create_access_token
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user_model import User, LoginLog
from schemas.user_schema import user
from default_settings import db 
import datetime
from blueprints import blp
from extensions.BCRYPT import bcrypt

class User_auth(Resource):
    
    #Login Authentication for the user who is present in the Database
    @blp.route('/login', methods=['POST'])
    def login_user():
        data = request.get_json()
        yash_id = data['yash_id']
        password = data['password']

        post = User.query.filter_by(yash_id=yash_id).first()

        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')

        expires = datetime.timedelta(minutes=60)

        if post and bcrypt.check_password_hash(post.password, password):
            access_token = create_access_token(identity=yash_id, expires_delta=expires)
            log = LoginLog(
                yash_id=yash_id,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True,
                message="Login successful"
            )
            db.session.add(log)
            db.session.commit()
            return jsonify({'access_token': access_token})
        else:
            log = LoginLog(
                yash_id=yash_id,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                message="Invalid credentials"
            )
            db.session.add(log)
            db.session.commit()
            return jsonify({'message': 'Invalid credentials'}), 401



    #Creating an Admin who can add users and access the user requirements
    @blp.route('/create_admin', methods=['POST'])
    def create_admin(): 
            name = request.json['name']
            email = request.json['email']
            password = request.json['password']
            yash_id = request.json['yash_id']
            b_unit = request.json['b_unit']
            active = request.json['active']

            admin_user = User(name=name, email=email, password=password, type='admin', active=active, yash_id=yash_id, b_unit=b_unit)
            admin_user.password = bcrypt.generate_password_hash(admin_user.password).decode('utf8')
            db.session.add(admin_user)
            db.session.commit()
            return jsonify("Admin Created Successfully")
        
    @blp.route('/changepassword', methods=['POST'])
    @jwt_required()
    def change_password():
        
        current_user = get_jwt_identity()

        check_user = User.query.filter_by(yash_id=current_user).first()



        if check_user is not None:

            data = request.get_json()
            old_password = data.get('old_password')
            new_password = data.get('new_password')


           
            if bcrypt.check_password_hash(check_user.password, old_password):

                hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
                check_user.password = hashed_password
                db.session.commit()

                return jsonify("Password changed")
            
            else:
                return jsonify("Missing Credentials"),500
         
        else:
            return jsonify("User not found"),400


