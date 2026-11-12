EVENT_TYPE_MAPPING = {
    "normal_can_event": 0,
    "normal_v2x_event": 1,
    "local_network_anomaly": 2,
    "abnormal_bsm_event": 3,
    "normal_perception_event": 4,
    "abnormal_perception_event": 5
}

# Fields carried by the perception events. The edge SIEM needs them to group the events of a same object and compare the classes announced by the vehicles.
PAYLOAD_FIELDS = ["zone_id", "object_id", "class"]


def normalize_event(event, previous_timestamp=None):
    current_timestamp = event["timestamp"]

    event_type = event["event_type"]
    event_type_code = EVENT_TYPE_MAPPING.get(event_type, -1)

    if previous_timestamp is None:
        inter_arrival_time = 0.0
    else:
        inter_arrival_time = current_timestamp - previous_timestamp

    # Normalize event into a structured format
    normalized_event = {
        "event_id": event["event_id"],
        "vehicle_id": event["vehicle_id"],
        "timestamp": current_timestamp,
        "event_type": event_type,
        "event_type_code": event_type_code,
        "inter_arrival_time": inter_arrival_time,
        "rule_flag": event.get("rule_flag", False),
        "mode": event.get("mode")
    }
        
    for field in PAYLOAD_FIELDS:
        if field in event:
            normalized_event[field] = event[field]

    return normalized_event