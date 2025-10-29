from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from config import Config

# Instancia as extensões (sem app ainda)
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()

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

    # --- Registrar Blueprints ---

    # Exemplo com o Blueprint de Autenticação
    from listify.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # (Você fará o mesmo para 'purchase', 'lists', 'history', 'products')

    # Uma rota simples para verificar se a API está no ar
    @app.route('/health')
    def health_check():
        return jsonify({"status": "healthy"}), 200

    return app