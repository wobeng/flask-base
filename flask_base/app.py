from apispec.ext.marshmallow import openapi

from flask_base.utils import OpenAPIConverter2

openapi.OpenAPIConverter = OpenAPIConverter2
from flasgger import Swagger, LazyString, LazyJSONEncoder
from flask import Flask, jsonify, request, redirect
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_base.exceptions import Error
import os


def init_api(name, title='', uiversion=2, supports_credentials=False, origins='*', flask_vars=None):
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
        app.config[k] = translate.get(v, v)

    # handle error
    @app.errorhandler(Error)
    def handle_client_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    # init swagger
    app.config['SWAGGER'] = dict(title=title, uiversion=uiversion)
    app.json_encoder = LazyJSONEncoder
    template = dict(
        host=LazyString(lambda: request.host),
        schemes=[LazyString(lambda: 'https' if request.is_secure else 'http')]
    )
    Swagger(app, template=template)

    @app.route('/')
    def index():
        return redirect('/apidocs')

    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    return app
