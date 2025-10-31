from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from config import Config
from flask_cors import CORS
import logging

# Instancia as extensões (sem app ainda)
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
jwt = JWTManager()

def create_app(config_class=Config):
    """
    Padrão Application Factory
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializa as extensões com a app
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Configurar CORS
    CORS(
        app,
        resources={r"/*": {"origins": app.config.get("CORS_ORIGINS", "*")}},
        supports_credentials=app.config.get("CORS_SUPPORTS_CREDENTIALS", True),
    )

    # Logger básico
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("listify")

    # --- Registrar Blueprints ---

    # Exemplo com o Blueprint de Autenticação
    from listify.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Blueprint de Produtos
    from listify.products import products_bp
    app.register_blueprint(products_bp, url_prefix='/products')

    # Blueprint de Compras
    from listify.purchase import purchase_bp
    app.register_blueprint(purchase_bp, url_prefix='/purchase')

    # Blueprints de Listas e Histórico
    from listify.lists import lists_bp
    app.register_blueprint(lists_bp, url_prefix='/lists')

    from listify.history import history_bp
    app.register_blueprint(history_bp, url_prefix='/history')

    # Uma rota simples para verificar se a API está no ar
    @app.route('/health')
    def health_check():
        return jsonify({"status": "healthy"}), 200

    # --- Handlers Globais de Erros JSON ---
    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({"error": "not_found", "message": "Rota ou recurso não encontrado"}), 404

    @app.errorhandler(405)
    def handle_405(e):
        return jsonify({"error": "method_not_allowed", "message": "Método HTTP não permitido para esta rota"}), 405

    @app.errorhandler(401)
    def handle_401(e):
        return jsonify({"error": "unauthorized", "message": "Não autorizado"}), 401

    @app.errorhandler(403)
    def handle_403(e):
        return jsonify({"error": "forbidden", "message": "Acesso negado"}), 403

    @app.errorhandler(500)
    def handle_500(e):
        logger.exception("Erro interno do servidor")
        return jsonify({"error": "internal_server_error", "message": "Erro interno do servidor"}), 500

    # --- Handlers de Erros do JWT ---
    @jwt.unauthorized_loader
    def jwt_unauthorized_loader(err_str):
        return jsonify({"error": "jwt_unauthorized", "message": err_str}), 401

    @jwt.invalid_token_loader
    def jwt_invalid_token_loader(err_str):
        return jsonify({"error": "jwt_invalid_token", "message": err_str}), 401

    @jwt.expired_token_loader
    def jwt_expired_token_loader(jwt_header, jwt_payload):
        return jsonify({"error": "jwt_expired", "message": "Token JWT expirado"}), 401

    @jwt.revoked_token_loader
    def jwt_revoked_token_loader(jwt_header, jwt_payload):
        return jsonify({"error": "jwt_revoked", "message": "Token JWT revogado"}), 401

    return app