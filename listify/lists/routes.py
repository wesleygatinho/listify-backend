from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from listify import db
from listify.models import ListaDeCompras, ItemDaLista
from . import lists_bp
from marshmallow import ValidationError
from listify.schemas import ListaCreateSchema, ItemDaListaCreateSchema, ItemDaListaUpdateSchema


def _serialize_item(item: ItemDaLista):
    return {
        "id": item.id,
        "descricao_item": item.descricao_item,
        "concluido": bool(item.concluido),
    }


def _serialize_lista(lista: ListaDeCompras, include_itens: bool = True):
    data = {
        "id": lista.id,
        "nome": lista.nome,
        "data_criacao": lista.data_criacao.isoformat() if lista.data_criacao else None,
    }
    if include_itens:
        # lazy=True, então podemos acessar lista.itens
        data["itens"] = [_serialize_item(i) for i in lista.itens]
    return data


@lists_bp.route('', methods=['POST'])
@jwt_required()
def criar_lista():
    try:
        dados = ListaCreateSchema().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "validation_error", "details": err.messages}), 400
    nome = dados['nome']

    user_id = int(get_jwt_identity())
    lista = ListaDeCompras(nome=nome, usuario_id=user_id)
    db.session.add(lista)
    db.session.commit()
    return jsonify(_serialize_lista(lista)), 201


@lists_bp.route('', methods=['GET'])
@jwt_required()
def listar_listas():
    user_id = int(get_jwt_identity())
    listas = ListaDeCompras.query.filter_by(usuario_id=user_id).order_by(ListaDeCompras.data_criacao.desc()).all()
    return jsonify([_serialize_lista(l) for l in listas]), 200


@lists_bp.route('/<int:lista_id>/items', methods=['POST'])
@jwt_required()
def adicionar_item(lista_id: int):
    user_id = int(get_jwt_identity())
    lista = ListaDeCompras.query.get(lista_id)
    if not lista:
        return jsonify({"error": "Lista não encontrada"}), 404
    if lista.usuario_id != user_id:
        return jsonify({"error": "Acesso negado à lista"}), 403

    try:
        dados_raw = request.get_json() or {}
        # aceita alias 'descricao' para conveniência
        if 'descricao_item' not in dados_raw and 'descricao' in dados_raw:
            dados_raw['descricao_item'] = dados_raw['descricao']
        # remover o alias para evitar erro de 'Unknown field' do Marshmallow
        dados_raw.pop('descricao', None)
        dados = ItemDaListaCreateSchema().load(dados_raw)
    except ValidationError as err:
        return jsonify({"error": "validation_error", "details": err.messages}), 400
    descricao = dados['descricao_item']

    item = ItemDaLista(lista_id=lista.id, descricao_item=descricao, concluido=False)
    db.session.add(item)
    db.session.commit()
    return jsonify(_serialize_item(item)), 201


@lists_bp.route('/items/<int:item_id>', methods=['PUT'])
@jwt_required()
def concluir_item(item_id: int):
    user_id = int(get_jwt_identity())
    item = ItemDaLista.query.get(item_id)
    if not item:
        return jsonify({"error": "Item não encontrado"}), 404

    lista = ListaDeCompras.query.get(item.lista_id)
    if not lista:
        return jsonify({"error": "Lista não encontrada"}), 404
    if lista.usuario_id != user_id:
        return jsonify({"error": "Acesso negado à lista"}), 403

    item.concluido = True
    db.session.commit()
    return jsonify(_serialize_item(item)), 200


@lists_bp.route('/items/<int:item_id>', methods=['PATCH'])
@jwt_required()
def atualizar_item(item_id: int):
    """Atualiza propriedades do ItemDaLista. Atualmente suporta 'concluido' booleano."""
    user_id = int(get_jwt_identity())
    item = ItemDaLista.query.get(item_id)
    if not item:
        return jsonify({"error": "Item não encontrado"}), 404

    lista = ListaDeCompras.query.get(item.lista_id)
    if not lista:
        return jsonify({"error": "Lista não encontrada"}), 404
    if lista.usuario_id != user_id:
        return jsonify({"error": "Acesso negado à lista"}), 403

    try:
        dados = ItemDaListaUpdateSchema().load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "validation_error", "details": err.messages}), 400

    item.concluido = bool(dados.get('concluido'))
    db.session.commit()
    return jsonify(_serialize_item(item)), 200


@lists_bp.route('/items/<int:item_id>', methods=['DELETE'])
@jwt_required()
def excluir_item(item_id: int):
    """Exclui um item específico da lista do usuário logado."""
    user_id = int(get_jwt_identity())
    item = ItemDaLista.query.get(item_id)
    if not item:
        return jsonify({"error": "Item não encontrado"}), 404

    lista = ListaDeCompras.query.get(item.lista_id)
    if not lista:
        return jsonify({"error": "Lista não encontrada"}), 404
    if lista.usuario_id != user_id:
        return jsonify({"error": "Acesso negado à lista"}), 403

    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Item excluído"}), 200


@lists_bp.route('/<int:lista_id>', methods=['DELETE'])
@jwt_required()
def excluir_lista(lista_id: int):
    user_id = int(get_jwt_identity())
    lista = ListaDeCompras.query.get(lista_id)
    if not lista:
        return jsonify({"error": "Lista não encontrada"}), 404
    if lista.usuario_id != user_id:
        return jsonify({"error": "Acesso negado à lista"}), 403

    # Remover itens explicitamente para evitar FK issues
    ItemDaLista.query.filter_by(lista_id=lista.id).delete()
    db.session.delete(lista)
    db.session.commit()
    return jsonify({"message": "Lista excluída"}), 200