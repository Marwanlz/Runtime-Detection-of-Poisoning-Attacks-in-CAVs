from flask import Flask, request, jsonify
import json
import os
import time
from collections import Counter

from correlation import detect_cross_vehicle_correlation
from corroboration import PERCEPTION_EVENT_TYPE, PerceptionCorroboration

from rules import apply_rules
from prioritization import assign_priority
from lightweight_ai import compute_anomaly_score
from shared.utils import normalize_event

app = Flask(__name__)

LOG_DIR = "logs"
EVENTS_LOG_FILE = os.path.join(LOG_DIR, "received_events.json")
CORRELATED_LOG_FILE = os.path.join(LOG_DIR, "correlated_alerts.json")
DIVERGING_LOG_FILE = os.path.join(LOG_DIR, "diverging_vehicle.json")

os.makedirs(LOG_DIR, exist_ok=True)

# Save the log every 200 events to avoid quadratic overhead.
SAVE_EVERY = 200

received_events = []
correlated_alerts = []

legacy_events = []

# Cross-vehicle corroboration of the perception events
corroboration = PerceptionCorroboration()
diverging_report = {}

previous_timestamps = {}

def save_json_to_file(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Edge SIEM is running"}), 200


@app.route("/events", methods=["POST"])
def receive_event():
    global previous_timestamps

    event = request.get_json()

    if not event:
        return jsonify({"error": "No JSON payload received"}), 400

    mode = event.get("mode", "baseline")

    if mode == "baseline":
        vehicle_id = event["vehicle_id"]
        prev_ts = previous_timestamps.get(vehicle_id)

        event = apply_rules(event)
        event = normalize_event(event, prev_ts)

        score, is_anomalous = compute_anomaly_score(event)
        event["anomaly_score"] = score
        event["ai_anomaly"] = is_anomalous

        event = assign_priority(event)

        decision_timestamp = time.time()
        event["decision_timestamp"] = decision_timestamp
        event["detection_latency"] = decision_timestamp - event["timestamp"]

        previous_timestamps[vehicle_id] = event["timestamp"]

    elif mode == "hybrid":
        # event processed in onboard SIEM
        pass

    received_events.append(event)

    if len(received_events) % SAVE_EVERY == 0:
        save_json_to_file(EVENTS_LOG_FILE, received_events)

    # Perception events are corroborated by object.
    if event.get("event_type") == PERCEPTION_EVENT_TYPE:
        report = corroboration.add_event(event)

        current = corroboration.ranking()

        if current:
            diverging_report.clear()
            diverging_report.update(current)
            save_json_to_file(DIVERGING_LOG_FILE, diverging_report)


        if report:
            print(f"[EDGE] Corroboration on "
                  f"{report['objects_with_majority']} objects with a majority "
                  f"({report['objects_without_majority']} without)")

            for vehicle_id, rate in report["disagreement_rate_per_vehicle"]:
                print(f"[EDGE]   {vehicle_id:<10} rate={rate:.2%} "
                      f"objects={report['comparisons_per_vehicle'][vehicle_id]}")

            print(f"[EDGE] Flagged: {', '.join(report['flagged_vehicles'])} "
                  f"(highest={report['highest_rate']:.2%}, "
                  f"largest_gap={report['largest_gap']:.2%}, "
                  f"baseline_gap={report['baseline_gap']:.2%})")

    else:
        legacy_events.append(event)

        new_alerts = detect_cross_vehicle_correlation(
            legacy_events,
            correlated_alerts,
            time_window=0.005
        )

        if new_alerts:
            correlated_alerts.extend(new_alerts)
            save_json_to_file(CORRELATED_LOG_FILE, correlated_alerts)

            for alert in new_alerts:
                print(
                    "[EDGE] Correlated alert detected: "
                    f"vehicles={alert['vehicles']} "
                    f"event_count={alert['event_count']} "
                    f"window={alert['time_window_seconds']}s"
                )

    print(f"[EDGE] Event received: {event}")

    return jsonify(
        {
            "status": "received",
            "total_events": len(received_events),
            "correlated_alerts": len(correlated_alerts),
            "flagged_vehicles": diverging_report.get("flagged_vehicles"),
        }
    ), 200


@app.route("/stats", methods=["GET"])
def get_stats():
    save_json_to_file(EVENTS_LOG_FILE, received_events)

    report = corroboration.ranking()
    if report:
        save_json_to_file(DIVERGING_LOG_FILE, report)

    total_events = len(received_events)

    events_per_vehicle = Counter(
        event.get("vehicle_id", "unknown") for event in received_events
    )

    events_per_type = Counter(
        event.get("event_type", "unknown") for event in received_events
    )

    timestamps = [
        event.get("timestamp") for event in received_events if "timestamp" in event
    ]

    stats = {
        "total_events": total_events,
        "events_per_vehicle": dict(events_per_vehicle),
        "events_per_type": dict(events_per_type),
        "timestamps": timestamps,
        "correlated_alerts_count": len(correlated_alerts),
        "correlated_alerts": correlated_alerts,
        "corroboration": corroboration.ranking(),
    }

    return jsonify(stats), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)