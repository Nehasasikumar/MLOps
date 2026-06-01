import os
import pickle
import sys
import types
from flask import Flask, request, jsonify, render_template
try:
    from flask_cors import CORS
except Exception:
    CORS = None

app = Flask(__name__)
if CORS is not None:
    CORS(app)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "machine_anomaly_model.pkl")


def load_model(path=MODEL_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model file not found at {path}. Place machine_anomaly_model.pkl next to app.py")
    # Try joblib first (some users save with joblib) then pickle
    # helper to attempt load with pickle
    def _load_with_pickle():
        with open(path, "rb") as f:
            return pickle.load(f)

    try:
        import joblib

        try:
            return joblib.load(path)
        except ModuleNotFoundError as e:
            # Common issue: pickle references a module named 'Pipeline'
            msg = str(e)
            if "No module named 'Pipeline'" in msg or e.name == 'Pipeline':
                try:
                    # create a stub module named 'Pipeline' that exposes sklearn.pipeline.Pipeline
                    import sklearn.pipeline as _skpipeline

                    mod = types.ModuleType('Pipeline')
                    setattr(mod, 'Pipeline', _skpipeline.Pipeline)
                    sys.modules['Pipeline'] = mod
                except Exception:
                    pass
                return joblib.load(path)
            raise
    except Exception:
        # fallback to pickle.load with same compatibility attempt
        try:
            return _load_with_pickle()
        except ModuleNotFoundError as e:
            msg = str(e)
            if "No module named 'Pipeline'" in msg or e.name == 'Pipeline':
                try:
                    import sklearn.pipeline as _skpipeline

                    mod = types.ModuleType('Pipeline')
                    setattr(mod, 'Pipeline', _skpipeline.Pipeline)
                    sys.modules['Pipeline'] = mod
                except Exception:
                    pass
                return _load_with_pickle()
            raise


model = None

# normalized handles after loading
predictor = None
label_encoder = None


def preprocess_text(text: str):
    """Adapt this function to match how your model was trained.
    Many text models expect tokenization, lowercasing, or a vectorizer object.
    If your saved object is a pipeline (vectorizer + estimator), no changes needed.
    """
    return text


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/predict", methods=["POST", "OPTIONS"])
def predict():
    # handle CORS preflight
    if request.method == "OPTIONS":
        return ("", 204)
    global model
    global predictor, label_encoder
    if model is None:
        try:
            model = load_model()
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # If the loaded object is a dict (your notebook saved a combined dict),
    # extract the text pipeline and label encoder
    if predictor is None:
        if isinstance(model, dict):
            # prefer text_model key
            if "text_model" in model:
                predictor = model["text_model"]
            else:
                # if a single estimator accidentally saved inside dict
                # try to locate a pipeline-like object
                for v in model.values():
                    if hasattr(v, "predict"):
                        predictor = v
                        break

            label_encoder = model.get("text_encoder") or model.get("text_encoder")
        else:
            predictor = model

    data = request.get_json(silent=True) or {}
    text = data.get("text")
    # fallback to form data (when client sends FormData)
    if text is None:
        text = request.form.get("text")
    if text is None:
        return jsonify({"success": False, "error": "Missing 'text' in request body"}), 400

    x = preprocess_text(text)

    # quick rule-based overrides for very explicit sentiment keywords
    try:
        low = x.lower()
        positive_keywords = ["awesome", "great", "excellent", "working fine", "operating perfectly", "no issues", "good", "ok", "okay", "running well"]
        negative_keywords = ["broken", "not working", "failed", "error", "fault", "needs repair"]
        if any(k in low for k in positive_keywords):
            # map to numeric class for 'Normal' if possible
            numeric = None
            if label_encoder is not None and hasattr(label_encoder, 'classes_'):
                try:
                    idx = list(label_encoder.classes_).index('Normal')
                    numeric = int(idx)
                except Exception:
                    numeric = 0
            else:
                numeric = 0
            return jsonify({"success": True, "prediction": str(numeric), "prediction_label": "Normal", "probability": 1.0})
        if any(k in low for k in negative_keywords):
            numeric = None
            if label_encoder is not None and hasattr(label_encoder, 'classes_'):
                try:
                    idx = list(label_encoder.classes_).index('Repair Required')
                    numeric = int(idx)
                except Exception:
                    numeric = 1
            else:
                numeric = 1
            return jsonify({"success": True, "prediction": str(numeric), "prediction_label": "Repair Required", "probability": 1.0})
    except Exception:
        pass

    try:
        # Many models accept an array-like of samples
        if predictor is None:
            return jsonify({"success": False, "error": "No predictor available"}), 500

        pred = predictor.predict([x])
        label = pred[0]
    except Exception as e:
        return jsonify({"success": False, "error": "Model prediction failed: " + str(e)}), 500

    response = {"success": True, "prediction": str(label)}

    # If model supports predict_proba, include probability for the predicted class
    try:
        if hasattr(predictor, "predict_proba"):
            probs = predictor.predict_proba([x])[0]
            import numpy as _np

            classes = getattr(predictor, "classes_", None)
            if classes is not None:
                # if label_encoder exists, classes_ are numeric; map accordingly
                try:
                    idx = int(_np.where(classes == label)[0][0])
                    response["probability"] = float(probs[idx])
                except Exception:
                    response["probabilities"] = probs.tolist()
            else:
                response["probabilities"] = probs.tolist()
    except Exception:
        pass

    # If we have a label encoder, try to inverse transform the numeric label
    try:
        if label_encoder is not None and hasattr(label_encoder, "inverse_transform"):
            try:
                inv = label_encoder.inverse_transform([label])[0]
                response["prediction_label"] = str(inv)
            except Exception:
                pass
    except Exception:
        pass

    return jsonify(response)


if __name__ == "__main__":
    try:
        model = load_model()
        print("Model loaded from", MODEL_PATH)
    except Exception as e:
        print("Warning: model not loaded at startup:", e)
    app.run(host="0.0.0.0", port=5000, debug=True)
