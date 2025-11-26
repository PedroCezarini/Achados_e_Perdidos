import os

# Exemplos de chaves/URIs que seu app possivelmente espera.
# Nunca commit valores reais — defina as variáveis no ambiente (Render / .env local).
ATLAS_CONNECTION_STRING = os.environ.get("ATLAS_CONNECTION_STRING", "")
SECRET_KEY = os.environ.get("SECRET_KEY", "")

# opcional: nome do db, usuário padrão, etc.
MONGO_DBNAME = os.environ.get("MONGO_DBNAME", "achadoseperdidos")