import importlib
import traceback
import pkgutil
import inspect
from collections import OrderedDict

from apispec.ext.marshmallow import openapi
from flask import request
from flask_base import get_logger

http_path = ["path", "body", "query", "header", "view_arg"]
http_methods = [
    "get",
    "head",
    "post",
    "put",
    "delete",
    "connect",
    "options",
    "trace",
    "patch",
]


class OpenAPIConverter2(openapi.OpenAPIConverter):
    def __init__(self, openapi_version, schema_name_resolver=None, spec=None):
        super().__init__(openapi_version, schema_name_resolver, spec)


def function_args(func):
    """Return key:map of  functions args and meta data about args"""
    response = OrderedDict()
    args = inspect.signature(func).parameters
    # arrange function as args as a dict
    for k, v in {
        k: v for k, v in args.items() if k not in ["self", "args", "kwargs"]
    }.items():
        v = str(v)
        try:
            default = v.split("=")[1]
        except IndexError:
            default = None
        try:
            typ = v.split(":")[1].split("=")[0]
        except IndexError:
            typ = None
        response[k] = {"default": default, "type": typ, "scope": "local"}
    if any([arg for arg in response.keys() if arg not in http_path and arg != "self"]):
        response["view_arg"] = {"default": None, "type": dict}
    return response


def find_schemas(method, schema, path=None):
    path = path.title().replace("_", "") if path else path
    schemas = []
    try:
        schemas.append(getattr(schema, path) if path else schema)
    except AttributeError:
        pass
    try:
        method_cls = getattr(schema, method)
        schemas.append(getattr(method_cls, path) if path else method_cls)
    except AttributeError:
        if not schemas:
            raise
    return schemas


def generate_cookie(
    name,
    content="",
    max_age=0,
    trusted_domains=None,
    http_only=True,
    samesite=True,
):
    referer = request.environ.get("HTTP_REFERER", "")
    secure = referer.startswith("https")
    cookie = {
        "key": name,
        "value": content,
        "httponly": http_only,
        "max_age": max_age,
        "secure": secure,
    }

    trusted_domains = trusted_domains.split(",")
    domain = trusted_domains[0]
    for allowed_domain in trusted_domains:
        if allowed_domain in str(request.host):
            domain = allowed_domain
    cookie["domain"] = "." + domain

    if samesite and secure:
        cookie["samesite"] = "Strict"
    else:
        cookie["samesite"] = "None"
    # elif referer.startswith('http://localhost'):
    #   cookie['samesite'] = 'None'
    return cookie


def import_submodules(package, recursive=True):
    """Import all submodules of a module, recursively, including subpackages

    :param package: package (name or actual module)
    :type package: str | module
    :rtype: dict[str, types.ModuleType]
    """
    logger = get_logger(package)

    if isinstance(package, str):
        package = importlib.import_module(package)
    results = {}
    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + "." + name
        try:
            results[full_name] = importlib.import_module(full_name)
        except BaseException:
            logger.critical(full_name)
            logger.critical(traceback.format_exc())
        if recursive and is_pkg:
            results.update(import_submodules(full_name))
    return results
