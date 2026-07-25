# Touchscreen Laser & Audio OSC Interface
> **PROTOTYPE VERSION 1**

A minimalist, high-contrast touchscreen interface and low-latency Node.js OSC bridge that simultaneously controls **MadMapper** (Lasers) and **Ableton Live** (Audio) over local network and Wi-Fi.

---

## Prototype Version 1 Overview

This prototype is designed specifically for performance environments where operators need simple, intuitive, non-technical touch controls to manipulate laser visuals and music effects simultaneously.

### Key Capabilities:
- **Dual OSC Routing**: Broadcasts low-latency UDP OSC messages to both **MadMapper** (`127.0.0.1:8000`) and **Ableton Live** (`172.20.10.8:11000` / Wi-Fi) from single touch gestures.
- **Minimalist Grayscale UI**: Clean, high-contrast 2-column dark touch surface (`http://localhost:3000`) designed for non-technical users.
- **Ultra-Smooth 60 FPS Sliders**:
  - `SIZE & SPEED` (Slider 1): Resizes Laser Surface in MadMapper (`/madmapper/laser/size`) AND modulates Effect Speed in Ableton Live (`/live/device/param/1`).
  - `INTENSITY` (Slider 2): Controls Master Laser Brightness in MadMapper (`/madmapper/laser/intensity`) AND Master Audio Volume in Ableton Live (`/live/device/param/2`).
- **Tactile Switches & Keyboard Shortcut**:
  - `LASER ON/OFF`: Tap toggle switch for master output shutter.
  - `HOLD STROBE [Q]`: Momentary press-and-hold button (**mapped to the `Q` key**). Press & hold turns Strobe ON (`1.0`); release turns Strobe OFF (`0.0`).
- **Kiosk Fullscreen Mode**: One-click borderless fullscreen mode for secondary touchscreen monitors.
- **Automated Port Reset**: Automatically clears occupied ports before launch (`npm run start`).

---

## Control Routing Matrix

| Touchscreen Control | Keyboard Shortcut | MadMapper OSC (`127.0.0.1:8000`) | Ableton Live OSC (`172.20.10.8:11000`) |
| :--- | :--- | :--- | :--- |
| **`SIZE & SPEED` Slider** | — | `/madmapper/laser/size` | `/live/device/param/1` |
| **`INTENSITY` Slider** | — | `/madmapper/laser/intensity` | `/live/device/param/2` |
| **`LASER ON/OFF` Switch** | — | `/madmapper/laser/power` | `/live/master/mute` |
| **`HOLD STROBE` Button** | **`Q` Key** (Hold/Release) | `/madmapper/laser/strobe` | `/live/repeat/enable` |

---

## Getting Started

### 1. Installation & Quick Start
```bash
# Clone the repository
git clone <your-repo-url>
cd laser_interface

# Start the OSC server and web UI
npm run start
```

### 2. Opening the UI
Open `http://localhost:3000` in your browser on your secondary touchscreen monitor and click **FULLSCREEN** in the top corner.

---

## 📡 Software Setup

### MadMapper
1. Open **Preferences** $\rightarrow$ **OSC**.
2. Set **Input Port** to `8000` and check **Enable OSC Input**.
3. Use **Control** $\rightarrow$ **Edit OSC Control** (`Cmd + Shift + O`) to auto-bind sliders.

### Ableton Live
1. Enable **Ableton Link** for automatic BPM sync.
2. Direct OSC packets are sent over Wi-Fi to Port `11000` (convertible to MIDI via Osculator or Max for Live).

---

## 📁 Repository Structure

```
├── server/
│   └── index.js         # Express + Socket.io + Node OSC UDP dispatcher
├── src/
│   ├── components/
│   │   └── TouchSlider.jsx  # rAF 60FPS smooth touch slider component
│   ├── App.jsx          # Main touch interface shell & Q-key binding
│   ├── index.css        # Minimalist grayscale dark stage design
│   └── main.jsx         # React DOM entry point
├── electron.js          # Electron borderless kiosk wrapper
└── package.json         # Scripts, dependencies, and port manager
```

---

## 🏷️ Version Tag
**Tag**: `v1.0.0-prototype`  
**License**: ISC
