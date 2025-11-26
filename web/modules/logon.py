from flask import Blueprint, request, session, flash, redirect, url_for, current_app
from hashlib import sha256
from time import time as time_now
import os

# optional: werkzeug check_password_hash for compatibility with stronger hashes
try:
    from werkzeug.security import check_password_hash
except Exception:
    check_password_hash = None  # fallback handled below

logon = Blueprint("logon", __name__)

# cache the client for the process lifetime to avoid recreating it every request
_client_cache = None

def _get_funcionarios_collection():
    """
    Retorna a collection correta de funcionários de forma tolerante:
    - tenta importar `db` do módulo principal (achados_e_perdidos)
    - tenta ler current_app.config (ATLAS_CONNECTION_STRING / MONGO_URI)
    - tenta usar variável de ambiente ATLAS_CONNECTION_STRING / MONGO_URI
    - prefere 'funcionarios' (lowercase) se a coleção existir, caso contrário usa 'Funcionarios'
    - usa _client_cache para não recriar clientes em cada requisição
    """
    global _client_cache

    # 1) tentar pegar db exportado pelo módulo principal (se existir)
    try:
        from achados_e_perdidos import db
        coll_names = db.list_collection_names()
        if "funcionarios" in coll_names:
            return db["funcionarios"]
        if "Funcionarios" in coll_names:
            return db["Funcionarios"]
        # default: return lowercase name (will create on first insert if needed)
        return db["funcionarios"]
    except Exception:
        # não conseguimos importar o db do módulo principal — prosseguir com fallback
        pass

    # 2) tentar pegar URI do current_app.config (quando disponível)
    uri = None
    try:
        uri = current_app.config.get("ATLAS_CONNECTION_STRING") or current_app.config.get("MONGO_URI")
    except RuntimeError:
        # current_app não disponível fora do contexto, mas aqui chamamos dentro da rota normalmente
        uri = None

    # 3) fallback para variável de ambiente
    if not uri:
        uri = os.environ.get("ATLAS_CONNECTION_STRING") or os.environ.get("MONGO_URI")

    if not uri:
        raise RuntimeError("ATLAS_CONNECTION_STRING não está definida e 'db' não pôde ser importado.")

    # reutilizar cliente para reduzir overhead
    if _client_cache is None:
        from pymongo import MongoClient
        _client_cache = MongoClient(uri, serverSelectionTimeoutMS=5000)

    db_name = "achadoseperdidos"
    db = _client_cache[db_name]
    coll_names = db.list_collection_names()
    if "funcionarios" in coll_names:
        return db["funcionarios"]
    if "Funcionarios" in coll_names:
        return db["Funcionarios"]
    return db["funcionarios"]


@logon.route("/logon", methods=["POST"])
def logon_action():
    # ler request.form dentro do handler
    matricula = request.form.get("matricula", "").strip()
    senha = request.form.get("senha", "")

    # debug via logger (mais seguro que prints). Remova/abaixe nível em produção.
    current_app.logger.debug("Login attempt matricula=%r senha_len=%d", matricula, len(senha))

    if not (matricula and senha):
        flash("Login Inválido!", "danger")
        return redirect(url_for("login"))

    try:
        funcionarios_collections = _get_funcionarios_collection()
    except Exception as e:
        current_app.logger.error("Erro ao obter coleção Funcionarios: %s", e)
        flash("Erro no servidor (DB). Contate o administrador.", "danger")
        return redirect(url_for("login"))

    # buscar primeiro por matrícula (mais robusto que consulta composta matricula+senha)
    funcionario = funcionarios_collections.find_one({"matricula": matricula})
    current_app.logger.debug("Lookup por matricula -> %s", bool(funcionario))

    if not funcionario:
        flash("Login Inválido!", "danger")
        return redirect(url_for("login"))

    if funcionario.get("desligado"):
        flash("Usuário desligado. Contate o administrador.", "danger")
        return redirect(url_for("login"))

    stored = funcionario.get("senha", "")
    # calcular sha256 da senha fornecida
    senha_sha = sha256(senha.encode("utf-8")).hexdigest()
    current_app.logger.debug("stored senha repr: %r", stored)
    current_app.logger.debug("computed sha256: %s", senha_sha)

    password_ok = False

    # Compatibilidade: se stored parece ser um hash werkzeug (pbkdf2/scrypt/bcrypt) use check_password_hash
    if isinstance(stored, str):
        lower = stored.lower()
        if (stored.startswith("pbkdf2:") or stored.startswith("scrypt:") or "$" in stored) and check_password_hash:
            try:
                password_ok = check_password_hash(stored, senha)
            except Exception:
                password_ok = False
        else:
            # comparar com sha256(hex)
            password_ok = (stored == senha_sha)
    else:
        # se stored for bytes ou outro tipo, normalize e compare
        try:
            stored_str = stored.decode("utf-8"
            ) if isinstance(stored, (bytes, bytearray)) else str(stored)
            password_ok = (stored_str == senha_sha)
        except Exception:
            password_ok = False

    if password_ok:
        session["funcionario_id"] = str(funcionario["_id"])
        session["nome"] = funcionario.get("nome")
        session["administrador"] = funcionario.get("administrador", False)
        session["logado"] = int(time_now())
        flash("Login com sucesso!", "success")
        return redirect(url_for("admin"))

    flash("Login Inválido!", "danger")
    return redirect(url_for("login"))


@logon.route("/logout", methods=["GET", "POST"])
def logout():
    # limpar toda a sessão para garantir logout completo
    session.clear()
    flash("Você saiu com sucesso.", "success")
    return redirect(url_for("login"))