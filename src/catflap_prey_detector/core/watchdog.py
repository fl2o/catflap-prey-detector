"""Minimal systemd sd_notify integration: readiness + watchdog keep-alive.

Every function is a no-op when the process is not running under systemd with a
notify socket available (e.g. ``make run``, pytest, a plain shell), so they are
safe to call unconditionally from the detection loop.
"""
import logging
import os
import socket
import time

logger = logging.getLogger(__name__)

# systemd exports NOTIFY_SOCKET for the service when the unit uses Type=notify
# (or WatchdogSec=). Captured once at import; if absent, every call below no-ops.
_NOTIFY_SOCKET = os.environ.get("NOTIFY_SOCKET")

# The detection loop calls pet() on every captured frame (~30/s); only actually
# message systemd this often. The unit's WatchdogSec is much larger than this.
_BEAT_INTERVAL = 10.0
_last_beat = 0.0


def _send(message: str) -> None:
    if not _NOTIFY_SOCKET:
        return
    # A leading "@" denotes an abstract-namespace socket (leading NUL byte).
    addr = "\0" + _NOTIFY_SOCKET[1:] if _NOTIFY_SOCKET.startswith("@") else _NOTIFY_SOCKET
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
            sock.sendto(message.encode("utf-8"), addr)
    except OSError as exc:
        logger.debug("sd_notify(%r) failed: %s", message, exc)


def notify_ready() -> None:
    """Signal that the service is up and running (required for Type=notify)."""
    _send("READY=1")


def pet(force: bool = False) -> None:
    """Send a watchdog keep-alive, throttled to once per _BEAT_INTERVAL seconds."""
    global _last_beat
    now = time.monotonic()
    if force or now - _last_beat >= _BEAT_INTERVAL:
        _last_beat = now
        _send("WATCHDOG=1")
