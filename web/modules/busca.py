from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from datetime import datetime, timezone
from decorators import login_required, session_expired
import pymongo
import secret

client = pymongo.MongoClient(secret.ATLAS_CONNECTION_STRING)
db = client["achadoseperdidos"]
objetos_collections = db["objetos"]
categorias_collections = db["categorias"]

busca = Blueprint("busca", __name__)


def data_valida(s):
    try:
        datetime.strptime(s, r"%Y-%m-%d")
        return True
    except ValueError:
        return False


def buscar_objetos(
    data_encontrado,
    categoria_id,
    identificacao,
    local_encontrado,
    status,
    backend=False,
):
    query = {}

    if data_encontrado:
        if not data_valida(data_encontrado):
            return jsonify({"error": "Data inválida"}), 400

        hoje = datetime.now()
        encontrada = datetime.strptime(data_encontrado, r"%Y-%m-%d")

        if encontrada > hoje:
            return jsonify({"error": "Data inválida"}), 400

        query["data_encontrado"] = data_encontrado

    if categoria_id and categoria_id != "0":
        categoria = db.categorias.find_one({"_id": ObjectId(categoria_id)})

        if not categoria:
            return jsonify({"error": "Categoria inválida"}), 400

        query["categoria"] = ObjectId(categoria_id)

    if identificacao:
        query["identificacao"] = {"$regex": identificacao, "$options": "i"}

    if local_encontrado:
        query["local_encontrado"] = {"$regex": local_encontrado, "$options": "i"}

    if backend and status and status != "0":
        if status.lower() not in ["perdido", "doado", "entregue"]:
            return jsonify({"error": "Status inválida"}), 400

        query["status"] = status

    pipeline = []

    if query:
        pipeline.append({"$match": query})

    project_fields = {
        "_id": 0,
        "data_encontrado": 1,
        "categoria_nome": "$categoria.nome",
        "identificacao": 1,
        "local_encontrado": 1,
    }

    if backend:
        project_fields["_id"] = {"$toString": "$_id"}
        project_fields.update(
            {
                "status": 1,
            }
        )

    pipeline.extend(
        [
            {
                "$lookup": {
                    "from": "categorias",
                    "localField": "categoria",
                    "foreignField": "_id",
                    "as": "categoria",
                }
            },
            {
                "$unwind": "$categoria",
            },
            {
                "$project": project_fields,
            },
            {"$sort": {"data_encontrado": -1}},
        ]
    )

    objetos = list(objetos_collections.aggregate(pipeline))

    return jsonify(objetos)


@busca.route("/busca", methods=["GET"])
def buscar_front():
    data_encontrado = request.args.get("data_encontrado")
    categoria_id = request.args.get("categoria_id")
    identificacao = request.args.get("identificacao")
    local_encontrado = request.args.get("local_encontrado")

    return buscar_objetos(
        data_encontrado, categoria_id, identificacao, local_encontrado, None
    )


@login_required
@session_expired
@busca.route("/admin/busca", methods=["GET"])
def buscar_admin():
    data_encontrado = request.args.get("data_encontrado")
    categoria_id = request.args.get("categoria_id")
    identificacao = request.args.get("identificacao")
    local_encontrado = request.args.get("local_encontrado")
    status = request.args.get("status")

    return buscar_objetos(
        data_encontrado,
        categoria_id,
        identificacao,
        local_encontrado,
        status,
        backend=True,
    )
