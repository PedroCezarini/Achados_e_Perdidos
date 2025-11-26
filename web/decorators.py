from functools import wraps
from flask import session, redirect, url_for, flash
from time import time


def session_expired(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        now = int(time())
        diff = now - session["logado"]
        if diff > 10 * 60:
            flash("Sessão expirou!", "danger")
            return redirect(url_for("logon.logout"))
        session["logado"] = now
        return f(*args, **kwargs)

    return decorated_function


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("logado") is None:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("administrador"):
            flash("Somente para administradores!", "danger")
            return redirect(url_for("admin"))
        return f(*args, **kwargs)

    return decorated_function
