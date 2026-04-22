#!/usr/bin/env python3
import socket
import struct
import random
import time
import can

PGN_ENGINE_TEMP = 0xFEEE
PGN_ENGINE_RPM = 0xF004
PGN_ENGINE_OIL_PRESSURE = 0xFEF1
PGN_ENGINE_FUEL_RATE = 0xFEF2
PGN_EXHAUST_TEMP = 0xFEF5
PGN_TURBO_RPM = 0xFEF6

UNITS = {
    "SM01": {
        "addr": 0x01,
        "rpm": 1800,
        "temp": 85,
        "oil": 350,
        "fuel": 25,
        "exhaust": 420,
        "turbo": 35000,
    },
    "SM02": {
        "addr": 0x02,
        "rpm": 1750,
        "temp": 82,
        "oil": 340,
        "fuel": 24,
        "exhaust": 415,
        "turbo": 34000,
    },
    "SM03": {
        "addr": 0x03,
        "rpm": 1850,
        "temp": 88,
        "oil": 360,
        "fuel": 26,
        "exhaust": 425,
        "turbo": 36000,
    },
}


def build_j1939_can_id(pgn, priority=3, src_addr=0x00):
    return (priority << 26) | (pgn << 8) | src_addr


def create_engine_data(pgn, value):
    data = bytearray(8)
    if pgn == PGN_ENGINE_RPM:
        struct.pack_into("<H", data, 0, value)
        struct.pack_into("<H", data, 2, 0xFFFF)
    elif pgn == PGN_ENGINE_TEMP:
        struct.pack_into("<H", data, 0, value)
    elif pgn == PGN_ENGINE_OIL_PRESSURE:
        struct.pack_into("<H", data, 0, value)
    elif pgn == PGN_ENGINE_FUEL_RATE:
        struct.pack_into("<H", data, 0, value)
    elif pgn == PGN_EXHAUST_TEMP:
        struct.pack_into("<H", data, 0, value)
    elif pgn == PGN_TURBO_RPM:
        struct.pack_into("<H", data, 0, value)
    return data


class EngineSimulator:
    def __init__(self, unit_name, interface="vcan0"):
        self.unit_name = unit_name
        self.interface = interface
        try:
            self.bus = can.interface.Bus(channel=interface, interface="socketcan")
        except can.CanError as e:
            raise RuntimeError(f"Failed to connect to CAN interface '{interface}': {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error connecting to CAN interface: {e}")
        
        if unit_name not in UNITS:
            raise ValueError(f"Unknown unit '{unit_name}'. Available: {list(UNITS.keys())}")
        self.unit = UNITS[unit_name]

    def close(self):
        try:
            self.bus.shutdown()
        except Exception as e:
            print(f"Warning: Error closing bus: {e}")

    def send_pgn(self, pgn, value):
        can_id = build_j1939_can_id(pgn, src_addr=self.unit["addr"])
        msg = can.Message(
            arbitration_id=can_id,
            data=create_engine_data(pgn, value),
            is_extended_id=True,
        )
        try:
            self.bus.send(msg)
        except can.CanError as e:
            print(f"Error sending CAN message: {e}")
        except Exception as e:
            print(f"Unexpected error sending message: {e}")

    def run_cycle(self, anomaly=False):
        base = self.unit
        if anomaly:
            rpm = base["rpm"] + random.randint(-200, 2500)
            temp = base["temp"] + random.randint(-10, 80)
            oil = base["oil"] + random.randint(-100, 200)
            fuel = base["fuel"] + random.randint(-10, 30)
            exhaust = base["exhaust"] + random.randint(-50, 200)
            turbo = base["turbo"] + random.randint(-5000, 10000)
        else:
            rpm = base["rpm"] + random.randint(-50, 50)
            temp = base["temp"] + random.randint(-3, 3)
            oil = base["oil"] + random.randint(-20, 20)
            fuel = base["fuel"] + random.randint(-2, 2)
            exhaust = base["exhaust"] + random.randint(-15, 15)
            turbo = base["turbo"] + random.randint(-1000, 1000)

        self.send_pgn(PGN_ENGINE_RPM, rpm)
        self.send_pgn(PGN_ENGINE_TEMP, temp + 273)
        self.send_pgn(PGN_ENGINE_OIL_PRESSURE, oil)
        self.send_pgn(PGN_ENGINE_FUEL_RATE, fuel)
        self.send_pgn(PGN_EXHAUST_TEMP, exhaust + 273)
        self.send_pgn(PGN_TURBO_RPM, turbo)


import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wirtgen ECM J1939 Simulator")
    parser.add_argument(
        "--unit", required=True, choices=["SM01", "SM02", "SM03"], help="Unit name"
    )
    parser.add_argument("--interface", default="vcan0", help="CAN interface")
    parser.add_argument("--interval", type=float, default=1.0, help="Send interval")
    parser.add_argument("--anomaly", action="store_true", help="Generate anomaly data")
    args = parser.parse_args()

    try:
        sim = EngineSimulator(args.unit, args.interface)
    except RuntimeError as e:
        print(f"Error: {e}")
        exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        exit(1)

    print(f"Starting {args.unit} simulator on {args.interface}...", flush=True)

    try:
        while True:
            try:
                sim.run_cycle(anomaly=args.anomaly)
            except Exception as e:
                print(f"Error in cycle: {e}", flush=True)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print(f"\nStopping {args.unit}...", flush=True)
    finally:
        sim.close()
        print("Simulator stopped.", flush=True)
