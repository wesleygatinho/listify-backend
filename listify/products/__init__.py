from flask import Blueprint

# 'products' é o nome do blueprint de produtos
products_bp = Blueprint('products', __name__)

# Importa as rotas para registrar no blueprint
from . import routes