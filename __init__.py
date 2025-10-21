from flask import Flask
from routes import Create_routes
from default_settings import Create_Database
from extensions import Create_Extension

def Create_app():

    app = Flask(__name__)

    
    Create_Database(app)
    Create_routes(app)
    Create_Extension(app)

    from blueprints import blp, rlp
    app.register_blueprint(blp)
    app.register_blueprint(rlp)
    

    return app

