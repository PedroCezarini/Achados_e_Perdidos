import os
from werkzeug.utils import secure_filename

PASTA = os.path.join(os.getcwd(), "static", "uploads")
EXTENSOES = {"png", "jpg", "jpeg", "gif"}
TAMANHO_MAXIMO = 16 * 1024 * 1024  # 16 Megabytes


def permitidos(arquivo):
    return "." in arquivo and arquivo.rsplit(".", 1)[1].lower() in EXTENSOES


def salvar_arquivo(arquivo):
    if arquivo and permitidos(arquivo.filename):
        nome_do_arquivo = secure_filename(arquivo.filename)
        pasta_upload = os.path.join(PASTA, nome_do_arquivo)
        arquivo.save(pasta_upload)
        return os.path.join("uploads", nome_do_arquivo)
    return None
