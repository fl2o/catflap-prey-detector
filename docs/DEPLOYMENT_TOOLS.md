# Deployment Tools

## Table of Contents
- [SSH Setup](#ssh-setup)
  - [Connect via SSH](#connect-via-ssh)
  - [SSH Key Authentication](#ssh-key-authentication)
- [Tailscale](#tailscale)
  - [Usage](#usage)
- [Syncthing](#syncthing)
- [tmux - Terminal Multiplexer](#tmux---terminal-multiplexer)
  - [Installation](#installation)
  - [Basic Usage](#basic-usage)
  - [Reconnecting](#reconnecting)
- [WiFi Power Management](#wifi-power-management)
  - [Check Current Status](#check-current-status)
  - [Disable Power Management](#disable-power-management)
- [Running as a Service](#running-as-a-service)
- [Monitoring Logs](#monitoring-logs)
  - [Application Logs](#application-logs)
- [Performance Monitoring](#performance-monitoring)
  - [System Resources](#system-resources)
  - [Process Monitoring](#process-monitoring)

This guide covers useful tools for deploying and managing the Catflap Prey Detector on a Raspberry Pi.

## SSH Setup

SSH allows you to remotely access and control your Raspberry Pi.

### Connect via SSH

From your computer:

```bash
ssh username@raspberrypi.local
```

Or using IP address:

```bash
ssh username@192.168.1.100
```

### SSH Key Authentication

For passwordless login:

```bash
# On your computer, generate SSH key (if you don't have one)
ssh-keygen -t ed25519

# Copy public key to Pi
ssh-copy-id username@raspberrypi.local

# Now you can connect without password
ssh username@raspberrypi.local
```

## Tailscale

[Tailscale](https://tailscale.com/) provides secure remote access to your Raspberry Pi from anywhere, even behind NAT/firewalls.

### Usage

After setup, your Pi gets a permanent Tailscale IP and name (e.g., `100.x.y.z` raspberrypi):

```bash
# From anywhere with Tailscale installed
ssh username@raspberrypi
```

## Syncthing

[Syncthing](https://syncthing.net/) keeps your code synchronized between your development machine and the Raspberry Pi.


## tmux - Terminal Multiplexer

[tmux](https://github.com/tmux/tmux/wiki) allows you to run the detector in a persistent session that continues even after you disconnect from SSH.

### Installation

```bash
sudo apt install tmux
```

### Basic Usage

Start a new tmux session and run the detector:

```bash
# Create a new named session
tmux new -s catflap

# Inside tmux, run the detector
cd /path/to/catflap-prey-detector
make run

# Detach from session (keeps it running): Press Ctrl+B, then D
```

### Reconnecting

```bash
# List running sessions
tmux ls

# Attach to existing session
tmux attach -t catflap
```

With tmux, you can close your terminal or disconnect from SSH, and the detector will continue running in the background.

## WiFi Power Management

Raspberry Pi's WiFi power management can cause connection drops. Disable it for stable operation:

### Check Current Status

```bash
iwconfig wlan0 | grep "Power Management"
```

### Disable Power Management

```bash
sudo iwconfig wlan0 power off
```

## Running as a Service

Configure the detector to start automatically on boot using systemd.


## Monitoring Logs

### Application Logs

```bash
# View live logs
tail -f runtime/logs/main_app.log

# Search for errors
grep ERROR runtime/logs/main_app.log

# View last 100 lines
tail -n 100 runtime/logs/main_app.log
```

## Performance Monitoring

### System Resources

```bash
# CPU and memory usage
htop

# Disk usage
df -h

# Temperature (important for Pi)
vcgencmd measure_temp
```

### Process Monitoring

```bash
# Find detector process
ps aux | grep catflap

# Monitor specific process
top -p $(pgrep -f catflap-detector)
```