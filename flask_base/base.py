import simplejson
from flask import make_response
from flask.views import MethodView

from flask_base.schema import validate_schema
from flask_base.swagger import generate_swagger


class Base(MethodView):
    v_schema = validate_schema
    g_swagger = generate_swagger

    @staticmethod
    def jsonify(data={}, translate_code=None):
        data = {'data': simplejson.dumps(data, indent=3)}
        if translate_code:
            data['translate_code'] = translate_code
        response = make_response({'data': data})
        response.headers['Content-Type'] = 'application/json'
        return response

    @classmethod
    def as_view(cls, name, *class_args, **class_kwargs):
        _cls = cls.g_swagger(cls) if cls.g_swagger else cls
        view_func = super(Base, _cls).as_view(name, *class_args, **class_kwargs)

        for decorator in [cls.v_schema]:
            if decorator:
                view_func2 = decorator(view_func)
                view_func2.view_class = view_func.view_class

                view_func2.__name__ = view_func.__name__
                view_func2.__doc__ = view_func.__doc__
                view_func2.__module__ = view_func.__module__
                view_func2.methods = view_func.methods
                view_func = view_func2

        return view_func
