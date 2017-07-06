from flask import Blueprint

from flask_base.schema import SchemaView

"""Create a blueprint  instance."""
api = Blueprint('api', __name__)


class Api(SchemaView):
    tags = 'Users'


from tests.apps.api_v1 import case
