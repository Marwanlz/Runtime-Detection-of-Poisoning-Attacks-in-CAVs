"""
Onboard event generation and edge side corroboration of perception events.

This is the cross-vehicle correlation described in Section 5.2 of the paper: events are 
grouped by object_id, the majority class is established, and each vehicle's class is 
compared with it.
"""

import threading

PERCEPTION_EVENT_TYPE = "abnormal_perception_event"

# The current ranking is printed every time this many objects have been seen
REPORT_EVERY = 1


class PerceptionCorroboration:

    def __init__(self):
        self.votes = {}          # object_id -> {vehicle_id: announced class}

        self.lock = threading.Lock()

    def add_event(self, event):
        if event.get("event_type") != PERCEPTION_EVENT_TYPE:
            return None

        object_id = event.get("object_id")
        vehicle_id = event.get("vehicle_id")
        announced = event.get("class")

        if object_id is None or vehicle_id is None or announced is None:
            return None

        with self.lock:
            known_objects = len(self.votes)
            self.votes.setdefault(object_id, {})[vehicle_id] = announced
            new_object = len(self.votes) > known_objects
            objects_reported = len(self.votes)

        if new_object and objects_reported % REPORT_EVERY == 0:
            return self.ranking()

        return None

    def ranking(self):

        with self.lock:
            snapshot = [dict(votes) for votes in self.votes.values()]

        disagreements = {}
        comparisons = {}
        with_majority = 0
        without_majority = 0

        for votes in snapshot:
            # A single opinion cannot be compared with anything. 
            if len(votes) < 2:
                continue

            counts = {}
            for announced in votes.values():
                counts[announced] = counts.get(announced, 0) + 1

            ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)

            if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
                without_majority += 1
                continue

            majority = ranked[0][0]
            with_majority += 1

            for vehicle_id, announced in votes.items():
                comparisons[vehicle_id] = comparisons.get(vehicle_id, 0) + 1

                if announced != majority:
                    disagreements[vehicle_id] = (
                        disagreements.get(vehicle_id, 0) + 1
                    )

        if not comparisons:
            return None

        rates = {
            vehicle_id: disagreements.get(vehicle_id, 0) / count
            for vehicle_id, count in comparisons.items()
        }

        ordered = sorted(rates.items(), key=lambda kv: kv[1], reverse=True)
        values = [rate for _, rate in ordered]


        gaps = [(values[i] - values[i + 1], -i) for i in range(len(values) - 1)]
        largest_gap, position = max(gaps) if gaps else (0.0, 0)
        cut = -position

        flagged = [vehicle_id for vehicle_id, _ in ordered[:cut + 1]]


        below = values[cut + 1:]
        baseline_gap = max(below) - min(below) if len(below) > 1 else 0.0

        return {
            "objects_reported": len(snapshot),
            "objects_with_majority": with_majority,
            "objects_without_majority": without_majority,
            "disagreement_rate_per_vehicle": ordered,
            "disagreements_per_vehicle": dict(disagreements),
            "comparisons_per_vehicle": dict(comparisons),
            "flagged_vehicles": flagged,
            "highest_rate": values[0],
            "largest_gap": largest_gap,
            "baseline_gap": baseline_gap
        }