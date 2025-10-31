from flask import Blueprint

lists_bp = Blueprint('lists', __name__)

from . import routes