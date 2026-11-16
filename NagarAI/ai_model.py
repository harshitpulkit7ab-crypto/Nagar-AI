from pathlib import Path
import pickle
import re
import math

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "complaint_classifier.pkl"


FALLBACK_KEYWORDS = {
    "Road Damage": ["pothole", "road", "street", "crack", "road damage", "broken road"],
    "Streetlight": ["street light", "streetlight", "lamp", "light not working", "dark road"],
    "Garbage": ["garbage", "waste", "trash", "dustbin", "litter", "rubbish"],
    "Drainage": ["drain", "drainage", "sewage", "overflow", "waterlogging", "sewer"],
    "Water Supply": ["water", "pipeline", "tap", "water supply", "leakage", "low pressure"],
    "Public Property": ["park", "bench", "toilet", "playground", "public building"],
}


def _fallback_predict(text):
    t = text.lower()
    scores = {}
    for category, words in FALLBACK_KEYWORDS.items():
        scores[category] = sum(1 for w in words if w in t)

    best = max(scores, key=scores.get)
    top_score = scores[best]
    if top_score == 0:
        return "General Civic Issue", 0.35

    confidence = min(0.95, 0.55 + top_score * 0.10)
    return best, confidence


def predict_category(text):
    """Predict category using the trained model; fall back to keywords if unavailable."""
    if MODEL_PATH.exists():
        try:
            with open(MODEL_PATH, "rb") as f:
                model = pickle.load(f)
            prediction = model.predict([text])[0]
            probabilities = model.predict_proba([text])[0]
            confidence = float(max(probabilities))
            return prediction, confidence
        except Exception:
            pass

    return _fallback_predict(text)


def calculate_priority(severity, public_impact, affected_people):
    """
    Transparent scoring system:
    severity: 1-5
    public_impact: 1-5
    affected_people: 1-5
    """
    score = (
        severity * 0.40 +
        public_impact * 0.35 +
        affected_people * 0.25
    )

    if score >= 4.2:
        priority = "Critical"
    elif score >= 3.3:
        priority = "High"
    elif score >= 2.2:
        priority = "Medium"
    else:
        priority = "Low"

    return priority, round(score, 2)
