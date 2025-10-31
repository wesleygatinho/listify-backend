from listify import db, bcrypt
import datetime

# Modelo de Usuário [cite: 131]
class Usuario(db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False) # RN02 [cite: 85]
    hash_senha = db.Column(db.String(128), nullable=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Relacionamentos
    compras = db.relationship('Compra', backref='comprador', lazy=True)
    listas_de_compras = db.relationship('ListaDeCompras', backref='criador', lazy=True)

    # Método para hashear a senha (RNF03) [cite: 76]
    def set_password(self, senha):
        self.hash_senha = bcrypt.generate_password_hash(senha).decode('utf-8')

    def check_password(self, senha):
        return bcrypt.check_password_hash(self.hash_senha, senha)

# Modelo de Produto [cite: 132]
class Produto(db.Model):
    __tablename__ = 'produto'
    id = db.Column(db.Integer, primary_key=True)
    codigo_barras = db.Column(db.String(100), unique=True, nullable=False) # RN01 [cite: 83]
    nome = db.Column(db.String(200), nullable=False)
    marca = db.Column(db.String(100))
    data_criacao = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# Modelo de Compra [cite: 133]
class Compra(db.Model):
    __tablename__ = 'compra'
    id = db.Column(db.Integer, primary_key=True)
    data_compra = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    valor_total = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    finalizada = db.Column(db.Boolean, default=False)

    itens = db.relationship('ItemDaCompra', backref='compra_associada', lazy=True)

# Modelo de ItemDaCompra [cite: 134]
class ItemDaCompra(db.Model):
    __tablename__ = 'item_da_compra'
    id = db.Column(db.Integer, primary_key=True)
    preco_pago = db.Column(db.Numeric(10, 2), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=1)
    compra_id = db.Column(db.Integer, db.ForeignKey('compra.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)

    # Relacionamento para acessar os dados do produto facilmente
    produto = db.relationship('Produto')

# Modelo de ListaDeCompras [cite: 135]
class ListaDeCompras(db.Model):
    __tablename__ = 'lista_de_compras'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

    itens = db.relationship('ItemDaLista', backref='lista_associada', lazy=True)

# Modelo de ItemDaLista [cite: 136]
class ItemDaLista(db.Model):
    __tablename__ = 'item_da_lista'
    id = db.Column(db.Integer, primary_key=True)
    descricao_item = db.Column(db.String(300), nullable=False)
    concluido = db.Column(db.Boolean, default=False)
    lista_id = db.Column(db.Integer, db.ForeignKey('lista_de_compras.id'), nullable=False)