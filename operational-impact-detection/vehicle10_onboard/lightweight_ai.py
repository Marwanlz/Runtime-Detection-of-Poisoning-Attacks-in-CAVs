import os
import numpy as np
import joblib

MODEL_PATH = os.path.join("model", "isolation_forest.pkl")
THRESHOLD_PATH = os.path.join("model", "threshold.npy")

model = joblib.load(MODEL_PATH)
threshold = np.load(THRESHOLD_PATH)

def extract_features(event):

    return [
        event["event_type_code"],
        event["inter_arrival_time"],
        int(event["rule_flag"]), 
    ]


def compute_anomaly_score(event):

    features = extract_features(event)
    score = model.decision_function([features])[0] 
    # A score below the threshold value means anomalous behavior
    is_anomalous = score < threshold  

    return float(score), bool(is_anomalous)