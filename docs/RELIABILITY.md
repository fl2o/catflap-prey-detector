# Reliability

The detector runs unattended as a systemd service with a few layers that let it
recover on its own. System unit + drop-in files are in
[`deploy/`](../deploy/), installed with `make install-service`.

- **Auto-start / restart** — runs as `catflap-detector` (`Restart=always`):
  starts on boot, restarts if it exits.
- **Liveness watchdog** — the service is `Type=notify`; the detection loop pings
  systemd, so a crashed *or* hung loop gets restarted.
- **Detection supervisor** — the detection thread restarts itself (with backoff)
  if it stops, independently of the rest of the process.
- **Hardware watchdog** — the board reboots if the kernel hard-freezes. This is
  configured system-wide (`RuntimeWatchdogSec`), so it covers the whole Pi, not
  just this service.
- **Logs** — bounded, rotating app logs (20 MB cap); journald persists across
  reboots, bounded to 200 MB.

## Operating it

Managed by systemd — don't launch it by hand (the camera can't be opened twice):

    systemctl status catflap-detector
    journalctl -u catflap-detector -f
    sudo systemctl restart catflap-detector

See [`deploy/README.md`](../deploy/README.md) for install/uninstall steps.
