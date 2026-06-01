from flask import Flask
from flask import request
from flask import jsonify

from flask_cors import CORS

from predict import predict_machine

app = Flask(__name__)

CORS(app)

@app.route("/predict", methods=["POST"])

def predict():

    data = request.json

    text = data["message"]

    result = predict_machine(text)

    return jsonify(result)


if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )