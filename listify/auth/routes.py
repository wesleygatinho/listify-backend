from flask import jsonify, request
from . import auth_bp
from listify import db
from listify.models import Usuario
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import re
import requests
import uuid
from marshmallow import ValidationError
from listify.schemas import RegisterSchema, LoginSchema, GoogleLoginSchema


def senha_forte(senha: str) -> bool:
    """RN03: mínimo 8 caracteres, com maiúscula, minúscula e número."""
    if not senha or len(senha) < 8:
        return False
    tem_maiuscula = re.search(r"[A-Z]", senha)
    tem_minuscula = re.search(r"[a-z]", senha)
    tem_numero = re.search(r"\d", senha)
    return all([tem_maiuscula, tem_minuscula, tem_numero])


@auth_bp.route('/register', methods=['POST'])
def register():
    """RF01: Cadastro de usuário com validação de senha e e-mail único."""
    try:
        dados = RegisterSchema().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "validation_error", "details": err.messages}), 400
    nome = dados['nome']
    email = dados['email']
    senha = dados['senha']

    if not senha_forte(senha):
        return jsonify({
            "error": "RN03: senha deve ter pelo menos 8 caracteres, incluir maiúscula, minúscula e número"
        }), 400

    # RN02: e-mail já cadastrado
    if Usuario.query.filter_by(email=email).first():
        return jsonify({"error": "RN02: e-mail já cadastrado"}), 409

    usuario = Usuario(nome=nome, email=email)
    usuario.set_password(senha)  # RNF03: Bcrypt

    db.session.add(usuario)
    db.session.commit()

    return jsonify({
        "message": "Usuário cadastrado com sucesso",
        "usuario": {"id": usuario.id, "nome": usuario.nome, "email": usuario.email}
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """RF02: Login com verificação de senha e emissão de JWT."""
    try:
        dados = LoginSchema().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "validation_error", "details": err.messages}), 400
    email = dados['email']
    senha = dados['senha']

    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario or not usuario.check_password(senha):
        return jsonify({"error": "Credenciais inválidas"}), 401

    access_token = create_access_token(identity=str(usuario.id))
    return jsonify({
        "access_token": access_token,
        "usuario": {"id": usuario.id, "nome": usuario.nome, "email": usuario.email}
    }), 200


@auth_bp.route('/google', methods=['POST'])
def login_google():
    """RF01 (Google): Login com Google simplificado via tokeninfo API."""
    # Aceita 'id_token' diretamente ou 'token' como alias
    dados_raw = request.get_json() or {}
    if 'id_token' not in dados_raw and 'token' in dados_raw:
        dados_raw['id_token'] = dados_raw['token']
    try:
        dados = GoogleLoginSchema().load(dados_raw)
    except ValidationError as err:
        return jsonify({"error": "validation_error", "details": err.messages}), 400
    id_token = dados['id_token']

    try:
        resp = requests.get(
            'https://oauth2.googleapis.com/tokeninfo', params={'id_token': id_token}, timeout=5
        )
        if resp.status_code != 200:
            return jsonify({"error": "Token do Google inválido"}), 401

        info = resp.json()
        email = info.get('email')
        email_verified = info.get('email_verified')
        nome_google = info.get('name') or 'Usuário Google'

        if not email:
            return jsonify({"error": "Token do Google sem e-mail"}), 400

        if str(email_verified).lower() not in ('true', '1'):
            return jsonify({"error": "E-mail do Google não verificado"}), 401

        usuario = Usuario.query.filter_by(email=email).first()
        if not usuario:
            usuario = Usuario(nome=nome_google, email=email)
            # Cria uma senha aleatória apenas para cumprir o modelo; não será usada.
            senha_fake = uuid.uuid4().hex + 'Aa1'
            usuario.set_password(senha_fake)
            db.session.add(usuario)
            db.session.commit()

        access_token = create_access_token(identity=str(usuario.id))
        return jsonify({
            "access_token": access_token,
            "usuario": {"id": usuario.id, "nome": usuario.nome, "email": usuario.email}
        }), 200
    except Exception:
        return jsonify({"error": "Falha ao validar token do Google"}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    """Exemplo de rota protegida usando @jwt_required()."""
    user_id = get_jwt_identity()
    usuario = Usuario.query.get(int(user_id))
    if not usuario:
        return jsonify({"error": "Usuário não encontrado"}), 404
    return jsonify({"id": usuario.id, "nome": usuario.nome, "email": usuario.email}), 200