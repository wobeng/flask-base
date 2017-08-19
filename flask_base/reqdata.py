from flask import request


def request_body():
    return request.get_json(True, True) or request.form


def request_query():
    return request.args


def request_header():
    return {
        key.lower().replace('-', '_'): val
        for key, val in request.headers
    }


def request_view_arg():
    return dict(request.view_args)
