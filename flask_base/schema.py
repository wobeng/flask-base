from flask import request

import flask_base.exceptions as excepts
import flask_base.req_data as req_data
from flask_base.base import Base
from flask_base.helper import function_args, http_path, find_schemas


def generate_schema(view_func):
    def merge_list_dict(l1, l2):
        """merge list of dict by index"""
        if l1 and l2:
            return [{**d, **l2[i]} for i, d in enumerate(l1) if d or l2[i]]
        return l1 + l2

    def validate_schemas(path, data, schemas):
        """Load and validate parent and child schema"""

        many = type(data) == list
        schemas_data = [] if many else {}
        schemas_errors = [] if many else {}

        for schema in schemas:
            schema_data, schema_errors = schema(many=many).load(data)
            if many:
                schemas_data = merge_list_dict(schemas_data, schema_data)
                if schema_errors:
                    schemas_errors = merge_list_dict(schemas_errors, schema_errors)
            else:
                schemas_data.update(schema_data)
                if schema_errors:
                    schemas_errors.update(schema_errors)

        if schemas_errors:
            expectation = getattr(excepts, path.title())
            raise expectation(schemas_errors)

        return schemas_data

    def wrapper(*args, **kwargs):
        """For each incoming data given, load and validate"""
        request_method = getattr(view_func.view_class, request.method.lower())
        view_func_args = function_args(request_method)

        responses = {}

        for arg in view_func_args:

            # set non http_path to none for now
            if arg not in http_path:
                responses[arg] = None
                continue

            # get data from request
            # find schemas for request
            # validate schemas
            data = getattr(req_data, 'request_' + arg)(view_func_args[arg]['type'] == 'list')
            schemas = find_schemas(arg, view_func)
            responses[arg] = validate_schemas(arg, data, schemas)

        # pass validated url variable overriding non http_path
        view_arg = responses.pop('view_arg', None)
        if view_arg:
            responses.update(view_arg)

        kwargs.update(responses)

        return view_func(*args, **kwargs)

    return wrapper


class SchemaView(Base):
    @classmethod
    def as_view(cls, name, *class_args, **class_kwargs):
        super_cls = super(SchemaView, cls)
        view_func = super_cls.as_view(name, *class_args, **class_kwargs)
        view_func = generate_schema(view_func)
        view_func.view_class = super_cls

        view_func.__name__ = name
        view_func.__doc__ = super_cls.__doc__
        view_func.__module__ = super_cls.__module__
        view_func.methods = super_cls.methods
        return view_func
