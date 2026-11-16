from pathlib import Path
import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "complaints.csv"
MODEL_PATH = BASE_DIR / "models" / "complaint_classifier.pkl"

df = pd.read_csv(DATA_PATH)

X = df["complaint"].astype(str)
y = df["category"].astype(str)

model = Pipeline([
    ("tfidf", TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        min_df=1
    )),
    ("classifier", LogisticRegression(max_iter=3000))
])

model.fit(X, y)

MODEL_PATH.parent.mkdir(exist_ok=True)
with open(MODEL_PATH, "wb") as f:
    pickle.dump(model, f)

print(f"Model trained on {len(df)} examples.")
print(f"Saved to: {MODEL_PATH}")
