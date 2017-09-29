import os

import simplejson
from flask import make_response, request
from flask.views import MethodView

from flask_base.schema import validate_schema
from flask_base.swagger import generate_swagger


class Base(MethodView):
    pre_decorators = []

    def __init__(self):
        self.cookies = []

    def set_cookie(self, name, content='', max_age=0, allowed_domains=None, http_only=True):
        allowed_domains = allowed_domains or os.environ['ALLOWED_DOMAINS']
        allowed_domains = allowed_domains.split(',')
        domain = allowed_domains[0]
        for allowed_domain in allowed_domains:
            if allowed_domain in str(request.host):
                domain = allowed_domain
        self.cookies.append({
            'key': name,
            'value': content,
            'httponly': http_only,
            'max_age': max_age,
            'secure': request.environ.get('HTTP_REFERER', 'https').startswith('https'),
            'domain': '.' + domain
        })

    @staticmethod
    def status_code(data):
        data = bool(data)
        codes = {
            True: {'POST': 201, 'OTHER': 200},
            False: {'POST': 201, 'GET': 404, 'OTHER': 204},
        }
        return codes.get(data).get(request.method, codes[data]['OTHER'])

    @staticmethod
    def make_response(data=None, msg=None):
        data = data or {}
        if msg:
            data['message'] = msg
        if data:
            data = {'data': {'items': data}}
            data = simplejson.dumps(data, indent=3)
        response = make_response(data or '')
        response.status_code = Base.status_code(data)
        response.headers['Content-Type'] = 'application/json'
        return response

    def success(self, data=None, msg=None):
        response = self.make_response(data, msg)
        for cookie in self.cookies:
            response.set_cookie(**cookie)
        return response

    @classmethod
    def as_view(cls, name, *class_args, **class_kwargs):
        _cls = generate_swagger(cls) if generate_swagger else cls
        view_func = super(Base, _cls).as_view(name, *class_args, **class_kwargs)
        for decorator in [validate_schema] + cls.pre_decorators:
            if decorator:
                view_func2 = decorator(view_func)
                view_func2.view_class = view_func.view_class
                view_func2.__name__ = view_func.__name__
                view_func2.__doc__ = view_func.__doc__
                view_func2.__module__ = view_func.__module__
                view_func2.methods = view_func.methods
                view_func = view_func2
        return view_func
