# Listify Backend

API backend do sistema Listify para controle de gastos em supermercado, com autenticação JWT, módulos de Produtos, Compras, Listas e Histórico, comparação de compras e validação de entradas com Marshmallow.

## Sumário

- Visão Geral
- Requisitos
- Instalação
- Configuração (.env)
- Banco de Dados e Migrações
- Execução (Desenvolvimento e Produção)
- CORS
- Autenticação e Autorização
- Endpoints Principais
- Validação e Tratamento de Erros
- Testes rápidos (curl)
- Notas e Limitações

## Visão Geral

- Framework: Flask (Application Factory)
- Banco: PostgreSQL (SQLAlchemy + Alembic/Flask-Migrate)
- Segurança: Flask-JWT-Extended (JWT), Bcrypt
- Validação: Marshmallow
- CORS: Flask-CORS
- Produção: Gunicorn (Linux/WSL/Docker)

Estrutura relevante:

```
listify-backend/
├── config.py               # Configurações centrais do app
├── listify/
│   ├── __init__.py         # Factory da aplicação, registro de blueprints, CORS e handlers
│   ├── models.py           # Modelos SQLAlchemy
│   ├── schemas.py          # Schemas Marshmallow
│   ├── services.py         # Serviços (ex.: comparação de compras)
│   ├── auth/               # Autenticação e JWT
│   ├── products/           # Produtos
│   ├── purchase/           # Compras
│   ├── lists/              # Listas de compras
│   └── history/            # Histórico e comparação
├── migrations/             # Migrações Alembic
├── requirements.txt        # Dependências
└── run.py                  # Entrada do app (dev), expõe `app`
```

## Requisitos

- Python 3.11+ (recomendado)
- PostgreSQL 13+ em execução
- PowerShell (Windows) ou bash (Linux/WSL/macOS)
- Virtualenv (recomendado)

## Instalação

1. Clone o repositório:

```bash
cd listify-backend
```

2. Crie e ative um virtualenv:

```bash
# Windows (PowerShell)
python -m venv venv
venv\Scripts\activate

# Linux/macOS/WSL
python3 -m venv venv
source venv/bin/activate
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

## Configuração (.env)

Crie um arquivo `.env` na raiz com as variáveis:

```env
SECRET_KEY=troque-por-um-segredo-forte
JWT_SECRET_KEY=troque-por-um-segredo-jwt
DATABASE_URL=postgresql://usuario:senha@localhost:5432/listify_db
CORS_ORIGINS=http://localhost:3000
```

- `DATABASE_URL`: string de conexão do PostgreSQL.
- `CORS_ORIGINS`: origem(s) permitidas para o frontend. Aceita múltiplas separadas por vírgula.

## Banco de Dados e Migrações

1. Crie o banco de dados no PostgreSQL (exemplo):

```bash
# terminal psql
psql -U postgres
CREATE DATABASE listify_db;
\q
```

2. Aplique as migrações existentes:

```bash
flask --app run.py db upgrade
```

Se você alterar modelos futuramente:

```bash
flask --app run.py db migrate -m "sua mensagem"
flask --app run.py db upgrade
```

## Execução

### Desenvolvimento (Windows/Linux/macOS)

```bash
# opção 1
flask --app run.py run

# opção 2
python run.py
```

Acesse `http://localhost:5000/health` para verificar.

### Produção (Linux/WSL/Docker)

Use Gunicorn:

```bash
gunicorn -w 2 -b 0.0.0.0:5000 run:app
```

Observação: Gunicorn não funciona nativamente no Windows (usa `fcntl`). Em Windows, execute via WSL/Docker, ou use `waitress`:

```bash
pip install waitress
python -c "from waitress import serve; from run import app; serve(app, host='0.0.0.0', port=5000)"
```


## Endpoints Principais

Todas as rotas retornam JSON. Em erros, usam mensagens padronizadas.

### Produtos (`/products`)

- `POST /products` (JWT): cadastra produto (RN01: código de barras único)
- `GET /products/barcode/{codigo_barras}` (JWT): busca por código de barras

### Compras (`/purchase`)

- `POST /purchase/start` (JWT): inicia compra
- `POST /purchase/{compra_id}/add` (JWT): adiciona item
- `POST /purchase/{compra_id}/finish` (JWT): finaliza compra (RN05: ao menos um item)

### Listas (`/lists`)

- `POST /lists` (JWT): cria lista
- `GET /lists` (JWT): lista listas do usuário
- `POST /lists/{lista_id}/items` (JWT): adiciona item à lista
- `PUT /lists/items/{item_id}` (JWT): marca item como concluído
- `DELETE /lists/{lista_id}` (JWT): exclui lista e seus itens

### Histórico (`/history`)

- `GET /history` (JWT): lista compras finalizadas
- `GET /history/{compra_id}` (JWT): detalhe de uma compra finalizada
- `GET /history/compare?a={idA}&b={idB}` (JWT): compara duas compras finalizadas do mesmo usuário

## Validação e Tratamento de Erros

### Validação (Marshmallow)

- Rotas `POST/PUT` validam o corpo com schemas em `listify/schemas.py`
- Em caso de inválido: `400` com `{"error":"validation_error","details":{...}}`

Exemplos de schemas:

- `RegisterSchema`: `nome`, `email`, `senha` (RN03: 8+ caracteres, maiúscula, minúscula, número)
- `ProductSchema`: `codigo_barras`, `nome`, `marca?`
- `ItemDaCompraCreateSchema`: `produto_id`, `preco_pago` (Decimal 2 casas), `quantidade>=1`
- `ListaCreateSchema`: `nome`
- `ItemDaListaCreateSchema`: `descricao_item` (aceita alias `descricao`)

### Erros Globais JSON

- 404: `{"error":"not_found","message":"Rota ou recurso não encontrado"}`
- 405: `{"error":"method_not_allowed","message":"Método HTTP não permitido para esta rota"}`
- 401: `{"error":"unauthorized","message":"Não autorizado"}`
- 403: `{"error":"forbidden","message":"Acesso negado"}`
- 500: `{"error":"internal_server_error","message":"Erro interno do servidor"}`

### Erros JWT

- `jwt_unauthorized`: 401, falta token
- `jwt_invalid_token`: 401, token inválido
- `jwt_expired`: 401, expirado
- `jwt_revoked`: 401, revogado


## Notas e Limitações

- Gunicorn não funciona nativamente no Windows; use WSL/Docker ou `waitress` para rodar em produção no Windows.
- Precisão monetária: valores tratados como `Decimal` com 2 casas; garanta que o banco use `NUMERIC(10,2)`.
- Migrações: sempre rode `db migrate` e `db upgrade` ao alterar modelos.
- Segurança: mantenha segredo das chaves (`SECRET_KEY`, `JWT_SECRET_KEY`) e use HTTPS em produção.

---

Em caso de dúvidas ou problemas, verifique os logs da aplicação e valide o `.env`. Este manual cobre instalação, configuração e uso básico da API Listify.