from datetime import datetime
from severity_mapper import map_severity
from object_parser import parse_affected_object
from alarm_filters import should_drop_alarm


def epoch_ms_to_utc(ts):
    if ts is None:
        return None

    if isinstance(ts, dict):
        ts = (
            ts.get("value")
            or ts.get("milliseconds")
            or (ts.get("seconds", 0) * 1000)
        )

    if isinstance(ts, str):
        if not ts.isdigit():
            return None
        ts = int(ts)

    if not isinstance(ts, (int, float)):
        return None

    try:
        return datetime.utcfromtimestamp(ts / 1000).isoformat() + "Z"
    except Exception:
        return None


def normalize_alarm(event):
    """
    Normalize Nokia NSP/NFMT alarm notification into a stable structure.
    """

    notif = event.get("data", {}).get("ietf-restconf:notification", {})

    alarm = None
    event_type = None

    for k, v in notif.items():
        if k.startswith("nsp-fault:"):
            event_type = k.replace("nsp-fault:", "")
            alarm = v
            break

    if not alarm or not isinstance(alarm, dict):
        return None

    # -------------------------------
    # Extract core fields
    # -------------------------------
    alarm_name = alarm.get("alarmName")
    specific_problem = alarm.get("specificProblem")
    probable_cause = alarm.get("probableCause")
    ne_name = alarm.get("neName")
    ne_id = alarm.get("neId")
    source = alarm.get("sourceType")
    object_type = alarm.get("affectedObjectType")

    # -------------------------------
    # Resolve severity BEFORE filtering
    # -------------------------------
    severity_raw = alarm.get("severity")
    severity = map_severity(severity_raw, specific_problem)

    # -------------------------------
    # FIXED: keyword arguments (CORRECT)
    # -------------------------------
    if should_drop_alarm(
        alarm_name=alarm_name,
        specific_problem=specific_problem,
        probable_cause=probable_cause,
        ne_name=ne_name,
        ne_id=ne_id,
        source=source,
        object_type=object_type,
        severity=severity,
    ):
        return None

    # -------------------------------
    # Normalized output
    # -------------------------------
    return {
        "event_type": event_type,
        "event_time": notif.get("eventTime"),

        "alarm_id": alarm.get("objectId"),
        "alarm_name": alarm_name,
        "specific_problem": specific_problem,
        "probable_cause": probable_cause,

        "ne_name": ne_name,
        "ne_id": ne_id,
        "source": source,

        "severity_raw": severity_raw,
        "severity": severity,

        "affected_object": alarm.get("affectedObject"),
        "affected_object_name": alarm.get("affectedObjectName"),
        "object_type": object_type,
        "object_details": parse_affected_object(
            alarm.get("affectedObject")
        ),

        "first_detected": epoch_ms_to_utc(
            alarm.get("firstTimeDetected")
        ),
        "last_detected": epoch_ms_to_utc(
            alarm.get("lastTimeDetected")
        ),

        "acknowledged": alarm.get("acknowledged", False),
        "service_affecting": alarm.get("serviceAffecting"),
        "implicitly_cleared": alarm.get("implicitlyCleared", False),
    }
