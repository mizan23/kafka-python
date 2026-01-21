import psycopg2
import json
from contextlib import contextmanager

# -------------------------------
# Database configuration
# -------------------------------
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "dbname": "nsp",
    "user": "nsp_user",
    "password": "nsp_pass",
}

# -------------------------------
# Connection helper
# -------------------------------
@contextmanager
def get_conn():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# -------------------------------
# SQL
# -------------------------------
UPSERT_ACTIVE_SQL = """
INSERT INTO active_alarms (alarm_id, alarm)
VALUES (%s, %s::jsonb)
ON CONFLICT (alarm_id)
DO UPDATE SET
    alarm = EXCLUDED.alarm,
    last_updated = now();
"""

DELETE_ACTIVE_SQL = """
DELETE FROM active_alarms
WHERE alarm_id = %s
RETURNING alarm;
"""

INSERT_HISTORY_SQL = """
INSERT INTO alarm_history (alarm_id, alarm, cleared_at)
VALUES (%s, %s::jsonb, now());
"""

# -------------------------------
# Lifecycle handler (CORRECT)
# -------------------------------
def handle_alarm_lifecycle(alarm: dict):
    """
    Alarm lifecycle (NSP-correct):

    alarm-create           -> active_alarms
    alarm-change + CLEAR   -> move active -> history
    alarm-change (orphan)  -> ignore
    alarm-delete           -> ignore
    """

    alarm_id = alarm.get("alarm_id")
    event_type = alarm.get("event_type")
    severity = alarm.get("severity")

    # ---------------------------
    # Hard safety guards
    # ---------------------------
    if not alarm_id or not event_type:
        return

    # ---------------------------
    # Ignore deletes completely
    # ---------------------------
    if event_type == "alarm-delete":
        return

    with get_conn() as conn:
        with conn.cursor() as cur:

            # =====================================================
            # CLEAR → move from active → history
            # =====================================================
            if event_type == "alarm-change" and severity == "CLEAR":
                cur.execute(DELETE_ACTIVE_SQL, (alarm_id,))
                row = cur.fetchone()

                # Only move if we actually had an active alarm
                if row and row[0]:
                    cur.execute(
                        INSERT_HISTORY_SQL,
                        (
                            alarm_id,
                            json.dumps(row[0], default=str),
                        ),
                    )
                return

            # =====================================================
            # ONLY alarm-create can create/update active alarms
            # =====================================================
            if event_type != "alarm-create":
                return

            # Must have meaningful data
            if not alarm.get("alarm_name") or not alarm.get("ne_name"):
                return

            cur.execute(
                UPSERT_ACTIVE_SQL,
                (
                    alarm_id,
                    json.dumps(alarm, default=str),
                ),
            )
