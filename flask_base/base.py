import os

from flask import make_response
from flask.views import MethodView

from flask_base.exceptions import Error
from flask_base.jsonstyle import GoogleJsonStyle
from flask_base.schema import validate_schema
from flask_base.swagger import generate_swagger
from flask_base.utils import generate_cookie


class Base(MethodView):
    pre_decorators = []

    def __init__(self):
        self.cookies = []

    def set_cookie(
        self,
        name,
        content="",
        max_age=0,
        allowed_domains=None,
        http_only=True,
        samesite=True,
    ):
        allowed_domains = allowed_domains or os.environ["ALLOWED_DOMAINS"]
        self.cookies.append(
            generate_cookie(
                name, content, max_age, allowed_domains, http_only, samesite
            )
        )

    def success(self, data=None, msg=None):
        if isinstance(data, list):
            data = {"items": data}
        style = GoogleJsonStyle(self, data, msg)
        response = make_response(style.body())
        response.status_code = style.status_code()
        response.headers["Content-Type"] = style.content_type()
        for cookie in self.cookies:
            response.set_cookie(**cookie)
        return response

    @staticmethod
    def fail(msg, status_code=400):
        return Error(msg, status_code).response()

    @classmethod
    def as_view(cls, name, *class_args, **class_kwargs):
        _cls = generate_swagger(cls) if generate_swagger else cls
        view_func = super(Base, _cls).as_view(
            name, *class_args, **class_kwargs
        )
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
