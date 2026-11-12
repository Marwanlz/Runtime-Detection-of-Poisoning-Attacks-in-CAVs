import random
import time
import uuid

from shared.scene import load_messages

EVENT_TYPES = [
    "normal_can_event",
    "normal_v2x_event",
    "local_network_anomaly",
    "abnormal_bsm_event"
]

EVENT_WEIGHTS = [0.7, 0.2, 0.05, 0.05]

# The two event types added by the extension, one normal and one abnormal.
NORMAL_PERCEPTION = "normal_perception_event"
ABNORMAL_PERCEPTION = "abnormal_perception_event"

N_EVENTS = 1000


# generate events (4 types)
def generate_event(vehicle_id="vehicle1"):
    event_type = random.choices(EVENT_TYPES, weights=EVENT_WEIGHTS, k=1)[0]

    event = {
        "event_id": str(uuid.uuid4()),
        "vehicle_id": vehicle_id,
        "timestamp": time.time(),
        "event_type": event_type
    }

    return event


# What the vehicle reports about one object it sees
def perception_event(vehicle_id, object_id, entry, event_type):
    return {
        "event_id": str(uuid.uuid4()),
        "vehicle_id": vehicle_id,
        "timestamp": time.time(),
        "event_type": event_type,
        "zone_id": entry["zone_id"],
        "object_id": object_id,
        "class": entry["classes"][vehicle_id]
    }


# One event per second: second N carries object N of the scene
def generate_stream(vehicle_id="vehicle1"):
    messages = load_messages()

    stream = []

    for object_id in sorted(messages):
        entry = messages[object_id]
        classes = entry["classes"]

        # Object out of sight: ordinary traffic of the original PoC
        if vehicle_id not in classes:
            stream.append(generate_event(vehicle_id))

        # The vehicles that see it do not agree on its class
        elif len(set(classes.values())) > 1:
            stream.append(
                perception_event(vehicle_id, object_id, entry,
                                 ABNORMAL_PERCEPTION)
            )

        # They all agree: the observation stays on board
        else:
            stream.append(
                perception_event(vehicle_id, object_id, entry,
                                 NORMAL_PERCEPTION)
            )

    while len(stream) < N_EVENTS:
        stream.append(generate_event(vehicle_id))

    return stream