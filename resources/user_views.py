from flask import request, json, jsonify
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user_model import User
from schemas.user_schema import user,users
from default_settings import db 
import datetime
from blueprints import blp
from extensions.BCRYPT import bcrypt

class User_Requirements(Resource):
    

    #Adding the user to the Database
    @blp.route('/adduser', methods=['POST'])
    @jwt_required()
    def adduser():

        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()

        if check_user.type != 'Superadmin':
            return jsonify("Unauthorized, Not an Super Admin")

        if request.method == 'POST':
            name = request.json['name'],
            email = request.json['email'],
            password = request.json['password']
            yash_id = request.json['yash_id']
            b_unit = request.json['b_unit']
            type = request.json['type']
           
            new_user = User(name=name, email=email, password=password, type=type, active='Y', yash_id=yash_id, b_unit=b_unit)
            new_user.password = bcrypt.generate_password_hash(new_user.password).decode('utf8')
            db.session.add(new_user)
            db.session.commit()
            result = user.dump(new_user)
            return jsonify(result)  
        else:
            return jsonify("User not Authorized")     
    
    #gettting all the users
    @blp.route('/getallusers', methods=['GET'])
    @jwt_required()
    def getallusers():

        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()

        if check_user.type == 'Superadmin':
            
            posts = User.query.all()
            result = users.dump(posts)
            return jsonify(result)
        
        else:
            return jsonify("User not Authorized")
            

    #get current user
    @blp.route('/getuser', methods=['GET'])
    @jwt_required()
    def getuser():

        current_user = get_jwt_identity()

        get_user = User.query.filter_by(yash_id=current_user).first()

        result = user.dump(get_user)
        return jsonify(result)
    
    #Getting user by id from the database 
    @blp.route('/getuser_by_id/<yash_id>', methods=['GET'])
    @jwt_required()
    def getuser_byID(yash_id):

        post = User.query.filter_by(yash_id=yash_id).first()

        if post is None:
            return jsonify("User not found")
        else:
            result = user.dump(post)
            return jsonify(result)
    

    #Edit the user present in the database
    @blp.route('/edituser/<yash_id>', methods=['PUT'])
    @jwt_required()
    def edituser(yash_id):

       
        current_user = get_jwt_identity()
        check_admin = User.query.filter_by(yash_id=current_user).first()

        check_user = User.query.filter_by(yash_id=yash_id).first()

        if check_user is not None and check_admin.type == 'Superadmin':

            if 'name' in request.json:
                check_user.name = request.json['name']
            if 'email' in request.json:
                check_user.email = request.json['email']

            if 'b_unit' in request.json:
                check_user.b_unit = request.json['b_unit']
            if 'active' in request.json:
                check_user.active = request.json['active']    
            db.session.commit()
            result = user.dump(check_user)
            return jsonify(result)
        
    #Delete the user from the database using the id
    @blp.route('/deleteuser/<yash_id>', methods=['DELETE'])
    @jwt_required()
    def delete_user(yash_id):

        current_user = get_jwt_identity()
        check_admin = User.query.filter_by(yash_id=current_user).first()

        if check_admin.type == 'Superadmin':

            getting_user = User.query.filter_by(yash_id=yash_id).first()
            db.session.delete(getting_user)
            db.session.commit()
            return jsonify("User Deleted")
        else:
            return jsonify("Not an Admin")