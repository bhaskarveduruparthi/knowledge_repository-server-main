from flask import Flask
from routes import Create_routes
from default_settings import Create_Database
from extensions import Create_Extension
from config import Config


def Create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
          

    Create_Database(app)
    Create_routes(app)
    Create_Extension(app)

    from blueprints import blp, rlp, slp, agent_bp
    app.register_blueprint(blp)
    app.register_blueprint(rlp)
    app.register_blueprint(slp)
    app.register_blueprint(agent_bp)

    return app


if __name__ == '__main__':
    app = Create_app()
    app.run(debug=True, use_reloader=False)