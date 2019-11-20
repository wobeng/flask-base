import inspect
import operator
import os
import random
import uuid
from collections import OrderedDict
from datetime import datetime
from functools import reduce

from apispec.ext.marshmallow import openapi
from flask import request
from pytz import UTC

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
    secure = request.environ.get('HTTP_REFERER', 'https').startswith('https')
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

    return cookie


def load_secret(secrets):
    # load secrets
    secrets = secrets or {}
    for key, value in secrets.items():
        if key not in os.environ:
            os.environ[key] = value


def datetime_utc(dt=None):
    if not dt:
        dt = datetime.utcnow()
    return dt.replace(tzinfo=UTC)


def date_id(prefix='', suffix=None):
    def call(_prefix=prefix, _suffix=suffix):
        _suffix = datetime_utc().replace(tzinfo=None).isoformat().replace('.', ':')
        _suffix = _suffix + '_' + str(uuid.uuid4())
        _suffix = _suffix or _suffix
        if _prefix:
            _prefix = _prefix + '::'
        return _prefix + _suffix

    return call


def pin_generator():
    return random.randint(100000, 999999)


class FormatData:
    def __init__(self, item):
        self.output = {}
        self.item = dict(item)

    @staticmethod
    def get_by_path(item, path_list):
        return reduce(operator.getitem, path_list, item)

    @staticmethod
    def set_by_path(item, path_list, value):
        FormatData.get_by_path(item, path_list[:-1])[path_list[-1]] = value

    @staticmethod
    def delete_in_dict(item, path_list):
        del FormatData.get_by_path(item, path_list[:-1])[path_list[-1]]

    def inc(self, keys):
        for k in keys:
            try:
                value = self.get_by_path(self.item, k.split('.'))
                FormatData.set_by_path(self.output, k.split('.'), value)
            except KeyError as e:
                continue
        return self.output

    def exc(self, keys):
        for k in keys:
            try:
                FormatData.delete_in_dict(self.item, k.split('.'))
            except KeyError as e:
                continue
        return self.item
