import simplejson
from flask import make_response
from flask.views import MethodView

from flask_base.schema import validate_schema
from flask_base.swagger import generate_swagger


class Base(MethodView):
    schema = validate_schema
    swagger = generate_swagger

    @staticmethod
    def jsonify(data):
        data = simplejson.dumps(data, indent=3)
        response = make_response(data)
        response.headers['Content-Type'] = 'application/json'
        return response

    @classmethod
    def as_view(cls, name, *class_args, **class_kwargs):

        view_func = super(Base, cls).as_view(name, *class_args, **class_kwargs)

        for decorator in [cls.schema]:
            if decorator:
                view_func2 = decorator(view_func)
                view_func2.view_class = view_func.view_class

                view_func2.__name__ = view_func.__name__
                view_func2.__doc__ = view_func.__doc__
                view_func2.__module__ = view_func.__module__
                view_func2.methods = view_func.methods
                view_func = view_func2

        return view_func
