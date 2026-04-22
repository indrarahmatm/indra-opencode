#!/usr/bin/env python3
import can
import threading
import json
import time
import urllib.request
import urllib.parse
import os
from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

units_data = {}
units_lock = threading.Lock()

TELEGRAM_TOKEN = "8627954180:AAHzpqbqsuHa1mCMmxXGQTLsE86CWlR0lLI"
TELEGRAM_CHAT_ID = "6054204698"

ANOMALY_THRESHOLDS = {
    "Engine RPM": {"min": 1500, "max": 2100},
    "Engine Temp": {"min": 250, "max": 400},
    "Oil Pressure": {"min": 150, "max": 500},
    "Fuel Rate": {"min": 10, "max": 40},
    "Exhaust Temp": {"min": 350, "max": 550},
    "Turbo RPM": {"min": 20000, "max": 50000},
}

last_alert_time = {}
ALERT_COOLDOWN = 60

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}).encode()
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

def check_anomaly(unit, param, value):
    if param not in ANOMALY_THRESHOLDS:
        return False
    thresh = ANOMALY_THRESHOLDS[param]
    return value < thresh["min"] or value > thresh["max"]

def send_anomaly_alert(unit, param, value):
    key = f"{unit}:{param}"
    now = time.time()
    if key in last_alert_time and now - last_alert_time[key] < ALERT_COOLDOWN:
        return
    last_alert_time[key] = now
    
    message = f"⚠️ *Health Report*\n\n*Unit:* {unit}\n*Parameter:* {param}\n*Value:* {value}"
    send_telegram(message)

PGN_NAMES = {
    0xF004: "Engine RPM",
    0xFEEE: "Engine Temp",
    0xFEF1: "Oil Pressure",
    0xFEF2: "Fuel Rate",
    0xFEF5: "Exhaust Temp",
    0xFEF6: "Turbo RPM",
}

def get_pgn(can_id):
    return (can_id >> 8) & 0xFFFF

def get_src_addr(can_id):
    return can_id & 0xFF

def decode_can_data(pgn, data):
    if pgn == 0xF004:
        value = data[0] | (data[1] << 8)
        return value if value < 0x8000 else value - 0x10000
    elif pgn in [0xFEEE, 0xFEF1, 0xFEF2, 0xFEF5, 0xFEF6]:
        return data[0] | (data[1] << 8)
    return 0

def listen_can():
    global units_data
    try:
        bus = can.interface.Bus(channel="vcan0", interface="socketcan")
    except Exception as e:
        print(f"Failed to connect to vcan0: {e}")
        return

    print("Listening for CAN messages on vcan0...")
    while True:
        try:
            msg = bus.recv(timeout=1.0)
            pgn = get_pgn(msg.arbitration_id)
            src = get_src_addr(msg.arbitration_id)
            
            if pgn in PGN_NAMES and src in [1, 2, 3]:
                unit_name = f"SM0{src}"
                value = decode_can_data(pgn, msg.data)
                
                with units_lock:
                    if unit_name not in units_data:
                        units_data[unit_name] = {}
                    units_data[unit_name][PGN_NAMES[pgn]] = value
                    units_data[unit_name]["timestamp"] = time.time()
                
                if check_anomaly(unit_name, PGN_NAMES[pgn], value):
                    send_anomaly_alert(unit_name, PGN_NAMES[pgn], value)
                
                socketio.emit("can_data", {
                    "unit": unit_name,
                    "parameter": PGN_NAMES[pgn],
                    "value": value,
                    "pgn": hex(pgn),
                    "data": units_data[unit_name].copy()
                })
        except Exception as e:
            pass

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ECM Simulator Monitor</title>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a2e; color: #eee; }
        h1 { text-align: center; color: #00d4ff; }
        .units { display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; }
        .unit-card { 
            background: #16213e; border-radius: 10px; padding: 20px; 
            min-width: 250px; border: 2px solid #0f3460;
        }
        .unit-card.active { border-color: #00d4ff; animation: pulse 2s infinite; }
        .unit-name { font-size: 24px; color: #00d4ff; margin-bottom: 15px; }
        .param { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #333; }
        .param-name { color: #888; }
        .param-value { font-weight: bold; color: #fff; }
        .param-value.warning { color: #ff9800; }
        .param-value.critical { color: #f44336; }
        .timestamp { color: #666; font-size: 12px; text-align: center; margin-top: 10px; }
        @keyframes pulse {
            0%, 100% { box-shadow: 0 0 5px #00d4ff; }
            50% { box-shadow: 0 0 20px #00d4ff; }
        }
    </style>
</head>
<body>
    <h1>ECM Simulator Monitor</h1>
    <div class="units" id="units"></div>
    <script>
        const units = { SM01: {}, SM02: {}, SM03: {} };
        const socket = io();
        
        socket.on("can_data", (data) => {
            units[data.unit] = data.data;
            render();
        });
        
        function render() {
            const container = document.getElementById("units");
            container.innerHTML = "";
            for (const [unit, params] of Object.entries(units)) {
                if (Object.keys(params).length < 2) continue;
                const now = Date.now();
                const age = params.timestamp ? (now - params.timestamp * 1000) / 1000 : 999;
                const active = age < 5 ? "active" : "";
                
                let html = `<div class="unit-card ${active}"><div class="unit-name">${unit}</div>`;
                const fields = ["Engine RPM", "Engine Temp", "Oil Pressure", "Fuel Rate", "Exhaust Temp", "Turbo RPM"];
                for (const field of fields) {
                    const val = params[field];
                    if (val !== undefined) {
                        let cls = "param-value";
                        if (field === "Engine RPM" && (val < 1600 || val > 2000)) cls += " warning";
                        if (field === "Engine Temp" && (val > 400 || val < 250)) cls += " warning";
                        html += `<div class="param"><span class="param-name">${field}</span><span class="${cls}">${val}</span></div>`;
                    }
                }
                html += `<div class="timestamp">${params.timestamp ? new Date(params.timestamp * 1000).toLocaleTimeString() : "-"}</div></div>`;
                container.innerHTML += html;
            }
        }
        setInterval(render, 1000);
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

if __name__ == "__main__":
    threading.Thread(target=listen_can, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5000)