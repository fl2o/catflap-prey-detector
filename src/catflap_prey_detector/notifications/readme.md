 # Notifications Module

Telegram bot for remote monitoring and control of the catflap prey detector.

## Features

- **Real-time Alerts:** Sends notifications with images when prey is detected
- **Remote Control:** Manual lock/unlock via Telegram commands
- **Live Camera:** Capture current camera view on demand
- **Status Monitoring:** Check catflap lock status

## Commands

- `/lock` - Manually lock the catflap
- `/unlock` - Manually unlock the catflap
- `/status` - Check current lock status and remaining time
- `/photo` - Capture and send current camera image
- `/ping` - Health check (responds with "pong")
- `/where` - Get current chat and thread IDs

## Setup

Set environment variables:
```bash
export BOT_TOKEN="your_telegram_bot_token"  # From @BotFather
export GROUP_ID="your_telegram_group_id"    # Chat ID for notifications
```