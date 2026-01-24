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
# Lifecycle handler
# -------------------------------
def handle_alarm_lifecycle(alarm: dict):
    """
    alarm-create         -> active_alarms
    alarm-change + CLEAR -> history
    alarm-delete         -> ignored
    """

    alarm_id = alarm.get("alarm_id")
    event_type = alarm.get("event_type")
    severity = alarm.get("severity")

    if not alarm_id or not event_type:
        return

    if event_type == "alarm-delete":
        return

    with get_conn() as conn:
        with conn.cursor() as cur:

            if event_type == "alarm-change" and severity == "CLEAR":
                cur.execute(DELETE_ACTIVE_SQL, (alarm_id,))
                row = cur.fetchone()

                if row and row[0]:
                    cur.execute(
                        INSERT_HISTORY_SQL,
                        (alarm_id, json.dumps(row[0], default=str)),
                    )
                return

            if event_type != "alarm-create":
                return

            if not alarm.get("alarm_name") or not alarm.get("ne_name"):
                return

            cur.execute(
                UPSERT_ACTIVE_SQL,
                (alarm_id, json.dumps(alarm, default=str)),
            )

# -------------------------------
# Power Issue state helper
# -------------------------------
def get_active_power_issues():
    """
    Fetch currently active Power Issue alarms.
    """
    sql = """
    SELECT alarm
    FROM active_alarms
    WHERE alarm->>'alarm_name' = 'Power Issue'
      AND alarm->>'object_type' = 'PHYSICALCONNECTION';
    """

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql)
        return [row[0] for row in cur.fetchall()]

def get_active_los_alarms():
    """
    Fetch currently active Loss of signal - OCH alarms.
    """
    sql = """
    SELECT alarm
    FROM active_alarms
    WHERE alarm->>'alarm_name' = 'Loss of signal - OCH'
      AND alarm->>'severity' IN ('CRITICAL', 'MAJOR');
    """

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql)
        return [row[0] for row in cur.fetchall()]