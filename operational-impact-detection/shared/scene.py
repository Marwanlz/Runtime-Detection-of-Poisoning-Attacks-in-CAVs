import json
import os
import random

# Classes of the SECRYPT classification model
CLASSES = ["other", "chair"]

# Confusion matrices measured in the SECRYPT paper, indexed by the poisoning rate of the training set.
GAN_AUGMENTED = False

MATRICES_WITHOUT_GAN = {
    0.0: [[294, 6], [6, 294]],
    0.1: [[296, 4], [21, 279]],
    0.2: [[296, 4], [32, 268]],
    0.4: [[297, 3], [40, 260]]
}

MATRICES_WITH_GAN = {
    0.0: [[299, 1], [43, 257]],
    0.1: [[300, 0], [89, 211]],
    0.2: [[300, 0], [103, 197]],
    0.4: [[300, 0], [129, 171]]
}

CONFUSION_MATRICES = MATRICES_WITH_GAN if GAN_AUGMENTED else MATRICES_WITHOUT_GAN

# Poisoning rate of each vehicle. 
POISONING_RATE = {
    "vehicle1": 0.0,
    "vehicle2": 0.0,
    "vehicle3": 0.0,
    "vehicle4": 0.0,
    "vehicle5": 0.0,
    "vehicle6": 0.0,
    "vehicle7": 0.0,
    "vehicle8": 0.4,
    "vehicle9": 0.0,
    "vehicle10": 0.0
}

N_VEHICLES = 10
N_OBJECTS = 1000
OBJECTS_PER_VEHICLE = 600
ZONE_ID = "z_01"
SEED = 42

VEHICLES = [f"vehicle{v}" for v in range(1, N_VEHICLES + 1)]

MESSAGES_FILE = os.path.join(os.path.dirname(__file__), "perception_messages.json")


# What the vehicles hear on the V2X channel. 
def load_messages():
    with open(MESSAGES_FILE, encoding="utf-8") as f:
        return json.load(f)


def vehicle_rng(vehicle_id):
    return random.Random(SEED + int(vehicle_id.replace("vehicle", "")))


# Share of the objects of each true class that the model gets wrong
def error_rates(vehicle_id):
    matrix = CONFUSION_MATRICES[POISONING_RATE.get(vehicle_id, 0.0)]

    return {
        true_class: (sum(row) - row[index]) / sum(row)
        for index, (true_class, row) in enumerate(zip(CLASSES, matrix))
    }


# The objects of the scene, and which vehicles see each of them
def build_scene():
    rng = random.Random(SEED)

    scene = [
        {"object_id": f"obj_{i:05d}", "true_class": "chair", "seen_by": []}
        for i in range(N_OBJECTS)
    ]

    for vehicle_id in VEHICLES:
        for index in rng.sample(range(N_OBJECTS), OBJECTS_PER_VEHICLE):
            scene[index]["seen_by"].append(vehicle_id)

    return scene


# What one vehicle announces.
def classify(scene, vehicle_id):
    rng = vehicle_rng(vehicle_id)
    rates = error_rates(vehicle_id)
    announced = {}

    for true_class in CLASSES:
        pool = [
            o["object_id"] for o in scene
            if vehicle_id in o["seen_by"] and o["true_class"] == true_class
        ]

        wrong = set(rng.sample(pool, round(rates[true_class] * len(pool))))
        other = CLASSES[1 - CLASSES.index(true_class)]

        for object_id in pool:
            announced[object_id] = other if object_id in wrong else true_class

    return announced


# perception_messages.json: one entry per object, the class announced by each vehicle
def build_messages():
    scene = build_scene()
    messages = {}

    for vehicle_id in VEHICLES:
        for object_id, predicted in classify(scene, vehicle_id).items():
            entry = messages.setdefault(
                object_id, {"zone_id": ZONE_ID, "classes": {}}
            )
            entry["classes"][vehicle_id] = predicted

    return messages


if __name__ == "__main__":
    messages = build_messages()

    with open(MESSAGES_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2)

    contested = sum(
        1 for e in messages.values() if len(set(e["classes"].values())) > 1
    )
    observers = [len(e["classes"]) for e in messages.values()]

    print("Perception messages saved to:", MESSAGES_FILE)
    print("Objects:", len(messages))
    print("Objects seen by each vehicle:", OBJECTS_PER_VEHICLE)
    print("Vehicles per object: min", min(observers),
          "max", max(observers),
          "mean", round(sum(observers) / len(observers), 2))
    print("Objects with a disagreement:", contested)