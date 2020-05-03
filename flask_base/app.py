from apispec.ext.marshmallow import openapi

from flask_base.utils import OpenAPIConverter2

openapi.OpenAPIConverter = OpenAPIConverter2
from flasgger import Swagger, LazyString, LazyJSONEncoder
from flask import Flask, request, redirect
from flask_cors import CORS
from flask_base.exceptions import Error


class CloudfrontProxy(object):
    """This middleware sets the proto scheme based on cloudfront header"""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        if 'HTTP_CLOUDFRONT_FORWARDED_PROTO' in environ:
            environ['wsgi.url_scheme'] = environ['HTTP_CLOUDFRONT_FORWARDED_PROTO']
        return self.app(environ, start_response)


def init_api(name, title='', uiversion=2, supports_credentials=False, origins='*', flask_vars=None, index_docs=True):
    # create an application instance.
    app = Flask(name, instance_relative_config=True)
    # init reserve proxy
    app.wsgi_app = CloudfrontProxy(app.wsgi_app)

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
    return app
