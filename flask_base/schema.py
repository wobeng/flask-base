from flask import request, g
from marshmallow import EXCLUDE, ValidationError

import flask_base.exceptions as excepts
from flask_base.utils import function_args, http_path, find_schemas


def incoming_data(location):
    header = {
        key.lower().replace("-", "_"): val for key, val in request.headers
    }
    incoming = {
        "body": request.get_json(True, True) or request.form,
        "query": request.args,
        "header": header,
        "view_arg": dict(request.view_args),
    }
    return incoming[location]


def load_schemas(path, data, schemas, class_name):
    """Load and validate parent and child schema"""
    schemas_data = {}
    schemas_errors = {}
    for schema in schemas:
        try:
            output = schema().load(data, unknown=EXCLUDE)
            schemas_data.update(output)
        except ValidationError as err:
            schemas_errors.update(err.messages)
    if schemas_errors:
        expectation = getattr(excepts, path.title().replace("_", ""))
        raise expectation(schemas_errors, class_name)
    return schemas_data


def validate_schema(view_func):
    def wrapper(*args, **kwargs):

        """For each incoming data given, load and validate"""
        g.processed_data = {}
        g.incoming_data = {}

        request_method = getattr(view_func.view_class, request.method.lower())
        view_func_args = function_args(request_method)

        # add global arg if global args exist in class
        if hasattr(view_func.view_class, "global_args"):
            for arg in view_func.view_class.global_args:
                if arg not in view_func_args:
                    view_func_args[arg] = view_func.view_class.global_args[arg]
                    view_func_args[arg]["scope"] = "global"

        # store unprocessed incoming data
        for arg in view_func_args:
            if arg in http_path:
                g.incoming_data[arg] = incoming_data(arg)
        # process incoming data
        for arg in view_func_args:
            # set non http_path to none for now
            if arg not in http_path:
                g.processed_data[arg] = None
                continue

            # get data from request
            # find schemas for request
            # validate schemas

            data = incoming_data(arg)
            if arg == "view_arg" and hasattr(
                g, "view_args"
            ):  # check for url processors
                data.update(g.view_args)
            schemas = find_schemas(
                request.method.title(), view_func.view_class.schema, path=arg
            )
            g.processed_data[arg] = load_schemas(
                arg, data, schemas, view_func.view_class.__name__
            )

        # process post validate
        for schema in find_schemas(
            request.method.title(), view_func.view_class.schema
        ):
            if hasattr(schema, "post_validate"):
                g.processed_data = schema.post_validate(g.processed_data)

        # pass validated url variable overriding non http_path
        if "view_arg" in g.processed_data:
            g.processed_data.update(g.processed_data.pop("view_arg"))

        # update function with requested data
        for arg in g.processed_data:
            if (
                arg in view_func_args
                and view_func_args[arg]["scope"] == "local"
            ):
                kwargs[arg] = g.processed_data[arg]
        return view_func(*args, **kwargs)

    return wrapper
