import psycopg2

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "dbname": "nsp",
    "user": "nsp_user",
    "password": "nsp_pass",
}

DELETE_SQL = """
DELETE FROM nsp_alarms
WHERE
    alarm_name = 'Quality Threshold Crossed 15m'
 OR alarm_name = 'Channel optical power out of range'
 OR alarm_name = 'Power management suspended'
 OR probable_cause IN ('OPR', 'PWRSUSP');
 OR alarm_name = 'Underlying resource unavailable - optical'
"""

COUNT_SQL = """
SELECT COUNT(*)
FROM nsp_alarms
WHERE
    alarm_name = 'Quality Threshold Crossed 15m'
 OR alarm_name = 'Channel optical power out of range'
 OR alarm_name = 'Power management suspended'
 OR probable_cause IN ('OPR', 'PWRSUSP');
"""


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            # Preview
            cur.execute(COUNT_SQL)
            count = cur.fetchone()[0]

            if count == 0:
                print("✅ No noisy alarms found. Nothing to delete.")
                return

            print(f"⚠️ {count} noisy alarms found")

            # Delete
            cur.execute(DELETE_SQL)
            conn.commit()

            print(f"🗑️ Deleted {count} noisy alarms")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
