# Deployment files

systemd unit and drop-in files that make the detector run unattended and
recover on its own. See [`docs/RELIABILITY.md`](../docs/RELIABILITY.md) for what
each layer does.

| File | Installs to | Purpose |
|------|-------------|---------|
| `catflap-detector.service` | `/etc/systemd/system/` | Runs the detector (`Type=notify`, auto-restart, liveness watchdog) |
| `10-watchdog.conf` | `/etc/systemd/system.conf.d/` | Hardware watchdog — reboots the board on a kernel hard-freeze |
| `10-persistent.conf` | `/etc/systemd/journald.conf.d/` | Persist logs across reboots, bounded to 200 MB |

## Install (recommended)

From the repo root:

```bash
make install-service
```

This fills the `<USER>` / `<INSTALL_DIR>` placeholders in the unit from your
current user and repo path, copies the three files into place, reloads systemd,
and enables the service on boot.

> **Prerequisite:** the service sources `<INSTALL_DIR>/.envrc` for its
> configuration (`BOT_TOKEN`, `GROUP_ID`, `PREY_DETECTOR_API_KEY`, ...). That
> file is gitignored and must exist before the service will start — see
> [`docs/CONFIGURATION.md`](../docs/CONFIGURATION.md).

## Install (manual)

```bash
# 1. Service unit — replace <USER> and <INSTALL_DIR> with real values first
sudo cp deploy/catflap-detector.service /etc/systemd/system/
sudo sed -i "s|<USER>|$(whoami)|g; s|<INSTALL_DIR>|$(pwd)|g" \
  /etc/systemd/system/catflap-detector.service
sudo systemctl daemon-reload
sudo systemctl enable --now catflap-detector

# 2. Hardware watchdog (system-wide — reboots the whole board on a freeze)
sudo mkdir -p /etc/systemd/system.conf.d
sudo cp deploy/10-watchdog.conf /etc/systemd/system.conf.d/
sudo systemctl daemon-reexec

# 3. Persistent, bounded journald logs
sudo mkdir -p /etc/systemd/journald.conf.d
sudo cp deploy/10-persistent.conf /etc/systemd/journald.conf.d/
sudo systemctl restart systemd-journald && sudo journalctl --flush
```

## Operate

```bash
systemctl status catflap-detector       # current state
journalctl -u catflap-detector -f        # live logs
sudo systemctl restart catflap-detector  # manual restart
```

## Uninstall

```bash
sudo systemctl disable --now catflap-detector
sudo rm /etc/systemd/system/catflap-detector.service
sudo rm -f /etc/systemd/system.conf.d/10-watchdog.conf
sudo rm -f /etc/systemd/journald.conf.d/10-persistent.conf
sudo systemctl daemon-reload && sudo systemctl daemon-reexec
```
