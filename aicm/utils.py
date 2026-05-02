import sys


def err(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)
