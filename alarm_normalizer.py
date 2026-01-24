from datetime import datetime, timezone, timedelta
import pytz
from datetime import datetime
from severity_mapper import map_severity
from object_parser import parse_affected_object
from alarm_filters import should_drop_alarm
from alarm_lifecycle import get_active_power_issues
from alarm_lifecycle import get_active_los_alarms


# -------------------------------
# Time conversion
# -------------------------------
LOCAL_TZ = pytz.timezone("Asia/Dhaka")

def utc_ms_to_local_iso(ts):
    """Convert epoch ms → ISO string in Asia/Dhaka (+6) timezone."""
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
        utc_dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
        local_dt = utc_dt.astimezone(LOCAL_TZ)
        return local_dt.isoformat()  # e.g. 2026-01-23T17:05:10+06:00
    except Exception:
        return None


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
    Normalize Nokia NSP/NFMT alarm notification.
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

    alarm_name = alarm.get("alarmName")
    specific_problem = alarm.get("specificProblem")
    probable_cause = alarm.get("probableCause")
    ne_name = alarm.get("neName")
    ne_id = alarm.get("neId")
    source = alarm.get("sourceType")
    object_type = alarm.get("affectedObjectType")

    severity_raw = alarm.get("severity")
    severity = map_severity(severity_raw, specific_problem)

    # 🔑 Fetch correlation context BEFORE filtering
    active_power_issues = get_active_power_issues()

    # new helper for LOS-OCH correlation
    active_los_alarms = get_active_los_alarms()

    if should_drop_alarm(
        alarm_name=alarm_name,
        specific_problem=specific_problem,
        probable_cause=probable_cause,
        ne_name=ne_name,
        ne_id=ne_id,
        source=source,
        object_type=object_type,
        severity=severity,
        affected_object_name=alarm.get("affectedObjectName"),
        first_detected=epoch_ms_to_utc(alarm.get("firstTimeDetected")),
        active_power_issues=active_power_issues,
        active_los_alarms=active_los_alarms,  # ✅ ADD THIS LINE
    ):
        return None
    
    

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

        "first_detected": utc_ms_to_local_iso(
            alarm.get("firstTimeDetected")
        ),
        "last_detected": utc_ms_to_local_iso(
            alarm.get("lastTimeDetected")
        ),

        "acknowledged": alarm.get("acknowledged", False),
        "service_affecting": alarm.get("serviceAffecting"),
        "implicitly_cleared": alarm.get("implicitlyCleared", False),
    }
