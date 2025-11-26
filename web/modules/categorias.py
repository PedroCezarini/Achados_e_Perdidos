from bson.codec_options import CodecOptions
from bson.objectid import ObjectId
from datetime import datetime, timezone
from decorators import login_required, session_expired, admin_required
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    session,
)
import pymongo
import secret

client = pymongo.MongoClient(secret.ATLAS_CONNECTION_STRING)
db = client["achadoseperdidos"].with_options(
    codec_options=CodecOptions(tz_aware=True, tzinfo=timezone.utc)
)
categoria_collections = db["categorias"]

categoria = Blueprint("categoria", __name__)


@categoria.route("/admin/categoria")
@login_required
@session_expired
def categoria_index():
    categorias = []
    for categoria in categoria_collections.find().sort('nome', 1):
        categoria["campos"] = [
            campo.capitalize().replace("_", " ") for campo in categoria["campos"]
        ]
        categorias.append(categoria)

    sessao = {
        "id": session.get("funcionario_id", ""),
        "nome": session.get("nome", ""),
        "administrador": session.get("administrador", ""),
    }

    return render_template("categoria.html", categorias=categorias, sessao=sessao)


@categoria.route("/admin/categoria/add/form", methods=["POST"])
@login_required
@session_expired
def categoria_add_action():
    nome = request.form.get("nome")
    campos = list(set(request.form.getlist("campos[]")))

    num_categorias = categoria_collections.count_documents(
        {"nome": nome.strip().capitalize()}
    )
    if num_categorias:
        flash("Categoria já existe!", "danger")
        return redirect(url_for(".categoria_index"))

    if not all([nome, campos]):
        vazios = []
        if not nome:
            vazios.append("Nome")
        if not campos:
            vazios.append("Campos")

        plural = "s" if len(vazios) > 1 else ""
        flash(f"Campo{plural} não preenchido{plural}:  {', '.join(vazios)}!", "danger")
        return redirect(url_for(".categoria_index"))

    campos = [campo.lower().strip().replace(" ", "_") for campo in campos]
    new_data = {
        "nome": nome.capitalize(),
        "campos": campos,
    }

    try:
        result = categoria_collections.insert_one(new_data)

        if result.inserted_id:
            flash("Categoria adicionada com sucesso!", "success")
        else:
            flash("Erro ao adicionar categoria.", "danger")
    except Exception:
        flash("Erro crítico ao adicionar a categoria!", "danger")

    return redirect(url_for(".categoria_index"))


@categoria.route("/admin/categoria/edit/<string:categoria_id>")
@login_required
@session_expired
def categoria_edit(categoria_id):
    categoria = categoria_collections.find_one({"_id": ObjectId(categoria_id)})
    categoria["campos"] = [
        campo.capitalize().replace("_", " ") for campo in categoria["campos"]
    ]

    sessao = {
        "id": session.get("funcionario_id", ""),
        "nome": session.get("nome", ""),
        "administrador": session.get("administrador", ""),
    }

    return render_template(
        "categoria_editar.html",
        categoria=categoria,
        sessao=sessao,
    )


@categoria.route("/admin/categoria/edit/<string:categoria_id>/form", methods=["POST"])
@login_required
@session_expired
def categoria_edit_action(categoria_id):
    nome = request.form.get("nome")
    campos = list(set(request.form.getlist("campos[]")))

    categoria = categoria_collections.find_one(
        {"_id": ObjectId(categoria_id)}
    )
    if nome != categoria["nome"]:
        num_categorias = categoria_collections.count_documents(
            {"nome": nome.strip().capitalize()}
        )
        if num_categorias:
            flash("Categoria já existe!", "danger")
            return redirect(url_for(".categoria_edit", categoria_id=categoria_id))

    if not all([nome, campos]):
        vazios = []
        if not nome:
            vazios.append("Nome")
        if not campos:
            vazios.append("Campos")

        plural = "s" if len(vazios) > 1 else ""
        flash(f"Campo{plural} não preenchido{plural}: {', '.join(vazios)}!", "danger")
        return redirect(url_for(".categoria_edit", categoria_id=categoria_id))

    campos = [campo.lower().strip().replace(" ", "_") for campo in campos]
    update_data = {
        "nome": nome.capitalize(),
        "campos": campos,
    }

    try:
        result = categoria_collections.update_one(
            {"_id": ObjectId(categoria_id)}, {"$set": update_data}
        )

        if result.modified_count == 1:
            flash("Categoria atualizada com sucesso!", "success")
        else:
            flash("Nenhuma alteração foi detectada.", "warning")
    except Exception:
        flash("Erro crítico na atualização da categoria!", "danger")

    return redirect(url_for(".categoria_index"))


@categoria.route("/admin/categoria/delete/<string:categoria_id>")
@login_required
@session_expired
@admin_required
def categoria_delete(categoria_id):
    categoria_collections.delete_one({"_id": ObjectId(categoria_id)})
    return redirect(url_for(".categoria_index"))


@categoria.route("/admin/_get_campos/<categoria_id>", methods=["GET"])
@login_required
@session_expired
def get_campos(categoria_id):
    categoria = categoria_collections.find_one({"_id": ObjectId(categoria_id)})

    return jsonify(
        {
            "campos": [
                campo.replace("_", " ").capitalize()
                for campo in categoria.get("campos")
            ]
        }
    )


def get_categorias():
    categorias = []
    for categoria in categoria_collections.find().sort('nome', 1):
        categorias.append(
            {
                "id": str(categoria["_id"]),
                "nome": categoria["nome"],
            }
        )

    return categorias
