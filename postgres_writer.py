import psycopg2
import json
from contextlib import contextmanager
from datetime import datetime

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
# SQL statements
# -------------------------------

UPSERT_ACTIVE_SQL = """
INSERT INTO active_alarms (alarm_id, alarm)
VALUES (%s, %s)
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
VALUES (%s, %s, now());
"""


# -------------------------------
# Main lifecycle handler
# -------------------------------

def handle_alarm_lifecycle(alarm: dict):
    """
    Alarm lifecycle handler:
    - alarm-create   → upsert into active_alarms
    - alarm-change   → update OR move to history if CLEAR
    - alarm-delete   → ignored
    """

    alarm_id = alarm.get("alarm_id")
    event_type = alarm.get("event_type")
    severity = alarm.get("severity")

    if not alarm_id:
        return  # safety guard

    # 🚫 IGNORE alarm-delete completely
    if event_type == "alarm-delete":
        return

    with get_conn() as conn:
        with conn.cursor() as cur:

            # 🔄 CLEAR → move to history
            if event_type == "alarm-change" and severity == "CLEAR":
                cur.execute(DELETE_ACTIVE_SQL, (alarm_id,))
                row = cur.fetchone()

                if row:
                    active_alarm_json = row[0]
                    cur.execute(
                        INSERT_HISTORY_SQL,
                        (alarm_id, active_alarm_json),
                    )
                return

            # ➕ CREATE or UPDATE → active_alarms
            cur.execute(
                UPSERT_ACTIVE_SQL,
                (
                    alarm_id,
                    json.dumps(alarm, default=str),
                ),
            )
