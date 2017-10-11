from flasgger import Swagger, LazyString, LazyJSONEncoder
from flask import Flask, jsonify, request, redirect
from flask_cors import CORS

from flask_base.exceptions import Error


def init_api(name, title='', uiversion=2, supports_credentials=False, origins='*', flask_vars=None):
    # create an application instance.
    app = Flask(name, instance_relative_config=True)

    # init cors
    if origins != '*':
        if 'https:' in origins:
            other_protocol = origins.replace('https:', 'http:')
        else:
            other_protocol = origins.replace('http:', 'https:')
        origins = [origins, other_protocol]
    CORS(app, origins=origins, supports_credentials=supports_credentials)

    # load flask environment in app
    flask_vars = flask_vars or {}
    translate = {'True': True, 'False': False, 'None': None}
    print(flask_vars)
    for k, v in flask_vars.items():
        app.config[k] = translate.get(v)

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
        title=title,
        host=LazyString(lambda: request.host),
        schemes=[LazyString(lambda: 'https' if request.is_secure else 'http')]
    )
    Swagger(app, template=template)

    @app.route('/')
    def index():
        return redirect('/apidocs')

    return app
