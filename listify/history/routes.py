from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from listify.models import Compra, ItemDaCompra, Produto
from . import history_bp
from listify.services import comparar_compras


def _serialize_produto(prod: Produto):
    return {
        "id": prod.id,
        "codigo_barras": prod.codigo_barras,
        "nome": prod.nome,
        "marca": prod.marca,
    }


def _serialize_item(item: ItemDaCompra):
    return {
        "id": item.id,
        "quantidade": item.quantidade,
        "preco_pago": float(item.preco_pago),
        "produto": _serialize_produto(item.produto) if item.produto else None,
    }


def _serialize_compra(compra: Compra, include_itens: bool = False):
    data = {
        "id": compra.id,
        "data_compra": compra.data_compra.isoformat() if compra.data_compra else None,
        "valor_total": float(compra.valor_total),
        "finalizada": bool(compra.finalizada),
    }
    if include_itens:
        itens = ItemDaCompra.query.filter_by(compra_id=compra.id).all()
        data["itens"] = [_serialize_item(i) for i in itens]
    return data


@history_bp.route('', methods=['GET'])
@jwt_required()
def listar_historico():
    user_id = int(get_jwt_identity())
    compras = Compra.query\
        .filter_by(usuario_id=user_id)\
        .filter(Compra.finalizada.is_(True))\
        .order_by(Compra.data_compra.desc())\
        .all()
    return jsonify([_serialize_compra(c, include_itens=False) for c in compras]), 200


@history_bp.route('/<int:compra_id>', methods=['GET'])
@jwt_required()
def detalhar_compra(compra_id: int):
    user_id = int(get_jwt_identity())
    compra = Compra.query.get(compra_id)
    if not compra:
        return jsonify({"error": "Compra não encontrada"}), 404
    if compra.usuario_id != user_id:
        return jsonify({"error": "Acesso negado à compra"}), 403
    if not compra.finalizada:
        return jsonify({"error": "Compra não está finalizada"}), 400

    return jsonify(_serialize_compra(compra, include_itens=True)), 200


@history_bp.route('/compare', methods=['GET'])
@jwt_required()
def comparar():
    """RF10: Compara duas compras finalizadas do usuário logado."""
    user_id = int(get_jwt_identity())
    a = request.args.get('a')
    b = request.args.get('b')
    if not a or not b:
        return jsonify({"error": "Parâmetros 'a' e 'b' são obrigatórios"}), 400
    try:
        ida = int(a)
        idb = int(b)
    except ValueError:
        return jsonify({"error": "Parâmetros 'a' e 'b' devem ser inteiros"}), 400
    if ida == idb:
        return jsonify({"error": "Parâmetros 'a' e 'b' devem ser diferentes"}), 400

    compra_a = Compra.query.get(ida)
    compra_b = Compra.query.get(idb)
    if not compra_a or not compra_b:
        return jsonify({"error": "Compra não encontrada"}), 404
    if compra_a.usuario_id != user_id or compra_b.usuario_id != user_id:
        return jsonify({"error": "Acesso negado às compras informadas"}), 403
    if not compra_a.finalizada or not compra_b.finalizada:
        return jsonify({"error": "Apenas compras finalizadas podem ser comparadas"}), 400

    relatorio = comparar_compras(compra_a, compra_b)
    return jsonify(relatorio), 200