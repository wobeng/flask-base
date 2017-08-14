from flask import request


def multi_dict_marsh(multi_dict, many=False):
    return {key: val.split(',') if many else val for key, val in multi_dict.items()}


def request_body(many=False):
    return request.get_json(True, True) or multi_dict_marsh(request.form, many)


def request_query(many=False):
    return multi_dict_marsh(request.args, many)


def request_header():
    return {
        key.lower().replace('-', '_'): val
        for key, val in request.headers
    }


def request_view_arg():
    return dict(request.view_args)
