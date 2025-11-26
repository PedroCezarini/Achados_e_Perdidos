from bson.codec_options import CodecOptions
from bson.objectid import ObjectId
from datetime import datetime, timezone
from decorators import login_required, session_expired, admin_required
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from upload import salvar_arquivo
import pymongo
import secret

client = pymongo.MongoClient(secret.ATLAS_CONNECTION_STRING)
db = client["achadoseperdidos"].with_options(
    codec_options=CodecOptions(tz_aware=True, tzinfo=timezone.utc)
)
objetos_collections = db["objetos"]
categorias_collections = db["categorias"]

objeto = Blueprint("objeto", __name__)


def data_valida(s):
    try:
        datetime.strptime(s, r"%Y-%m-%d")
        return True
    except ValueError:
        return False


@objeto.route("/admin/objeto")
@login_required
@session_expired
def objeto_index():
    categorias = list(categorias_collections.find().sort('nome', 1))
    objetos = list(
        objetos_collections.aggregate(
            [
                {
                    "$lookup": {
                        "from": "categorias",
                        "localField": "categoria",
                        "foreignField": "_id",
                        "as": "categoria",
                    }
                },
                {"$unwind": "$categoria"},
            ]
        )
    )

    hoje = datetime.now().strftime(r"%Y-%m-%d")

    sessao = {
        "id": session.get("funcionario_id", ""),
        "nome": session.get("nome", ""),
        "administrador": session.get("administrador", ""),
    }

    return render_template(
        "objeto.html",
        objetos=objetos,
        categorias=categorias,
        hoje=hoje,
        sessao=sessao,
    )


@objeto.route("/admin/objeto/add", methods=["POST"])
@login_required
@session_expired
def objeto_add():
    descricao = request.form.get("descricao")
    data_encontrado = request.form.get("data_encontrado")
    local_encontrado = request.form.get("local_encontrado")
    identificacao = request.form.get("identificacao")
    categoria_id = request.form.get("categoria", None)

    if not categoria_id:
        flash("Categoria inválida!", "danger")
        return redirect(url_for(".objeto_index"))

    categoria = db.categorias.find_one({"_id": ObjectId(categoria_id)})

    if not categoria:
        flash("Categoria inválida!", "danger")
        return redirect(url_for(".objeto_index"))

    if not data_encontrado:
        flash("Data encontrada inválida!", "danger")
        return redirect(url_for(".objeto_index"))

    if not data_valida(data_encontrado):
        flash("Data encontrada inválida!", "danger")
        return redirect(url_for(".objeto_index"))

    hoje = datetime.now()
    encontrada = datetime.strptime(data_encontrado, r"%Y-%m-%d")

    if encontrada > hoje:
        flash("Data encontrada inválida!", "danger")
        return redirect(url_for(".objeto_index"))

    caminho_da_imagem = None
    if "imagem" in request.files:
        imagem = request.files["imagem"]

        if imagem.filename:
            caminho_da_imagem = salvar_arquivo(imagem)

            if not caminho_da_imagem:
                flash(
                    "Tipo de arquivo da imagem não permitido ou falha ao salvar.",
                    "danger",
                )

    if not all([descricao, local_encontrado]):
        vazios = []
        if not descricao:
            vazios.append("Descrição")
        if not local_encontrado:
            vazios.append("Local encontrado")

        plural = "s" if len(vazios) > 1 else ""
        flash(f"Campo{plural} não preenchido{plural}: {', '.join(vazios)}!", "danger")
        return redirect(url_for(".categoria_index"))

    campos = {
        campo.lower(): request.form.get(f"campos[{campo}]", "")
        for campo in categoria.get("campos", [])
    }

    new_data = {
        "descricao": descricao,
        "imagem": caminho_da_imagem,
        "categoria": ObjectId(categoria_id),
        "data_insercao": datetime.now(timezone.utc),
        "data_encontrado": data_encontrado,
        "identificacao": identificacao,
        "local_encontrado": local_encontrado,
        "campos": campos,
        "resolvido": False,
        "status": "perdido",
    }

    try:
        result = objetos_collections.insert_one(new_data)

        if result.inserted_id:
            flash("Objeto adicionada com sucesso!", "success")
        else:
            flash("Erro ao adicionar objeto.", "danger")
    except Exception:
        flash("Erro crítico ao adicionar a objeto!", "danger")

    return redirect(url_for(".objeto_index"))


@objeto.route("/admin/objeto/edit/<string:objeto_id>")
@login_required
@session_expired
def objeto_edit(objeto_id):
    objeto = list(
        objetos_collections.aggregate(
            [
                {"$match": {"_id": ObjectId(objeto_id)}},
                {
                    "$lookup": {
                        "from": "categorias",
                        "localField": "categoria",
                        "foreignField": "_id",
                        "as": "categoria",
                    }
                },
                {"$unwind": "$categoria"},
                {"$limit": 1},
            ]
        )
    )[0]

    hoje = datetime.now().strftime(r"%Y-%m-%d")

    sessao = {
        "id": session.get("funcionario_id", ""),
        "nome": session.get("nome", ""),
        "administrador": session.get("administrador", ""),
    }

    return render_template(
        "objeto_editar.html",
        objeto=objeto,
        hoje=hoje,
        sessao=sessao,
    )


@objeto.route("/admin/objeto/edit/<string:objeto_id>/form", methods=["POST"])
@login_required
@session_expired
def objeto_edit_action(objeto_id):
    objeto = db.objetos.find_one({"_id": ObjectId(objeto_id)})

    descricao = request.form.get("descricao")
    data_encontrado = request.form.get("data_encontrado")
    local_encontrado = request.form.get("local_encontrado")
    identificacao = request.form.get("identificacao")
    resolvido = request.form.get("resolvido")
    status = request.form.get("status")
    resolucao = request.form.get("resolucao")
    destinatario_nome = request.form.get("destinatario_nome")
    destinatario_documento = request.form.get("destinatario_documento")
    destinatario_contato = request.form.get("destinatario_contato")
    remover_imagem = request.form.get("removerImagem")

    categoria_id = request.form.get("categoria", None)
    categoria = db.categorias.find_one({"_id": ObjectId(categoria_id)})

    if not data_encontrado:
        flash("Data encontrada inválida!", "danger")
        return redirect(url_for(".objeto_edit", objeto_id=objeto_id))

    if not data_valida(data_encontrado):
        flash("Data encontrada inválida!", "danger")
        return redirect(url_for(".objeto_edit", objeto_id=objeto_id))

    hoje = datetime.now()
    encontrada = datetime.strptime(data_encontrado, r"%Y-%m-%d")

    if encontrada > hoje:
        flash("Data encontrada inválida!", "danger")
        return redirect(url_for(".objeto_edit", objeto_id=objeto_id))

    caminho_da_imagem = None
    if not remover_imagem:
        if "imagem" in request.files:
            imagem = request.files["imagem"]

            if imagem.filename:
                caminho_da_imagem = salvar_arquivo(imagem)

                if not caminho_da_imagem:
                    flash(
                        "Tipo de arquivo da imagem não permitido ou falha ao salvar.",
                        "danger",
                    )

        if not caminho_da_imagem:
            caminho_da_imagem = objeto.get("imagem")

    if not status:
        flash("Status não pode ser vazio!", "danger")
        return redirect(url_for(".objeto_edit", objeto_id=objeto_id))

    vazios = []
    if not all([descricao, local_encontrado]):
        if not descricao:
            vazios.append("Descrição")
        if not local_encontrado:
            vazios.append("Local encontrado")

    if status != "perdido" and not all(
        [resolucao, destinatario_nome, destinatario_documento, destinatario_contato]
    ):
        if not resolucao:
            vazios.append("Resolução")
        if not destinatario_nome:
            vazios.append("Nome do destinatário")
        if not destinatario_documento:
            vazios.append("Documento do destinatário")
        if not destinatario_contato:
            vazios.append("Contato do destinatário")

    if vazios:
        plural = "s" if len(vazios) > 1 else ""
        flash(f"Campo{plural} não preenchido{plural}: {', '.join(vazios)}!", "danger")
        return redirect(url_for(".objeto_edit", objeto_id=objeto_id))

    campos = {
        campo: request.form.get(f"campos[{campo}]")
        for campo in categoria.get("campos", [])
    }

    update_data = {
        "descricao": descricao,
        "imagem": caminho_da_imagem,
        "identificacao": identificacao,
        "data_encontrado": data_encontrado,
        "local_encontrado": local_encontrado,
        "campos": campos,
        "resolvido": resolvido is not None,
        "status": status,
        "resolucao": resolucao,
        "destinatario": {
            "nome": destinatario_nome,
            "documento": destinatario_documento,
            "contato": destinatario_contato,
        },
    }

    try:
        result = objetos_collections.update_one(
            {"_id": ObjectId(objeto_id)}, {"$set": update_data}
        )

        if result.modified_count == 1:
            flash("Objeto atualizado com sucesso!", "success")
        else:
            flash("Nenhuma alteração foi detectada.", "warning")
    except Exception:
        flash("Erro crítico na atualização do objeto!", "danger")

    return redirect(url_for(".objeto_index"))


@objeto.route("/admin/objeto/<string:objeto_id>/delete")
@login_required
@session_expired
@admin_required
def objeto_deletar(objeto_id):
    objetos_collections.delete_one({"_id": ObjectId(objeto_id)})
    return redirect(url_for(".objeto_index"))


def get_objetos_perdidos():
    objetos = list(
        objetos_collections.aggregate(
            [
                {
                    "$match": {
                        "status": "perdido"  # Filtra objetos com status "perdido"
                    }
                },
                {
                    "$lookup": {
                        "from": "categorias",
                        "localField": "categoria",
                        "foreignField": "_id",
                        "as": "detalhes_categoria",
                    }
                },
                {"$unwind": "$detalhes_categoria"},
                {
                    "$project": {
                        "_id": 1,
                        "data_encontrado": 1,
                        "identificacao": 1,
                        "local_encontrado": 1,
                        "categoria_nome": "$detalhes_categoria.nome",
                        "status": 1,
                    }
                },
                {"$sort": {"data_encontrado": -1}},
            ]
        )
    )

    return objetos
