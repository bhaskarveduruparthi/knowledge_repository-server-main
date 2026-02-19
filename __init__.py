from flask import Flask
from routes import Create_routes
from default_settings import Create_Database
from extensions import Create_Extension
from services.email_service import mail
from config import Config


def Create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    mail.init_app(app)          

    Create_Database(app)
    Create_routes(app)
    Create_Extension(app)

    from blueprints import blp, rlp, slp
    app.register_blueprint(blp)
    app.register_blueprint(rlp)
    app.register_blueprint(slp)

    return app


if __name__ == '__main__':
    app = Create_app()
    app.run(debug=True, use_reloader=False)