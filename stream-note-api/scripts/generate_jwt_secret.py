#!/usr/bin/env python3
"""Generate a strong JWT secret for `.env`."""

from __future__ import annotations

import argparse
import secrets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate JWT_SECRET_KEY for Stream Note backend."
    )
    parser.add_argument(
        "--bytes",
        type=int,
        default=48,
        help="Entropy size in bytes before URL-safe encoding (default: 48).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.bytes < 32:
        raise SystemExit("--bytes must be >= 32 for sufficient entropy.")

    secret = secrets.token_urlsafe(args.bytes)
    print("Generated JWT secret:")
    print(secret)
    print()
    print("Add this line to stream-note-api/.env:")
    print(f"JWT_SECRET_KEY={secret}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
