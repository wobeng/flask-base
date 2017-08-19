import simplejson
from flask import make_response, request
from flask.views import MethodView

from flask_base.schema import validate_schema
from flask_base.swagger import generate_swagger


class Base(MethodView):
    pre_decorators = []

    @staticmethod
    def success(data=None, msg=None):
        data = data or {}
        if msg:
            data['message'] = msg
        if data:
            data = {'data': {'items': data}}
            data = simplejson.dumps(data, indent=3)
            status_code = 200
            if request.method == 'POST':
                status_code = 201
        else:
            data = ''
            status_code = 204
            if request.method == 'GET':
                status_code = 404
            elif request.method == 'POST':
                status_code = 201
        response = make_response(data)
        response.status_code = status_code
        response.headers['Content-Type'] = 'application/json'
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
