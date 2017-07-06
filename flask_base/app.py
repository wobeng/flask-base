import os
from aws_helper.aws import Aws
from flasgger import Swagger
from flask import Flask
from py_helper.i18n import i18n

# init aws and load config from s3 to environment if dev
aws = Aws()
if os.environ.get('SERVERTYPE', "DEV") == "DEV":
    aws.load_config()


def init_app(name):
    # create an application instance.
    app = Flask(name, instance_relative_config=True)

    # register i18n
    app.jinja_env.add_extension('jinja2.ext.i18n')
    app.jinja_env.install_gettext_translations(i18n)

    # add flask configs
    for env in os.environ:
        if env.startswith("FLASK_"):
            app.config[env.replace("FLASK_", "")] = os.environ[env]

    # add swagger
    app.config['SWAGGER'] = dict(title='', uiversion=2)
    template = dict(swagger='2.0')
    Swagger(app, template=template)

    return app
