import pandas as pd
import pickle

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier

df = pd.read_csv(
    "dataset/text_dataset_2000_rows.csv"
)

X = df["text"]
y = df["label"]

model = Pipeline([
    (
        "tfidf",
        TfidfVectorizer()
    ),
    (
        "rf",
        RandomForestClassifier(
            n_estimators=200,
            random_state=42
        )
    )
])

model.fit(X, y)

pickle.dump(
    model,
    open("text_model.pkl", "wb")
)

print("Text Model Trained")