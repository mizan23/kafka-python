1️⃣ Decide what we run

Your main entry point is clearly:

python full_flow_main.py


So the service will run that, not alarms.py.

Directory:

/home/mizan/kafka-python


Virtualenv:

/home/mizan/kafka-python/venv

2️⃣ Create log directory
sudo mkdir -p /var/log/nsp
sudo chown mizan:mizan /var/log/nsp


Logs will be:

/var/log/nsp/nsp-consumer.log

/var/log/nsp/nsp-consumer.err

3️⃣ Create systemd service file

Create the file:

sudo nano /etc/systemd/system/nsp-kafka-consumer.service

✅ Paste this EXACT content
[Unit]
Description=NSP Kafka Alarm Consumer
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=mizan
Group=mizan
WorkingDirectory=/home/mizan/kafka-python

# Use virtualenv python
ExecStart=/home/mizan/kafka-python/venv/bin/python full_flow_main.py

# Environment
Environment=PYTHONUNBUFFERED=1

# Restart policy
Restart=always
RestartSec=10

# Logging
StandardOutput=append:/var/log/nsp/nsp-consumer.log
StandardError=append:/var/log/nsp/nsp-consumer.err

# Hardening (safe defaults)
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target


Save and exit.

4️⃣ Reload systemd and enable service
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable nsp-kafka-consumer

5️⃣ Start the service
sudo systemctl start nsp-kafka-consumer

6️⃣ Verify status
systemctl status nsp-kafka-consumer


You should see:

✅ Active: running

No Python import errors

No permission errors

7️⃣ View logs (important)
Live logs
tail -f /var/log/nsp/nsp-consumer.log

Error logs
tail -f /var/log/nsp/nsp-consumer.err

8️⃣ Stop / restart (anytime)
sudo systemctl stop nsp-kafka-consumer
sudo systemctl restart nsp-kafka-consumer
