from flask import Blueprint

purchase_bp = Blueprint('purchase', __name__)

from . import routes