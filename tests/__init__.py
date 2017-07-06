from flask import Flask

from tests.apps.api_v1 import api

app = Flask(__name__)
app.register_blueprint(api)


@app.route("/")
def hello():
    print(app.url_map)
    return ""


if __name__ == '__main__':
    app.run(host='0.0.0.0')
