import os

from aws_utils import client
from flasgger import Swagger
from flask import Flask, jsonify
from flask_cors import CORS

from flask_base.exceptions import Error

# init aws and load config from s3 to environment if dev
aws = None


def init_api(name, **cors):
    # create an application instance.
    app = Flask(name, instance_relative_config=True)

    # init cors
    CORS(app, **cors)

    try:
        # add flask configs
        global aws
        aws = client()
        for env in os.environ:
            if env.startswith("FLASK_"):
                app.config[env.replace("FLASK_", "")] = os.environ[env]
    except BaseException:
        pass

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
