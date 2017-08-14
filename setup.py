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
    dependency_links=[
        'git+ssh://git@github.com/wobeng/py-utils.git@master#egg=py-utils-1.0.0'
    ],
    install_requires=[
        'Flask',
        'marshmallow',
        'simplejson',
        'flasgger',
        'apispec',
        'PyYAML'
    ]
)
