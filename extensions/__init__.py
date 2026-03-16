from extensions import JWT, CORS, CSRF, BCRYPT,REDIS
from flask_restful import Api

def Create_Extension(app):

    new_api = Api(app)

    for extensions in (
        CSRF,
        JWT,
        CORS,
        BCRYPT,
        REDIS
      
       
    ):
        extensions.init_app(app)
    
    return new_api