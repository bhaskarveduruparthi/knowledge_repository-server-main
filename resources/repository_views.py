from flask import request, json, jsonify
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user_model import User
from models.repository_model import KNR
from schemas.repository_schema import knr,knrs
from schemas.user_schema import user,users
from default_settings import db 
import datetime
from blueprints import rlp

class KNR_Requirements(Resource):
    

    #Getting all the forms in the Database
    @rlp.route('/getallreporecords', methods=['GET'])
    @jwt_required()
    def getallrepos():

        current_user = get_jwt_identity()
        check_user = User.query.filter_by(yash_id=current_user).first()

        if check_user is not None and check_user.type == 'admin':
        
            get_repos = KNR.query.all()
            result = knrs.dump(get_repos)
            return jsonify(result)
        else:
            return jsonify("Not Authorized")