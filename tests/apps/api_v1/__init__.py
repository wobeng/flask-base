from flask import Blueprint

from flask_base.base import Base
from flask_base.schema import validate_schema

"""Create a blueprint  instance."""
api = Blueprint('api', __name__)


class Api(Base):
    tags = 'Users'


from tests.apps.api_v1 import case
