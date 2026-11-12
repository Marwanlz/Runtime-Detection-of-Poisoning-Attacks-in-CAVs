def detect_cross_vehicle_correlation(received_events, existing_alerts, time_window=0.005):

    critical_events = [
        e for e in received_events
        if e.get("priority") == "critical"
    ]

    critical_events.sort(key=lambda e: e.get("timestamp", 0))

    new_alerts = []

    for i, base_event in enumerate(critical_events):

        base_time = base_event.get("timestamp", 0)
        base_type = base_event.get("event_type")

        involved_events = [base_event]
        involved_vehicles = {base_event.get("vehicle_id")}

        for j in range(i + 1, len(critical_events)):

            candidate = critical_events[j]

            if candidate.get("event_type") != base_type:
                continue

            if candidate.get("timestamp", 0) - base_time <= time_window:

                involved_events.append(candidate)
                involved_vehicles.add(candidate.get("vehicle_id"))

            else:
                break

        # Two or more vehicles reporting the same event type within the time window
        if len(involved_vehicles) >= 2:

            event_ids = sorted(e["event_id"] for e in involved_events)

            already_exists = any(
                sorted(alert["event_ids"]) == event_ids
                for alert in existing_alerts + new_alerts
            )

            if not already_exists:

                alert = {
                    "alert_type": "cross_vehicle_correlated_alert",
                    "event_type": base_type,
                    "vehicles": sorted(list(involved_vehicles)),
                    "event_ids": event_ids,
                    "event_count": len(involved_events),
                    "first_timestamp": involved_events[0]["timestamp"], # first event
                    "last_timestamp": involved_events[-1]["timestamp"], # last event
                    "time_window_seconds": time_window
                }

                new_alerts.append(alert)

    return new_alerts