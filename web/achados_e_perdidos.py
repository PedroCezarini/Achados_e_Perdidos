from flask import Flask, render_template, session
from .decorators import login_required, session_expired
from zoneinfo import ZoneInfo
from datetime import datetime
from .modules.funcionarios import funcionario
from .modules.categorias import categoria, get_categorias
from .modules.objetos import objeto, get_objetos_perdidos
from .modules.logon import logon
from .modules.busca import busca
import os
import secrets

app = Flask(__name__)
# pegar SECRET_KEY do ambiente (Render) ou gerar temporariamente em dev
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(16)

app.register_blueprint(categoria)
app.register_blueprint(objeto)
app.register_blueprint(funcionario)
app.register_blueprint(logon)
app.register_blueprint(busca)


# Filtros #
@app.template_filter("format_datetime")
def jinja_format_datetime(value):
    if value is None:
        return ""

    if isinstance(value, str):
        try:
            value = datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return value

    if value.tzinfo is None:
        value = value.replace(tzinfo=ZoneInfo("UTC"))

    local_tz = ZoneInfo("America/Sao_Paulo")
    value_local = value.astimezone(local_tz)
    return value_local.strftime("%d/%m/%Y")


# ----- #
# Index #
@app.route("/")
def index():
    sessao = {
        "id": session.get("funcionario_id", ""),
        "nome": session.get("nome", ""),
        "administrador": session.get("administrador", ""),
        "logado": session.get("logado", ""),
    }

    hoje = datetime.now().strftime(r"%Y-%m-%d")

    return render_template(
        "index.html",
        objetos_perdidos=get_objetos_perdidos(),
        categorias=get_categorias(),
        hoje=hoje,
        sessao=sessao,
    )


@app.route("/admin/")
@login_required
@session_expired
def admin():
    sessao = {
        "id": session.get("funcionario_id", ""),
        "nome": session.get("nome", ""),
        "administrador": session.get("administrador", ""),
    }

    return render_template("admin.html", sessao=sessao)


@app.route("/login/")
def login():
    return render_template("login.html")


if __name__ == "__main__":
    app.jinja_env.auto_reload = True
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
    app.run(debug=True)