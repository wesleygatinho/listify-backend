from flask import jsonify, request
from flask_jwt_extended import jwt_required
from listify import db
from listify.models import Produto
from . import products_bp
from marshmallow import ValidationError
from listify.schemas import ProductSchema


def serialize_produto(prod: Produto):
    return {
        "id": prod.id,
        "codigo_barras": prod.codigo_barras,
        "nome": prod.nome,
        "marca": prod.marca,
    }


@products_bp.route('/barcode/<string:codigo_barras>', methods=['GET'])
@jwt_required()
def buscar_por_codigo_barras(codigo_barras):
    """RF04: Busca produto pelo código de barras."""
    prod = Produto.query.filter_by(codigo_barras=codigo_barras).first()
    if not prod:
        return jsonify({"error": "Produto não encontrado"}), 404
    return jsonify(serialize_produto(prod)), 200


@products_bp.route('', methods=['POST'])
@jwt_required()
def cadastrar_produto():
    """RF05: Cadastra novo produto (RN01: código de barras único)."""
    try:
        dados = ProductSchema().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "validation_error", "details": err.messages}), 400
    codigo_barras = dados['codigo_barras']
    nome = dados['nome']
    marca = dados.get('marca')

    if Produto.query.filter_by(codigo_barras=codigo_barras).first():
        return jsonify({"error": "RN01: código de barras já cadastrado"}), 409

    prod = Produto(codigo_barras=codigo_barras, nome=nome, marca=marca)
    db.session.add(prod)
    db.session.commit()

    return jsonify(serialize_produto(prod)), 201