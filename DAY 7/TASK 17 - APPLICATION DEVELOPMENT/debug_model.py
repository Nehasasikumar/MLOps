from app import load_model
import numpy as np


def get_predictor_and_encoder(model):
    predictor = None
    encoder = None
    if isinstance(model, dict):
        predictor = model.get('text_model')
        encoder = model.get('text_encoder')
        if predictor is None:
            for v in model.values():
                if hasattr(v, 'predict'):
                    predictor = v
                    break
    else:
        predictor = model
    return predictor, encoder


if __name__ == '__main__':
    model = load_model()
    predictor, encoder = get_predictor_and_encoder(model)
    print('Predictor type:', type(predictor))
    if encoder is not None:
        print('Label encoder classes:', list(encoder.classes_))
    try:
        classes = getattr(predictor, 'classes_', None)
        print('Predictor.classes_:', classes)
    except Exception as e:
        print('Could not read predictor.classes_', e)

    samples = [
        'machine is awesome',
        'machine broken',
        'needs repair',
        'operating perfectly',
        'service required immediately'
    ]

    for s in samples:
        try:
            pred = predictor.predict([s])[0]
            out = f"Input: {s!r} -> prediction: {pred}"
            if hasattr(predictor, 'predict_proba'):
                probs = predictor.predict_proba([s])[0]
                out += ' probs=' + np.array2string(probs, precision=3)
            if encoder is not None and hasattr(encoder, 'inverse_transform'):
                try:
                    label = encoder.inverse_transform([int(pred)])[0]
                    out += f" label='{label}'"
                except Exception:
                    pass
            print(out)
        except Exception as e:
            print('Error predicting for', s, e)
