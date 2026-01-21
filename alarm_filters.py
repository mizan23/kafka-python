"""
alarm_filters.py

Central place for alarm filtering policy.
Return True  -> DROP alarm
Return False -> KEEP alarm
"""

def should_drop_alarm(
    *,
    alarm_name,
    specific_problem,
    probable_cause,
    ne_name,
    ne_id,
    source,
    object_type,
    severity,
):
    """
    Decide whether an alarm should be dropped.
    Return True  -> DROP
    Return False -> KEEP
    """

    # ✅ Always keep cleared alarms
    if severity == "CLEAR":
        return False

    if (
        # CLI / ZIC login–logout alarms
        (
            isinstance(object_type, str)
            and object_type.startswith("NE")
            and "CLI" in object_type
            and object_type.endswith(("Login", "Logout"))
        )

        or (
            isinstance(probable_cause, str)
            and probable_cause.startswith("NE")
            and probable_cause.endswith(("Login", "Logout"))
        )

        or (
            isinstance(alarm_name, str)
            and object_type.startswith("Indicates")
            and "Threshold" in object_type
            and object_type.endswith("detection")
        )

        or (
            isinstance(alarm_name, str)
            and object_type.startswith("Power")
            and "management" in object_type
            and object_type.endswith("suspended")
        )
        
        or alarm_name == "SR_RESTORED"
        or alarm_name == "SR_MANUAL_SWITCH"
        or alarm_name == "BASELINE"
        

        or alarm_name == "Adjacency Not Found"
        # Security / power / optical noise alarms
        or specific_problem == "SEC_NA"
        or probable_cause in ("OPR", "PWRSUSP")

        # Generic 15-minute threshold alarms
        or (
            isinstance(probable_cause, str)
            and probable_cause.startswith("T-")
            and probable_cause.endswith(("15-MIN", "1-DAY"))
        )

        or (
            isinstance(alarm_name, str)
            and alarm_name.startswith("Quality Threshold Crossed")
            and alarm_name.endswith(("15m", "24h"))
        )

        # Low-importance severities
        or severity in ("WARNING", "INFO")
    ):
        return True

    return False
