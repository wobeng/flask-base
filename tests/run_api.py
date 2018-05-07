from flask_base.app import init_api
from tests.app.api_v1.api import api

app = init_api(name=__name__, title='flask-base-testing')
app.register_blueprint(api)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
