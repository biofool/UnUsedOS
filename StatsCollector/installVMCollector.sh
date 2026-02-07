#!/bin/bash

# Create the script to run vmstat and pipe the output to logger
cat << 'EOF' | sudo tee /usr/local/bin/vmstat_vs.sh > /dev/null
#!/bin/bash
# Script to run vmstat and pipe the output to logger
vmstat 10 | logger -t VEMS
EOF

# Make the script executable
sudo chmod +x /usr/local/bin/vmstat_vs.sh

# Create the systemd service file
cat << 'EOF' | sudo tee /etc/systemd/system/vmstat-vs.service > /dev/null
[Unit]
Description=VMStat Logging Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/vmstat_vs.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd to recognize the new service, enable it to start at boot, and start the service
sudo systemctl daemon-reload
sudo systemctl enable vmstat-vs.service
sudo systemctl start vmstat-vs.service

# Display the status of the new service
echo "Service vmstat-vs has been started. Here is the status:"
sudo systemctl status vmstat-vs.service
