# health metric specific processing

METRIC_LIST = ["blood pressure", "weight", "glucose"]

def deserialize_metric(event):
    if event.event_type[3:] == "blood pressure":
        split_bp = event.description.split("/")
        return {"systolic": int(split_bp[0]), "diastolic": int(split_bp[1])}
    return int(event.description)

def process_health_metric_event_stream(hm_event_stream, tracked_health_metrics):
    print(tracked_health_metrics)
    print(hm_event_stream)
    output_dict = {}
    for event_type in tracked_health_metrics:
        output_dict[event_type] = []
    for event in hm_event_stream:
        event_type = event.event_type[3:]  # get rid of "hm_"
        if event_type in tracked_health_metrics:
            print("in here")
            new_hm_event = {"time": event.event_time, "value": deserialize_metric(event)}
            output_dict[event_type].append(new_hm_event)
    return output_dict