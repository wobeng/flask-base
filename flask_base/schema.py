from flask import request, g

import flask_base.exceptions as excepts
from flask_base import reqdata
from flask_base.utils import function_args, http_path, find_schemas


def validate_schema(view_func):
    def load_schemas(path, data, schemas, class_name):
        """Load and validate parent and child schema"""

        schemas_data = {}
        schemas_errors = {}

        for schema in schemas:

            schema_data, schema_errors = schema().load(data)
            schemas_data.update(schema_data)

            if schema_errors:
                schemas_errors.update(schema_errors)

        if schemas_errors:
            expectation = getattr(excepts, path.title().replace('_', ''))
            raise expectation(schemas_errors, class_name)

        return schemas_data

    def wrapper(*args, **kwargs):

        """For each incoming data given, load and validate"""
        processed_data = {}

        request_method = getattr(view_func.view_class, request.method.lower())
        view_func_args = function_args(request_method)

        # add global arg if global args exist in class
        if hasattr(view_func.view_class, 'global_args'):
            for arg in view_func.view_class.global_args:
                if arg not in view_func_args:
                    view_func_args[arg] = view_func.view_class.global_args[arg]
                    view_func_args[arg]['scope'] = 'global'

        for arg in view_func_args:

            # set non http_path to none for now
            if arg not in http_path:
                processed_data[arg] = None
                continue

            # get data from request
            # find schemas for request
            # validate schemas
            data = getattr(reqdata, 'request_' + arg)()
            if arg == 'view_arg' and hasattr(g, 'view_args'):  # check for url processors
                data.update(g.view_args)
            schemas = find_schemas(request.method.title(), arg, view_func.view_class.schema)
            processed_data[arg] = load_schemas(arg, data, schemas, view_func.view_class.__name__)

        # pass validated url variable overriding non http_path
        if 'view_arg' in processed_data:
            processed_data.update(processed_data.pop('view_arg'))

        # update function with requested data
        for arg in processed_data:
            if arg in view_func_args and view_func_args[arg]['scope'] == 'local':
                kwargs[arg] = processed_data[arg]
        return view_func(*args, **kwargs)

    return wrapper
