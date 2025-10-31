from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from decimal import Decimal
from listify import db
from listify.models import Compra, ItemDaCompra, Produto, Usuario
from . import purchase_bp
from marshmallow import ValidationError
from listify.schemas import ItemDaCompraCreateSchema


def _recalcular_total(compra: Compra) -> Decimal:
    total = Decimal('0.00')
    # Recarrega itens para garantir consistência
    itens = ItemDaCompra.query.filter_by(compra_id=compra.id).all()
    for item in itens:
        # item.preco_pago é Decimal; quantidade é int -> Decimal
        total += (item.preco_pago * item.quantidade)
    compra.valor_total = total
    db.session.commit()
    return total


@purchase_bp.route('/start', methods=['POST'])
@jwt_required()
def iniciar_compra():
    """RF03: Inicia uma compra associada ao usuário autenticado."""
    user_id = int(get_jwt_identity())
    usuario = Usuario.query.get(user_id)
    if not usuario:
        return jsonify({"error": "Usuário não encontrado"}), 404

    compra = Compra(usuario_id=usuario.id, valor_total=Decimal('0.00'))
    db.session.add(compra)
    db.session.commit()

    return jsonify({"compra_id": compra.id, "valor_total": float(compra.valor_total)}), 201


@purchase_bp.route('/<int:compra_id>/add', methods=['POST'])
@jwt_required()
def adicionar_item(compra_id: int):
    """RF06: Adiciona item à compra e recalcula valor_total."""
    user_id = int(get_jwt_identity())
    compra = Compra.query.get(compra_id)
    if not compra:
        return jsonify({"error": "Compra não encontrada"}), 404
    if compra.usuario_id != user_id:
        return jsonify({"error": "Acesso negado à compra"}), 403

    try:
        dados = ItemDaCompraCreateSchema().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "validation_error", "details": err.messages}), 400
    produto_id = dados['produto_id']
    preco_pago = dados['preco_pago']
    quantidade = dados.get('quantidade', 1)

    produto = Produto.query.get(produto_id)
    if not produto:
        return jsonify({"error": "Produto não encontrado"}), 404

    try:
        # preco_pago já é Decimal pelo schema; vamos garantir 2 casas
        preco_val = Decimal(str(preco_pago)).quantize(Decimal('0.01'))
        quantidade = int(quantidade)
        if quantidade <= 0:
            return jsonify({"error": "quantidade deve ser >= 1"}), 400
    except Exception:
        return jsonify({"error": "Dados inválidos para preco_pago/quantidade"}), 400

    item = ItemDaCompra(produto_id=produto.id, compra_id=compra.id, preco_pago=preco_val, quantidade=quantidade)
    db.session.add(item)
    db.session.commit()

    novo_total = _recalcular_total(compra)
    return jsonify({
        "item_id": item.id,
        "valor_total": float(novo_total)
    }), 201


@purchase_bp.route('/item/<int:item_id>', methods=['DELETE'])
@jwt_required()
def remover_item(item_id: int):
    """RF06: Remove item da compra e recalcula valor_total."""
    user_id = int(get_jwt_identity())
    item = ItemDaCompra.query.get(item_id)
    if not item:
        return jsonify({"error": "Item não encontrado"}), 404

    compra = Compra.query.get(item.compra_id)
    if not compra:
        return jsonify({"error": "Compra não encontrada"}), 404
    if compra.usuario_id != user_id:
        return jsonify({"error": "Acesso negado à compra"}), 403

    db.session.delete(item)
    db.session.commit()

    novo_total = _recalcular_total(compra)
    return jsonify({"valor_total": float(novo_total)}), 200


@purchase_bp.route('/<int:compra_id>/finish', methods=['POST'])
@jwt_required()
def finalizar_compra(compra_id: int):
    """RF08/RN05: Finaliza a compra se houver ao menos um item."""
    user_id = int(get_jwt_identity())
    compra = Compra.query.get(compra_id)
    if not compra:
        return jsonify({"error": "Compra não encontrada"}), 404
    if compra.usuario_id != user_id:
        return jsonify({"error": "Acesso negado à compra"}), 403

    # Verifica RN05: pelo menos um item na compra
    itens_count = ItemDaCompra.query.filter_by(compra_id=compra.id).count()
    if itens_count == 0:
        return jsonify({"error": "RN05: compra deve ter ao menos um item"}), 400

    # Marca como finalizada e recalcula total
    compra.finalizada = True
    total = _recalcular_total(compra)
    db.session.commit()
    return jsonify({"message": "Compra finalizada", "valor_total": float(total), "compra_id": compra.id}), 200