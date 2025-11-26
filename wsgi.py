# WSGI entrypoint — usa o pacote `web`
from web.achados_e_perdidos import app

# se sua app usar factory: from web.achados_e_perdidos import create_app; app = create_app()