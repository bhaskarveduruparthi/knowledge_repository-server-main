from flask import request, json, jsonify, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.repository_model import KNR
from models.user_model import User
from schemas.user_schema import user, users
from schemas.repository_schema import knr, knrs
from default_settings import db
import datetime
from blueprints import blp
from extensions.BCRYPT import bcrypt
from extensions.REDIS import redis
from sqlalchemy import func, case


def get_cached_data(cache_key):
    """
    Safely get data from Redis cache with error handling
    Compatible with Flask-Caching
    """
    try:
        cached = redis.get(cache_key)
        if cached:
            # Flask-Caching may return data already deserialized
            if isinstance(cached, (dict, list)):
                return cached
            if isinstance(cached, str):
                try:
                    return json.loads(cached)
                except (json.JSONDecodeError, ValueError):
                    return cached
            return cached
    except Exception as e:
        current_app.logger.warning(f"Redis GET error for key {cache_key}: {str(e)}")
    return None


def set_cached_data(cache_key, data, timeout=300):
    """
    Safely set data to Redis cache with error handling
    Compatible with Flask-Caching
    Flask-Caching signature: cache.set(key, value, timeout=timeout)
    """
    try:
        # Flask-Caching handles serialization automatically
        redis.set(cache_key, data, timeout=timeout)
    except Exception as e:
        current_app.logger.warning(f"Redis SET error for key {cache_key}: {str(e)}")


def delete_cache_keys(*keys):
    """
    Safely delete multiple cache keys with error handling
    Compatible with Flask-Caching
    """
    try:
        for key in keys:
            redis.delete(key)
    except Exception as e:
        current_app.logger.warning(f"Redis DELETE error: {str(e)}")


def clear_all_user_caches():
    """
    Clear all user-related caches
    """
    cache_keys = [
        'all_users_superadmin',
        'all_users_manager',
        'all_managers_superadmin'
    ]
    delete_cache_keys(*cache_keys)


def clear_user_specific_cache(yash_id):
    """
    Clear cache for a specific user
    """
    cache_key = f'user_{yash_id}'
    delete_cache_keys(cache_key)


class User_Requirements(Resource):

    # Adding the user to the Database
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

            new_user = User(name=name, email=email, password=password, type=type, active='Y', yash_id=yash_id,
                            b_unit=b_unit)
            new_user.password = bcrypt.generate_password_hash(new_user.password).decode('utf8')
            db.session.add(new_user)
            db.session.commit()
            
            # Clear all user caches after adding a new user
            clear_all_user_caches()
            
            result = user.dump(new_user)
            return jsonify(result)
        else:
            return jsonify("User not Authorized")

    # getting all the users
    @blp.route('/getallusers', methods=['GET'])
    @jwt_required()
    def getallusers():

        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()

        if check_user.type == 'Superadmin':
            # Check cache first
            cache_key = 'all_users_superadmin'
            cached = get_cached_data(cache_key)
            if cached:
                return jsonify(cached)

            # If no cache, query database
            posts = User.query.all()
            result = users.dump(posts)
            
            # Store in cache for 5 minutes
            set_cached_data(cache_key, result, timeout=300)
            return jsonify(result)
            
        elif check_user.type == 'manager':
            # Check cache first
            cache_key = 'all_users_manager'
            cached = get_cached_data(cache_key)
            if cached:
                return jsonify(cached)

            # If no cache, query database
            posts = User.query.filter_by(type='user').all()
            result = users.dump(posts)
            
            # Store in cache for 5 minutes
            set_cached_data(cache_key, result, timeout=300)
            return jsonify(result)
        else:
            return jsonify("User not Authorized")

    @blp.route('/getallmanagers', methods=['GET'])
    @jwt_required()
    def getallmanagers():

        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()

        if check_user.type == 'Superadmin':
            # Check cache first
            cache_key = 'all_managers_superadmin'
            cached = get_cached_data(cache_key)
            if cached:
                return jsonify(cached)

            # If no cache, query database
            posts = User.query.filter_by(type='manager').all()
            result = users.dump(posts)
            
            # Store in cache for 5 minutes
            set_cached_data(cache_key, result, timeout=300)
            return jsonify(result)

        else:
            return jsonify("User not Authorized")

    # get current user
    @blp.route('/getuser', methods=['GET'])
    @jwt_required()
    def getuser():

        current_user = get_jwt_identity()

        # Check cache first
        cache_key = f'user_{current_user}'
        cached = get_cached_data(cache_key)
        if cached:
            return jsonify(cached)

        # If no cache, query database
        get_user = User.query.filter_by(yash_id=current_user).first()
        result = user.dump(get_user)
        
        # Store in cache for 5 minutes
        set_cached_data(cache_key, result, timeout=300)
        return jsonify(result)

    # Getting user by id from the database
    @blp.route('/getuser_by_id/<yash_id>', methods=['GET'])
    @jwt_required()
    def getuser_byID(yash_id):

        # Check cache first
        cache_key = f'user_{yash_id}'
        cached = get_cached_data(cache_key)
        if cached:
            return jsonify(cached)

        # If no cache, query database
        post = User.query.filter_by(yash_id=yash_id).first()

        if post is None:
            return jsonify("User not found")
        else:
            result = user.dump(post)
            
            # Store in cache for 5 minutes
            set_cached_data(cache_key, result, timeout=300)
            return jsonify(result)

    # Edit the user present in the database
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
            
            # Clear all user caches and specific user cache
            clear_all_user_caches()
            clear_user_specific_cache(yash_id)
            
            result = user.dump(check_user)
            return jsonify(result)

    # Delete the user from the database using the id
    @blp.route('/deleteuser/<yash_id>', methods=['DELETE'])
    @jwt_required()
    def delete_user(yash_id):

        current_user = get_jwt_identity()
        check_admin = User.query.filter_by(yash_id=current_user).first()

        if check_admin.type == 'Superadmin':

            getting_user = User.query.filter_by(yash_id=yash_id).first()
            db.session.delete(getting_user)
            db.session.commit()
            
            # Clear all user caches and specific user cache
            clear_all_user_caches()
            clear_user_specific_cache(yash_id)
            
            return jsonify("User Deleted")
        else:
            return jsonify("Not an Admin")