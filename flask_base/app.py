from flasgger import Swagger
from flask import Flask, jsonify
from flask_cors import CORS

from py_utils.exceptions import Error


def init_api(name, **cors):
    # create an application instance.
    app = Flask(name, instance_relative_config=True)

    # init cors
    CORS(app, **cors)

    # handle error
    @app.errorhandler(Error)
    def handle_client_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    # init swagger
    app.config['SWAGGER'] = dict(title='', uiversion=2)
    Swagger(app, template=dict(swagger='2.0'))

    return app
