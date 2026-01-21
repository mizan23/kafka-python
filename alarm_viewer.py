#!/usr/bin/env python3
import psycopg2
import json
from tabulate import tabulate
from argparse import ArgumentParser

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
# DB helper
# -------------------------------
def get_conn():
    return psycopg2.connect(**DB_CONFIG)

# -------------------------------
# ACTIVE alarms (list)
# -------------------------------
def show_active(limit=20):
    sql = """
    SELECT
        alarm_id,
        alarm->>'alarm_name',
        alarm->>'ne_name',
        alarm->>'severity',
        alarm->>'last_detected',
        last_updated
    FROM active_alarms
    ORDER BY last_updated DESC
    LIMIT %s;
    """

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (limit,))
        rows = cur.fetchall()

    if not rows:
        print("✅ No active alarms")
        return

    print("\n🚨 ACTIVE ALARMS\n")
    print(tabulate(
        rows,
        headers=[
            "Alarm ID",
            "Alarm Name",
            "NE",
            "Severity",
            "Last Detected",
            "Updated At"
        ],
        tablefmt="psql"
    ))

# -------------------------------
# HISTORY alarms (list)
# -------------------------------
def show_history(limit=20):
    sql = """
    SELECT
        alarm_id,
        alarm->>'alarm_name',
        alarm->>'ne_name',
        alarm->>'severity',
        cleared_at
    FROM alarm_history
    ORDER BY cleared_at DESC
    LIMIT %s;
    """

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (limit,))
        rows = cur.fetchall()

    if not rows:
        print("✅ No historical alarms")
        return

    print("\n📜 ALARM HISTORY\n")
    print(tabulate(
        rows,
        headers=[
            "Alarm ID",
            "Alarm Name",
            "NE",
            "Severity",
            "Cleared At"
        ],
        tablefmt="psql"
    ))

# -------------------------------
# FULL ALARM VIEW (ACTIVE)
# -------------------------------
def show_active_full(alarm_id):
    sql = """
    SELECT alarm
    FROM active_alarms
    WHERE alarm_id = %s;
    """

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (alarm_id,))
        row = cur.fetchone()

    if not row:
        print("❌ Active alarm not found")
        return

    print("\n🚨 FULL ACTIVE ALARM\n")
    print(json.dumps(row[0], indent=2, default=str))

# -------------------------------
# FULL ALARM VIEW (HISTORY)
# -------------------------------
def show_history_full(alarm_id):
    sql = """
    SELECT alarm, cleared_at
    FROM alarm_history
    WHERE alarm_id = %s
    ORDER BY cleared_at DESC
    LIMIT 1;
    """

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (alarm_id,))
        row = cur.fetchone()

    if not row:
        print("❌ History alarm not found")
        return

    alarm, cleared_at = row
    alarm["cleared_at"] = str(cleared_at)

    print("\n📜 FULL HISTORICAL ALARM\n")
    print(json.dumps(alarm, indent=2, default=str))

# -------------------------------
# Delete ACTIVE alarm
# -------------------------------
def delete_active(alarm_id):
    sql = "DELETE FROM active_alarms WHERE alarm_id = %s;"

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (alarm_id,))
        deleted = cur.rowcount
        conn.commit()

    if deleted:
        print(f"🗑️ Deleted ACTIVE alarm: {alarm_id}")
    else:
        print("❌ Active alarm not found")

# -------------------------------
# Delete HISTORY alarm
# -------------------------------
def delete_history(alarm_id):
    sql = "DELETE FROM alarm_history WHERE alarm_id = %s;"

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (alarm_id,))
        deleted = cur.rowcount
        conn.commit()

    if deleted:
        print(f"🗑️ Deleted HISTORY alarm(s): {alarm_id}")
    else:
        print("❌ History alarm not found")

# -------------------------------
# Purge HISTORY
# -------------------------------
def purge_history():
    sql = "DELETE FROM alarm_history;"

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql)
        deleted = cur.rowcount
        conn.commit()

    print(f"🧹 Purged {deleted} historical alarms")

# -------------------------------
# CLI
# -------------------------------
def main():
    parser = ArgumentParser(
        description="NSP Alarm Viewer (Active & History)",
    )

    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("active", help="Show active alarms")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("history", help="Show alarm history")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("active-full", help="Show full active alarm JSON")
    p.add_argument("alarm_id")

    p = sub.add_parser("history-full", help="Show full historical alarm JSON")
    p.add_argument("alarm_id")

    p = sub.add_parser("delete-active", help="Delete active alarm")
    p.add_argument("alarm_id")

    p = sub.add_parser("delete-history", help="Delete history alarm")
    p.add_argument("alarm_id")

    sub.add_parser("purge-history", help="Delete ALL history alarms")

    args = parser.parse_args()

    if args.cmd == "active":
        show_active(args.limit)
    elif args.cmd == "history":
        show_history(args.limit)
    elif args.cmd == "active-full":
        show_active_full(args.alarm_id)
    elif args.cmd == "history-full":
        show_history_full(args.alarm_id)
    elif args.cmd == "delete-active":
        delete_active(args.alarm_id)
    elif args.cmd == "delete-history":
        delete_history(args.alarm_id)
    elif args.cmd == "purge-history":
        purge_history()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
