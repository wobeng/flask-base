from setuptools import setup

setup(
    name='flask-base',
    version='1.0.0',
    packages=['flask_base'],
    url='https://github.com/wobeng/flask-base',
    license='',
    author='wobeng',
    author_email='wobeng@yblew.com',
    description='flask base app',
    install_requires=[
        'Flask',
        'marshmallow',
        'simplejson',
        'flasgger',
        'apispec',
        'apispec-webframeworks @ git+https://git@github.com/marshmallow-code/apispec-webframeworks.git@master#egg=apispec-webframeworks',
        'PyYAML',
        'flask-cors',
        'bcrypt',
        'python-dateutil',
        'phonenumbers',
        'requests',
        'validators',
        'validate_email',
        'jsonschema==3.0.0a3',
        'pytz',
        'pynamodb @ git+https://github.com/pynamodb/PynamoDB#egg=pynamodb'
    ]
)
