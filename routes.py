from resources.repository_views import KNR_Requirements
from resources.support_views import Support
from resources.user_login import User_auth

from flask_restful import Api

from resources.user_views import User_Requirements

def Create_routes(app):

    api = Api(app)

    api.add_resource(User_auth, '/users', methods=['GET','POST'])
    api.add_resource(Support, '/support', methods=['GET', 'POST'] )
    api.add_resource(User_Requirements, '/users', methods=['GET','POST', 'PUT', 'DELETE'])
    api.add_resource(KNR_Requirements, '/repos', methods=['GET','POST', 'PUT', 'DELETE'])
    return api.init_app(app)