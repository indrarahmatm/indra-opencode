#!/usr/bin/env python3
"""Server Health Monitor - Linux system health check"""

import subprocess
import os
import socket
import re
from datetime import datetime


def get_hostname():
    return socket.gethostname()


def get_uptime():
    try:
        with open("/proc/uptime", "r") as f:
            uptime_seconds = float(f.readline().split()[0])
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        return f"{days} days, {hours} hours, {minutes} minutes"
    except Exception:
        return "Unknown"


def get_cpu_usage():
    try:
        result = subprocess.run(
            ["top", "-bn1"], capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.split("\n"):
            if "Cpu(s)" in line or "%Cpu" in line:
                match = re.search(r"(\d+\.?\d*)\s*id", line)
                if match:
                    idle = float(match.group(1))
                    used = 100 - idle
                    return round(used, 1)
        return 0.0
    except Exception:
        return 0.0


def get_cpu_cores():
    try:
        result = subprocess.run(["nproc"], capture_output=True, text=True, timeout=5)
        return int(result.stdout.strip())
    except Exception:
        return 1


def get_load_average():
    try:
        result = subprocess.run(["uptime"], capture_output=True, text=True, timeout=5)
        match = re.search(
            r"load average[s]?: ([\d.]+), ([\d.]+), ([\d.]+)", result.stdout
        )
        if match:
            return f"{match.group(1)}, {match.group(2)}, {match.group(3)}"
        return "N/A"
    except Exception:
        return "N/A"


def get_memory_usage():
    try:
        result = subprocess.run(
            ["free", "-b"], capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().split("\n")
        if len(lines) >= 2:
            mem_line = lines[1].split()
            total = int(mem_line[1])
            used = int(mem_line[2])
            percent = (used / total) * 100
            return {"total": total, "used": used, "percent": round(percent, 1)}
        return {"total": 0, "used": 0, "percent": 0}
    except Exception:
        return {"total": 0, "used": 0, "percent": 0}


def format_bytes(bytes_val):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.1f}{unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f}PB"


def get_disk_usage():
    try:
        result = subprocess.run(
            ["df", "-B1"], capture_output=True, text=True, timeout=10
        )
        lines = result.stdout.strip().split("\n")
        for line in lines[1:]:
            if "/" in line and not line.startswith("tmpfs"):
                parts = line.split()
                if len(parts) >= 6:
                    device = parts[0]
                    if device == "/dev/sda" or device.startswith("/dev/"):
                        total = int(parts[1])
                        used = int(parts[2])
                        percent = float(parts[4].replace("%", ""))
                        return {
                            "total": total,
                            "used": used,
                            "percent": round(percent, 1),
                        }
        return {"total": 0, "used": 0, "percent": 0}
    except Exception:
        return {"total": 0, "used": 0, "percent": 0}


def get_services_count():
    try:
        result = subprocess.run(
            [
                "systemctl",
                "list-units",
                "--type=service",
                "--state=running",
                "--no-pager",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        count = sum(1 for line in result.stdout.split("\n") if ".service" in line)
        return count
    except Exception:
        return 0


def check_alerts(cpu, memory, disk):
    alerts = []
    if cpu > 80:
        alerts.append(f"WARNING: CPU usage is {cpu}% (threshold: 80%)")
    if memory > 85:
        alerts.append(f"WARNING: Memory usage is {memory}% (threshold: 85%)")
    if disk > 90:
        alerts.append(f"CRITICAL: Disk usage is {disk}% (threshold: 90%)")
    return alerts


def main():
    hostname = get_hostname()
    uptime = get_uptime()
    cpu_usage = get_cpu_usage()
    cpu_cores = get_cpu_cores()
    load_avg = get_load_average()
    memory = get_memory_usage()
    disk = get_disk_usage()
    services = get_services_count()

    print("\n" + "=" * 50)
    print("=== Server Health Report ===")
    print("=" * 50)
    print(f"Host: {hostname}")
    print(f"Uptime: {uptime}")
    print(f"CPU: {cpu_usage}% | Cores: {cpu_cores} | Load: {load_avg}")
    print(
        f"Memory: {format_bytes(memory['used'])}/{format_bytes(memory['total'])} ({memory['percent']}%)"
    )
    print(
        f"Disk: {format_bytes(disk['used'])}/{format_bytes(disk['total'])} ({disk['percent']}%)"
    )
    print(f"Services Running: {services}")
    print("=" * 50)

    alerts = check_alerts(cpu_usage, memory["percent"], disk["percent"])
    if alerts:
        print("\n--- Alerts ---")
        for alert in alerts:
            print(f"  ⚠ {alert}")

    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
