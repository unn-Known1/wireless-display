# Wireless Display

Use your Android TV as a wireless secondary display for your Linux Mint laptop.

## Quick Start

### 1. Install Linux Receiver
```bash
sudo dpkg -i wireless-display-receiver_1.0.0_amd64.deb
pip3 install PyQt6
python3 /opt/wireless-display/receiver/wireless-display-receiver.py
```

### 2. Install Android TV App
1. Transfer `wireless-display-tv.apk` to your Android TV
2. Enable "Unknown Sources" in TV settings
3. Install and launch "Wireless Display"

### 3. Connect
- Run the receiver on your laptop (note the IP)
- Open the app on your TV and enter the IP
- Your TV becomes a secondary display

## Features
- Full-screen display at TV resolution
- Adjustable quality (Low/Medium/High)
- Real-time stats (latency, FPS)
- Collapsible UI overlay on TV

## Requirements
- Linux Mint with Python 3.8+ and PyQt6
- Android TV with API 21+
- Same WiFi network

## License
MIT
