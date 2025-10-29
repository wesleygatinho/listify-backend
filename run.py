from listify import create_app, db
# Importe todos os seus modelos para que o SQLAlchemy os 'veja'
from listify.models import Usuario, Produto, Compra, ItemDaCompra, ListaDeCompras, ItemDaLista

app = create_app()

@app.shell_context_processor
def make_shell_context():
    """
    Facilita o uso do 'flask shell' ao pré-importar o db e os modelos.
    Isso também ajuda o Flask-Migrate a encontrar os modelos.
    """
    return {
        'db': db,
        'Usuario': Usuario,
        'Produto': Produto,
        'Compra': Compra,
        'ItemDaCompra': ItemDaCompra,
        'ListaDeCompras': ListaDeCompras,
        'ItemDaLista': ItemDaLista
    }

if __name__ == '__main__':
    app.run(debug=True)