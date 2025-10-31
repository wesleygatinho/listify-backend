from marshmallow import Schema, fields, validate, ValidationError

# --- Auth Schemas ---
class RegisterSchema(Schema):
    nome = fields.Str(required=True, validate=validate.Length(min=2))
    email = fields.Email(required=True)
    senha = fields.Str(required=True, validate=validate.Length(min=8))

class LoginSchema(Schema):
    email = fields.Email(required=True)
    senha = fields.Str(required=True)

class GoogleLoginSchema(Schema):
    id_token = fields.Str(required=True)

# --- Product Schemas ---
class ProductSchema(Schema):
    codigo_barras = fields.Str(required=True, validate=validate.Length(min=1))
    nome = fields.Str(required=True, validate=validate.Length(min=1))
    marca = fields.Str(allow_none=True)

# --- List Schemas ---
class ListaCreateSchema(Schema):
    nome = fields.Str(required=True, validate=validate.Length(min=1))

class ItemDaListaCreateSchema(Schema):
    descricao_item = fields.Str(required=True, validate=validate.Length(min=1))

class ItemDaListaUpdateSchema(Schema):
    # Atualiza o estado de conclusão do item
    concluido = fields.Boolean(required=True)

# --- Purchase Schemas ---
class ItemDaCompraCreateSchema(Schema):
    produto_id = fields.Int(required=True, strict=True)
    preco_pago = fields.Decimal(required=True, places=2)
    quantidade = fields.Int(required=False, load_default=1, validate=validate.Range(min=1))