import inspect
from collections import OrderedDict

from flask import request

import flask_base.exceptions as excepts

http_path = ['path', 'body', 'query', 'header', 'cookie', 'view_arg']


def function_args(func):
    """Return key:map of  functions args and meta data about args"""
    response = OrderedDict()
    args = inspect.signature(func).parameters
    # arrange function as args as a dict
    for k, v in {k: v for k, v in args.items() if k != 'self'}.items():
        v = str(v)
        try:
            default = v.split('=')[1]
        except IndexError:
            default = None
        try:
            typ = v.split(':')[1].split('=')[0]
        except IndexError:
            typ = None
        response[k] = {'default': default, 'type': typ}
    if any([arg for arg in response.keys() if arg not in http_path and arg != 'self']):
        response['view_arg'] = {'default': None, 'type': dict}
    return response


def find_schemas(path, view_func):
    path = path.title().replace('_', '')
    schema = view_func.view_class.__schema__
    schema_req_cls = request.method.title()
    schemas = []
    try:
        schemas.append(getattr(schema, path))
    except AttributeError:
        pass
    try:
        schemas.append(getattr(getattr(schema, schema_req_cls), path))
    except AttributeError:
        if not schemas:
            raise excepts.Schema('{} schema class is missing from {}'.format(schema_req_cls, schema.__name__))
    return schemas
