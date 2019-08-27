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
        'apispec-webframeworks',
        'PyYAML',
        'flask-cors'
    ]
)
