#!/usr/bin/env python3
import os
import subprocess
import requests
import json
import time
from datetime import datetime

BOT_TOKEN = "7157068412:AAEkomBO_qCBW7SfUvblefqJ-WL6m8TZluk"
CHAT_ID = "6054204698"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
GET_UPDATE_URL = f"{API_URL}/getUpdates"
SEND_MSG_URL = f"{API_URL}/sendMessage"

OPENCODE_API = "http://localhost:4096"


def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def send_message(text, reply_markup=None):
    try:
        data = {"chat_id": CHAT_ID, "text": text}
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        requests.post(SEND_MSG_URL, data=data, timeout=10)
    except Exception as e:
        log(f"Send error: {e}")


COMMANDS = {
    "health": (
        "python3 /home/indra/network-monitor/server_health.py",
        "Server health report",
    ),
    "uptime": ("uptime", "Server uptime"),
    "free": ("free -h", "Memory usage"),
    "df": ("df -h", "Disk usage"),
    "hostname": ("hostname", "Server hostname"),
    "ps": ("ps aux --sort=-%cpu | head -10", "Top processes"),
    "network": ("ip -br addr show && ss -tuln | head -10", "Network info"),
    "logs": (
        "tail -10 /var/log/syslog 2>/dev/null || journalctl -n 10 --no-pager",
        "Recent logs",
    ),
    "help": ("help", "Show available commands"),
}


def get_main_menu():
    return {
        "keyboard": [
            [{"text": "📊 Health"}, {"text": "💻 System"}],
        ],
        "resize_keyboard": True,
    }


def get_system_menu():
    return {
        "keyboard": [
            [{"text": "📈 Uptime"}, {"text": "🧠 Memory"}],
            [{"text": "💾 Disk"}, {"text": "🔍 Process"}],
            [{"text": "🌐 Network"}, {"text": "📝 Logs"}],
            [{"text": "⬅️ Back"}],
        ],
        "resize_keyboard": True,
    }


def execute_command(cmd_key):
    if cmd_key == "help":
        help_text = "Server Monitor Commands:\n\n"
        for key, (cmd, desc) in COMMANDS.items():
            help_text += f"/{key} - {desc}\n"
        return help_text

    if cmd_key not in COMMANDS:
        return "Perintah tidak dikenal. Ketik /help"

    command = COMMANDS[cmd_key][0]
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        return result.stdout or result.stderr or "(tanpa output)"
    except Exception as e:
        return f"Error: {str(e)}"


def register_bot_commands():
    commands = []
    try:
        requests.post(
            f"{API_URL}/setMyCommands", json={"commands": commands}, timeout=10
        )
    except:
        pass


def get_latest_offset():
    try:
        resp = requests.get(GET_UPDATE_URL, timeout=5)
        data = resp.json()
        if data.get("ok") and data.get("result"):
            return max(u.get("update_id", 0) for u in data["result"]) + 1
    except:
        pass
    return None


def main():
    log("Bot started - Power menu disabled")
    register_bot_commands()

    send_message("== SERVER MONITOR ==\n\nPilih menu:", get_main_menu())
    send_message("Commands:\n" + "\n".join(f"/{k}" for k in COMMANDS.keys()))

    last_update_id = get_latest_offset()

    while True:
        try:
            params = {"timeout": 10}
            if last_update_id:
                params["offset"] = last_update_id + 1

            response = requests.get(GET_UPDATE_URL, params=params, timeout=15)
            data = response.json()

            if data.get("ok"):
                updates = data.get("result", [])
                for update in updates:
                    update_id = update.get("update_id")
                    message = update.get("message", {})
                    chat_id = str(message.get("chat", {}).get("id"))
                    text = message.get("text", "")

                    if chat_id != CHAT_ID:
                        last_update_id = update_id
                        continue

                    if text:
                        log(f"Message: {text}")

                        if text.lower() in ["/start", "/menu"]:
                            send_message(
                                "== SERVER MONITOR ==\n\nPilih menu:", get_main_menu()
                            )
                        elif text == "📊 Health":
                            send_message(execute_command("health"), get_main_menu())
                        elif text == "💻 System":
                            send_message("System Menu:", get_system_menu())
                        elif text == "📈 Uptime":
                            send_message(execute_command("uptime"), get_system_menu())
                        elif text == "🧠 Memory":
                            send_message(execute_command("free"), get_system_menu())
                        elif text == "💾 Disk":
                            send_message(execute_command("df"), get_system_menu())
                        elif text == "🔍 Process":
                            send_message(execute_command("ps"), get_system_menu())
                        elif text == "🌐 Network":
                            send_message(execute_command("network"), get_system_menu())
                        elif text == "📝 Logs":
                            send_message(execute_command("logs"), get_system_menu())
                        elif text == "⬅️ Back":
                            send_message(
                                "== SERVER MONITOR ==\n\nPilih menu:", get_main_menu()
                            )
                        else:
                            parts = text.strip().lstrip("/").split()
                            if parts:
                                cmd = parts[0]
                                result = execute_command(cmd)
                                send_message(result)
                            else:
                                send_message("Ketik /help untuk daftar command")

                    last_update_id = update_id

        except Exception as e:
            log(f"Error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    main()
