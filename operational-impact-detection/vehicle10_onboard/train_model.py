import os
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest

MODEL_DIR = "model"
MODEL_PATH = os.path.join(MODEL_DIR, "isolation_forest.pkl")
THRESHOLD_PATH = os.path.join(MODEL_DIR, "threshold.npy")

# Generate synthetic normal events (event type 0 or 1)
def generate_normal_training_data(n_samples=10000):
    event_type_code = np.random.choice([0, 1], size=n_samples) 
    # around 1 second between events, consistent with app.py sleep(1)
    inter_arrival_time = np.random.uniform(0.8, 1.2, size=n_samples)
    rule_flag = np.zeros(n_samples)

    X = np.column_stack(
        [
            event_type_code,
            inter_arrival_time,
            rule_flag,
        ]
    )

    return X

# We only use normal events
def train_model():
    os.makedirs(MODEL_DIR, exist_ok=True)

    X_train = generate_normal_training_data()

    model = IsolationForest(
        n_estimators=100,
        contamination="auto",
        random_state=42
    )

    model.fit(X_train)

    normal_scores = model.decision_function(X_train)
    # The threshold is set at the 5th percentile of normal scores
    threshold = np.percentile(normal_scores, 5) 
    joblib.dump(model, MODEL_PATH)
    np.save(THRESHOLD_PATH, threshold)

    print("Model saved to:", MODEL_PATH)
    print("Threshold saved to:", THRESHOLD_PATH)
    print("Threshold value:", threshold)


if __name__ == "__main__":
    train_model()