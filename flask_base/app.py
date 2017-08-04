import os
from aws_helper.aws import Aws
from flasgger import Swagger
from flask import Flask, jsonify
from flask_base.exceptions import Error
from flask_cors import CORS

# init aws and load config from s3 to environment if dev
aws = Aws()
if os.environ.get('SERVERTYPE', "DEV") == "DEV":
    aws.load_config()


def init_api(name, **cors):
    # create an application instance.
    app = Flask(name, instance_relative_config=True)

    # init cors
    CORS(app, **cors)

    # add flask configs
    for env in os.environ:
        if env.startswith("FLASK_"):
            app.config[env.replace("FLASK_", "")] = os.environ[env]

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
