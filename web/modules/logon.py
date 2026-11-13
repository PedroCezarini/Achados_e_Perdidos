from flask import Blueprint, request, session, flash, redirect, url_for, current_app
from hashlib import sha256
from time import time as time_now

# Verificação opcional de hashes mais fortes (Werkzeug), para facilitar uma futura migração
try:
    from werkzeug.security import check_password_hash
except Exception:
    check_password_hash = None

logon = Blueprint("logon", __name__)


def _get_funcionarios_collection():
    """Usa a mesma conexão com o banco que as demais telas (módulo funcionarios)."""
    from .funcionarios import funcionarios_collections

    return funcionarios_collections


@logon.route("/logon", methods=["POST"])
def logon_action():
    # ler request.form dentro do handler
    matricula = request.form.get("matricula", "").strip()
    senha = request.form.get("senha", "")

    # debug via logger (mais seguro que prints). Remova/abaixe nível em produção.

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
