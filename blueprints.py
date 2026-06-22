from flask import Blueprint

blp = Blueprint('users', __name__, url_prefix='/users')

rlp = Blueprint('repo', __name__, url_prefix='/repos')

slp = Blueprint('support', __name__, url_prefix='/support')

agent_bp = Blueprint('agent', __name__, url_prefix='/api/agent')

