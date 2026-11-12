#Combine rule-based detection and ai_anomaly
def assign_priority(event):

    if event["rule_flag"] or event["ai_anomaly"]:
        event["priority"] = "critical"
    else:
        event["priority"] = "low"

    return event