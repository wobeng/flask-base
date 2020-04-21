from apispec.ext.marshmallow import openapi

from flask_base.utils import OpenAPIConverter2

openapi.OpenAPIConverter = OpenAPIConverter2
from flasgger import Swagger, LazyString, LazyJSONEncoder
from flask import Flask, request, redirect
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_base.exceptions import Error


def init_api(name, title='', uiversion=2, supports_credentials=False, origins='*', flask_vars=None, index_docs=True):
    # create an application instance.
    app = Flask(name, instance_relative_config=True)
    # init cors
    if origins != '*':
        if isinstance(origins, str):
            origins = [origins]
    CORS(app, origins=origins, supports_credentials=supports_credentials)

    # load flask environment in app
    flask_vars = flask_vars or {}
    translate = {'True': True, 'False': False, 'None': None}
    for k, v in flask_vars.items():
        if k.startswith('FLASK_'):
            app.config[k.split('_')[-1]] = translate.get(v, v)

    # handle error
    @app.errorhandler(Error)
    def handle_client_error(error):
        return error.response()

    # init swagger
    app.config['SWAGGER'] = dict(title=title, uiversion=uiversion)
    app.json_encoder = LazyJSONEncoder
    template = dict(
        host=LazyString(lambda: request.host),
        schemes=[LazyString(lambda: 'https' if request.is_secure else 'http')]
    )
    Swagger(app, template=template)

    if index_docs:
        @app.route('/')
        def index():
            return redirect('/apidocs')

    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    return app
