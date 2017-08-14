from flask import request


def multi_dict_marsh(multi_dict):
    return {key: val.split(',') for key, val in multi_dict.items()}


def request_body():
    return request.get_json(True, True) or multi_dict_marsh(request.form)


def request_query():
    return multi_dict_marsh(request.args)


def request_header():
    return {
        key.lower().replace('-', '_'): val
        for key, val in request.headers
    }


def request_view_arg():
    return dict(request.view_args)
