from flask_base.exceptions import Error
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS
from flask import Flask, redirect
from flasgger import Swagger, LazyJSONEncoder
from apispec.ext.marshmallow import openapi

from flask_base.utils import OpenAPIConverter2

openapi.OpenAPIConverter = OpenAPIConverter2


class CloudfrontProxy(object):
    """This middleware sets the proto scheme based on cloudfront header"""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        if "HTTP_CLOUDFRONT_FORWARDED_PROTO" in environ:
            environ["wsgi.url_scheme"] = environ["HTTP_CLOUDFRONT_FORWARDED_PROTO"]
        return self.app(environ, start_response)


def init_api(
    name,
    title="",
    uiversion=2,
    supports_credentials=False,
    origins="*",
    flask_vars=None,
    index_docs=True,
):
    # create an application instance.
    app = Flask(name, instance_relative_config=True, subdomain_matching=True)

    # init reserve proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_port=1)
    app.wsgi_app = CloudfrontProxy(app.wsgi_app)

    # init cors
    if origins != "*":
        if isinstance(origins, str):
            origins = [origins]
    CORS(app, origins=origins, supports_credentials=supports_credentials)

    # load flask environment in app
    flask_vars = flask_vars or {}
    translate = {"True": True, "False": False, "None": None}
    for k, v in flask_vars.items():
        if k.startswith("FLASK_"):
            app.config[k.replace("FLASK_", "")] = translate.get(v, v)

    # handle error
    @app.errorhandler(Error)
    def handle_client_error(error):
        return error.response()

    # init swagger
    app.config["SWAGGER"] = dict(title=title, uiversion=uiversion)
    app.json_encoder = LazyJSONEncoder
    swagger_config = {"specs_route": "/apidocs"}
    Swagger(app, config=swagger_config, merge=True)

    if index_docs:

        @app.route("/")
        def index():
            return redirect("/apidocs")

    return app
