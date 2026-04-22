#!/bin/bash
sudo cp ecm-simulator.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ecm-simulator
sudo systemctl start ecm-simulator
echo "Service installed and started"