import os
from werkzeug.utils import secure_filename
from flask import current_app

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "static/uploads")

def _ensure_upload_dir():
    path = os.path.join(os.path.dirname(current_app.root_path), UPLOAD_DIR) if current_app else UPLOAD_DIR
    os.makedirs(path, exist_ok=True)
    return path

def salvar_arquivo(file_storage, prefix=None):
    """
    Salva um FileStorage (request.files['...']) no diretório de uploads e retorna o nome salvo.
    - file_storage: objeto werkzeug.datastructures.FileStorage
    - prefix: str opcional para prefixar o nome do arquivo (ex.: id do objeto)
    """
    if file_storage is None:
        raise ValueError("file_storage é None")

    filename = secure_filename(file_storage.filename)
    if prefix:
        filename = f"{prefix}_{filename}"

    # determina path relativo ao projeto; ajusta conforme sua estrutura
    upload_dir = _ensure_upload_dir()
    dest = os.path.join(upload_dir, filename)
    file_storage.save(dest)
    return filename