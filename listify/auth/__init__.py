from flask import Blueprint

# 'auth' é o nome do blueprint
auth_bp = Blueprint('auth', __name__)

# Importamos as rotas no final para evitar importação circular
from . import routes