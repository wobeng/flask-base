import inspect
from apispec.ext.marshmallow import openapi
from collections import OrderedDict
from flask import request

http_path = ['path', 'body', 'query', 'header', 'view_arg']
http_methods = ['get', 'head', 'post', 'put', 'delete', 'connect', 'options', 'trace', 'patch']


class OpenAPIConverter2(openapi.OpenAPIConverter):
    def __init__(self, openapi_version, schema_name_resolver=None, spec=None):
        super().__init__(openapi_version, schema_name_resolver, spec)


def function_args(func):
    """Return key:map of  functions args and meta data about args"""
    response = OrderedDict()
    args = inspect.signature(func).parameters
    # arrange function as args as a dict
    for k, v in {k: v for k, v in args.items() if k not in ['self', 'args', 'kwargs']}.items():
        v = str(v)
        try:
            default = v.split('=')[1]
        except IndexError:
            default = None
        try:
            typ = v.split(':')[1].split('=')[0]
        except IndexError:
            typ = None
        response[k] = {'default': default, 'type': typ, 'scope': 'local'}
    if any([arg for arg in response.keys() if arg not in http_path and arg != 'self']):
        response['view_arg'] = {'default': None, 'type': dict}
    return response


def find_schemas(method, schema, path=None):
    path = path.title().replace('_', '') if path else path
    schemas = []
    try:
        schemas.append(getattr(schema, path) if path else schema)
    except AttributeError:
        pass
    try:
        method_cls = getattr(schema, method)
        schemas.append(getattr(method_cls, path) if path else method_cls)
    except AttributeError:
        if not schemas:
            raise
    return schemas


def generate_cookie(name, content='', max_age=0, allowed_domains=None, http_only=True, samesite=True):
    referer = request.environ.get('HTTP_REFERER', '')
    secure = referer.startswith('https')
    cookie = {
        'key': name,
        'value': content,
        'httponly': http_only,
        'max_age': max_age,
        'secure': secure
    }

    allowed_domains = allowed_domains.split(',')
    domain = allowed_domains[0]
    for allowed_domain in allowed_domains:
        if allowed_domain in str(request.host):
            domain = allowed_domain
    cookie['domain'] = '.' + domain

    if samesite and secure:
        cookie['samesite'] = 'Strict'
    elif referer.startswith('http://localhost'):
        cookie['samesite'] = 'None'

    return cookie
