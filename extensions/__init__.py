from extensions import JWT, CORS, CSRF, BCRYPT, MAIL
from flask_restful import Api

def Create_Extension(app):

    new_api = Api(app)

    for extensions in (
        CSRF,
        JWT,
        CORS,
        BCRYPT,
        MAIL
      
       
    ):
        extensions.init_app(app)
    
    return new_api