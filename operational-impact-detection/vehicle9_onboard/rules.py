def apply_rules(event):
    rule_flag = False

    if event["event_type"] == "local_network_anomaly":
        rule_flag = True

    if event["event_type"] == "abnormal_bsm_event":
        rule_flag = True

    # A disagreement on an object has to be forwarded: the edge SIEM is the only place where the messages of several vehicles can be compared
    if event["event_type"] == "abnormal_perception_event":
        rule_flag = True

    event["rule_flag"] = rule_flag

    return event