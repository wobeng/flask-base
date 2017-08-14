from flask import redirect

from flask_base.app import init_api
from tests.apps.api_v1 import api

app = init_api(__name__)
app.register_blueprint(api)


@app.route('/')
def index():
    return redirect('/apidocs')


if __name__ == '__main__':
    app.run(host='0.0.0.0')
