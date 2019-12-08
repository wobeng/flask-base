from flask import Blueprint, g

from flask_base.base import Base

"""Create a blueprint  instance."""
api = Blueprint('api', __name__, url_prefix='/<app>')


@api.url_defaults
def add_app_code(endpoint, values):
    values.setdefault('app', g.app)


@api.url_value_preprocessor
def pull_app_code(endpoint, values):
    g.view_args = dict()
    g.view_args['app'] = values.pop('app')


class Api(Base):
    tags = 'users'
    global_args = {
        'header': {'default': None, 'type': dict},
        'view_arg': {'default': None, 'type': dict}
    }


