import sys
import time


def err(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def retry(fn, retries=2, delay=1.0, on_retry=None):
    last_exc = None
    for attempt in range(1 + retries):
        try:
            return fn()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            last_exc = e
            if attempt < retries:
                if on_retry:
                    on_retry(attempt + 1, e)
                else:
                    print(f"Retrying ({attempt + 1}/{retries})...", file=sys.stderr)
                time.sleep(delay)
    raise last_exc
