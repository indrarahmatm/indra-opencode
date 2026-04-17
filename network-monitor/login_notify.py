#!/usr/bin/env python3
"""Login notification script - dipanggil oleh PAM"""

import subprocess
import sys
import os
import socket
from datetime import datetime

TOKEN = "7157068412:AAEkomBO_qCBW7SfUvblefqJ-WL6m8TZluk"
CHAT_ID = "6054204698"
API_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"


def send_telegram(message):
    try:
        import urllib.request
        import urllib.parse

        data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": message}).encode()
        req = urllib.request.Request(API_URL, data=data, method="POST")
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Gagal kirim: {e}", file=sys.stderr)


def main():
    hostname = socket.gethostname()
    user = os.environ.get("USER", os.environ.get("LOGNAME", "unknown"))
    ptype = os.environ.get("PAM_TYPE", "unknown")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"🔔 LOGIN NOTIFICATION\n\nHost: {hostname}\nUser: {user}\nType: {ptype}\nTime: {timestamp}"

    send_telegram(message)
    print(f"Login notification sent for {user} at {timestamp}")


if __name__ == "__main__":
    main()
