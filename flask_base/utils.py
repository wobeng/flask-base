import inspect
from collections import OrderedDict

from flask import request

http_path = ['path', 'body', 'query', 'header', 'view_arg']
http_methods = ['get', 'head', 'post', 'put', 'delete', 'connect', 'options', 'trace', 'patch']


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


def find_schemas(method, path, schema):
    path = path.title().replace('_', '')
    schemas = []
    try:
        schemas.append(getattr(schema, path))
    except AttributeError:
        pass
    try:
        schemas.append(getattr(getattr(schema, method), path))
    except AttributeError:
        if not schemas:
            raise
    return schemas


def generate_cookie(name, content='', max_age=0, allowed_domains=None, http_only=True, samesite=None):
    cookie = {
        'key': name,
        'value': content,
        'httponly': http_only,
        'max_age': max_age,
        'secure': request.environ.get('HTTP_REFERER', 'https').startswith('https')
    }

    allowed_domains = allowed_domains.split(',')
    domain = allowed_domains[0]
    for allowed_domain in allowed_domains:
        if allowed_domain in str(request.host):
            domain = allowed_domain
    cookie['domain'] = '.' + domain

    if samesite:
        cookie['samesite'] = samesite

    return cookie
