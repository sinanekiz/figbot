"""Restrained bring-up command line for the Pi 5."""

from __future__ import annotations

import argparse
import json

from .controller import MotionClient


def main() -> int:
    parser = argparse.ArgumentParser(description="FIGBOT V0 motion commissioning CLI")
    parser.add_argument("--port", default="/dev/ttyACM0")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("arm")
    sub.add_parser("disarm")
    home = sub.add_parser("home")
    home.add_argument("axis", choices=("J1", "J2", "J3", "J4"))
    move = sub.add_parser("move")
    for axis in ("j1", "j2", "j3", "j4"):
        move.add_argument(f"--{axis}", type=float, required=True)
    args = parser.parse_args()
    client = MotionClient(args.port)
    try:
        if args.command == "status": reply = client.status()
        elif args.command == "arm": reply = client.arm()
        elif args.command == "disarm": reply = client.disarm()
        elif args.command == "home": reply = client.home(args.axis)
        else:
            reply = client.move_degrees({name.upper(): getattr(args, name) for name in ("j1", "j2", "j3", "j4")})
        print(json.dumps({"kind": reply.kind, "seq": reply.seq, "fields": reply.fields}))
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
