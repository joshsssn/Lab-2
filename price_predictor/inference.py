
import os
import tensorflow as tf
import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'saved_model.keras')
_model = None

def load_model():
    global _model
    if _model is None:
        if os.path.exists(MODEL_PATH):
            _model = tf.keras.models.load_model(MODEL_PATH)
        else:
            raise FileNotFoundError(f"Model not found at {MODEL_PATH}. Please run train.py first.")
    return _model

def predict_price(title):
    model = load_model()
    # Model expects a tensor or numpy array
    prediction = model.predict(tf.constant([title]), verbose=0)
    return float(prediction[0][0])

if __name__ == "__main__":
    # Test
    print(predict_price("Gold Rolex Watch"))
    print(predict_price("Broken old generic watch parts"))
