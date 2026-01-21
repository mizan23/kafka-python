We’ll use systemd timer (modern & reliable).

Service file
sudo nano /etc/systemd/system/nsp-alarm-cleanup.service

[Unit]
Description=NSP Alarm History Cleanup

[Service]
Type=oneshot
User=mizan
WorkingDirectory=/home/mizan/kafka-python
ExecStart=/home/mizan/kafka-python/venv/bin/python cleanup_history.py

Timer file
sudo nano /etc/systemd/system/nsp-alarm-cleanup.timer

[Unit]
Description=Run NSP alarm history cleanup daily

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target

Enable it
sudo systemctl daemon-reload
sudo systemctl enable --now nsp-alarm-cleanup.timer

🔎 Verify cleanup timer
systemctl list-timers | grep nsp
