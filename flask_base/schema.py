from flask import request, g

import flask_base.exceptions as excepts
import flask_base.req_data as req_data
from flask_base.helper import function_args, http_path, find_schemas


def validate_schema(view_func):
    def merge_list_dict(l1, l2):
        """merge list of dict by index"""
        if l1 and l2:
            return [{**d, **l2[i]} for i, d in enumerate(l1) if d or l2[i]]
        return l1 + l2

    def load_schemas(path, data, schemas):
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
        g.sch_data = {}
        if not hasattr(g, 'req_data'):
            g.req_data = {}

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
                g.sch_data[arg] = None
                continue

            # get data from request
            # find schemas for request
            # validate schemas
            data = getattr(req_data, 'request_' + arg)(view_func_args[arg]['type'] == 'list')
            schemas = find_schemas(request.method.title(), arg, view_func.view_class.schema)
            g.req_data[arg] = data
            g.sch_data[arg] = load_schemas(arg, data, schemas)

        # pass validated url variable overriding non http_path
        view_arg = g.sch_data.pop('view_arg', None)
        if view_arg:
            g.sch_data.update(view_arg)

        # update function with requested data
        print(g.sch_data)
        for arg in g.sch_data:
            if view_func_args[arg]['scope'] == 'local':
                print(arg, view_func_args[arg])
                kwargs.update(g.sch_data)

        return view_func(*args, **kwargs)

    return wrapper
