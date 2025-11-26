from pymongo import MongoClient
import os, pprint
from hashlib import sha256

uri = os.environ.get("ATLAS_CONNECTION_STRING") or "mongodb+srv://admin:<PASSWORD>@cluster0.../achadoseperdidos?retryWrites=true&w=majority"
client = MongoClient(uri)
db = client["achadoseperdidos"]

matricula = "11111"
print("Collections in DB:", db.list_collection_names())

# check typical variants
for colname in ["Funcionarios", "funcionarios", "funcionarios_collections", "funcionarios_collection"]:
    col = db[colname]
    user = col.find_one({"matricula": matricula})
    print(f"\nChecking collection '{colname}': found ->", bool(user))
    if user:
        pprint.pprint(user)
        stored = user.get("senha")
        print("stored type:", type(stored))
        print("stored repr:", repr(stored))
        # compute sha256 of the password you tried (adjust below)
        tried = "senha"   # altere para a senha que você digitou no formulário
        computed = sha256(tried.encode("utf-8")).hexdigest()
        print(f"sha256({tried!r}) = {computed}")
        print("stored == computed ->", stored == computed)