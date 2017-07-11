from collections import Mapping

import simplejson
import yaml
from apispec import APISpec

from flask_base.helper import function_args, http_path, find_schemas, http_methods


def generate_swagger(cls):
    def update_nested(d, u):
        """Update nested dictionary"""
        for k, v in u.items():
            if isinstance(v, Mapping):
                r = update_nested(d.get(k, {}), v)
                d[k] = r
            else:
                d[k] = u[k]
        return d

    def generate_spec(schema):
        """Generate apispec """
        spec = APISpec(
            title=class_name,
            version='1.0.0',
            plugins=(
                'apispec.ext.flask',
                'apispec.ext.marshmallow',
            ),
        )
        spec.definition(class_name, schema=schema)
        return simplejson.loads(simplejson.dumps(spec.to_dict()['definitions']))

    def find_specs(schemas):
        """Generate apispec for parent and child schema"""
        schemas_data = {}
        for schema in schemas:
            data = generate_spec(schema)
            schemas_data = update_nested(schemas_data, data)
        return schemas_data

    for http_method in [attr for attr in dir(cls) if attr in http_methods]:
        view_func = getattr(cls, http_method)
        class_name = cls.__name__ + '.' + http_method.title()

        """For each incoming data given, generate"""
        definitions = {}
        parameters = []
        tags = getattr(cls, 'tags', [])

        view_func_args = function_args(view_func)

        # add view_arg if url_rules exist in class
        if 'view_arg' not in view_func_args and hasattr(cls, 'url_rules'):
            view_func_args['view_arg'] = {'default': None, 'type': dict}

        for arg, val in {arg: val for arg, val in view_func_args.items() if arg in http_path}.items():
            spec = find_specs(find_schemas(http_method.title(), arg, cls.__schema__))
            if arg in ['body']:
                parameter = {
                    'name': arg,
                    'in': 'body',
                    'schema': {
                        '$ref': '#/definitions/' + class_name
                    }
                }
                if 'required' in spec[class_name]:
                    parameter['required'] = True
                parameters.append(parameter)
                definitions.update(spec)
            elif arg in ['view_arg', 'header', 'path', 'query']:
                for f, v in spec[class_name]['properties'].items():
                    parameter = dict(name=f, required=False)
                    parameter['in'] = ('path' if arg == 'view_arg' else arg)
                    parameter['type'] = v['type']
                    if 'required' in spec[class_name] and f in spec[class_name]['required']:
                        parameter['required'] = True
                    if 'default' in spec[class_name]['properties'][f]:
                        parameter['default'] = spec[class_name]['properties'][f]['default']
                    parameters.append(parameter)

        output = list([class_name, class_name, '---'])
        if view_func.__doc__:
            output[1] = view_func.__doc__
        output.append(yaml.safe_dump({'tags': tags}, allow_unicode=True, default_flow_style=False))
        output.append(yaml.safe_dump({'parameters': parameters}, allow_unicode=True, default_flow_style=False))
        if definitions:
            output.append(yaml.safe_dump({'definitions': definitions}, allow_unicode=True, default_flow_style=False))

        setattr(getattr(cls, http_method), '__doc__', '\n'.join(output))

    return cls
