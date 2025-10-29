from flask import jsonify
from . import auth_bp

@auth_bp.route('/register', methods=['POST'])
def register():
    # A lógica de cadastro (RF01) [cite: 54] virá aqui
    return jsonify({"message": "Esta é a rota de registro"}), 200

@auth_bp.route('/login', methods=['POST'])
def login():
    # A lógica de login (RF02) [cite: 56] virá aqui
    return jsonify({"message": "Esta é a rota de login"}), 200