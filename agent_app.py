from flask import Flask

from flask_jwt_extended import JWTManager

from flask_cors import CORS

import secrets

from default_settings import db

from agent.routes import AgentReport, AgentReportExport, AgentSearch, AgentChat, AgentDocument, AgentSummarize

from flask_restful import Api

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Saibhaskar9@LocalHost:3306/knwldg_repository'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config["JWT_TOKEN_LOCATION"] = ["headers", "query_string"]

app.config["JWT_QUERY_STRING_NAME"] = "access_token"

app.config['JSON_SORT_KEYS'] = False

app.config['JWT_SECRET_KEY'] = 'jwt-secret'   # MUST match default_settings.py exactly

app.config['SECRET_KEY'] = secrets.token_urlsafe(16)

db.init_app(app)

jwt = JWTManager(app)

CORS(app)   # matches your main app's wide-open CORS() default exactly

api = Api(app)

api.add_resource(AgentSearch, '/agent/search', methods=['POST'])

api.add_resource(AgentChat, '/agent/chat', methods=['POST'])

api.add_resource(AgentDocument, '/agent/document/<int:doc_id>', methods=['GET'])

api.add_resource(AgentSummarize, '/agent/document/<int:doc_id>/summarize', methods=['POST'])

api.add_resource(AgentReport, '/agent/report', methods=['POST'])
api.add_resource(AgentReportExport, '/agent/report/export', methods=['POST'])

gunicorn_app = app

if __name__ == '__main__':

    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5004)
 