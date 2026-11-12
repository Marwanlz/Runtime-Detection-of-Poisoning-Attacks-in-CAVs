# Each event is generated, analyzed locally, and forwarded to the edge SIEM (if critical)
import json
import os
import time
import requests

from event_generator import generate_stream
from rules import apply_rules
from shared.utils import normalize_event
from lightweight_ai import compute_anomaly_score
from prioritization import assign_priority

MODE = os.getenv("MODE", "hybrid").lower()

EDGE_SIEM_URL = "http://edge_siem:5000/events"

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "events.json")

os.makedirs(LOG_DIR, exist_ok=True)


def save_event_locally(event):
    existing_events = []

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            try:
                existing_events = json.load(f)
            except json.JSONDecodeError:
                existing_events = []

    existing_events.append(event)

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(existing_events, f, indent=2)


def send_event_to_central(event):
    try:
        response = requests.post(EDGE_SIEM_URL, json=event, timeout=5)
        print(f"[VEHICLE2] Sent event {event['event_id']} - Status: {response.status_code}")
    except requests.RequestException as e:
        print(f"[VEHICLE2] Failed to send event: {e}")


def main():
    time.sleep(5)

    previous_timestamp = None

        # One event per second: second N carries object N of the scene
    for event in generate_stream(vehicle_id="vehicle2"):
        event["timestamp"] = time.time()
        event["mode"] = MODE
        
        # Send generated events to the EDGE SIEM
        if MODE == "baseline":
            print(
                f"[VEHICLE2][BASELINE] Event {event['event_id']} "
                f"type={event['event_type']} generated and forwarded to edge SIEM"
            )

            save_event_locally(event)
            send_event_to_central(event)

        elif MODE == "hybrid":
            event = apply_rules(event)
            event = normalize_event(event, previous_timestamp)

            score, is_anomalous = compute_anomaly_score(event)
            event["anomaly_score"] = score
            event["ai_anomaly"] = is_anomalous

            event = assign_priority(event)

            event["decision_timestamp"] = time.time()
            event["detection_latency"] = event["decision_timestamp"] - event["timestamp"]

            previous_timestamp = event["timestamp"]

            print(
                f"[VEHICLE2][HYBRID] Event {event['event_id']} "
                f"type={event['event_type']} "
                f"rule_flag={event['rule_flag']} "
                f"score={event['anomaly_score']:.5f} "
                f"ai_anomaly={event['ai_anomaly']} "
                f"priority={event['priority']}"
            )

            save_event_locally(event)
            # send only critical events
            if event["priority"] == "critical":
                send_event_to_central(event)
            else:
                print(f"[VEHICLE2] Event {event['event_id']} processed locally") # for low priority events

        time.sleep(1)


if __name__ == "__main__":
    main()