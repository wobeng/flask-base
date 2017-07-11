from flask import Blueprint

from flask_base.base import Base
from tests.models.api_v1 import BaseSchema

"""Create a blueprint  instance."""
api = Blueprint('api', __name__)


class Api(Base):
    __schema__ = BaseSchema
    tags = 'users'
    url_rules = ['host']


from tests.apps.api_v1 import case
