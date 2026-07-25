# Advanced Hand & Finger Motion Controller

A real-time hand-tracking performance controller built with Google MediaPipe Tasks API, OpenCV, MIDI (`mido`), and OSC (`python-osc`).

## Features
- **Individual Finger Height Tracking**: Tracks Index, Middle, Ring, Pinky, and Thumb heights independently.
- **Finger Spread (Fan Gesture)**: Detects fingers pressed together vs spread wide open.
- **Wrist Roll / Rotation**: Detects wrist rotary angle.
- **Two-Hand Distance**: Measures physical distance between Left and Right hands.
- **Virtual MIDI Routing (Ableton Live)**: Sends CC messages & Note triggers over macOS `IAC Driver Bus 1`.
- **OSC Routing (MadMapper)**: Sends high-resolution OSC float parameters (`0.0`–`1.0`) to `127.0.0.1:8000`.

---

## Signal Mapping Reference

### 1. Left Hand Controls
| Gesture / Parameter | MIDI CC / Note (Ableton) | OSC Address (MadMapper) | Description |
|---------------------|--------------------------|-------------------------|-------------|
| **Hand Y (Height)** | MIDI CC #1 | `/hand/left/y` | Master Filter / Track Volume |
| **Hand X (Position)** | MIDI CC #2 | `/hand/left/x` | Track Pan |
| **Index Pinch** | MIDI CC #3 | `/hand/left/pinch` | FX Dry/Wet |
| **Index Finger Y** | MIDI CC #7 | `/hand/left/index_y` | Independent Index Height |
| **Middle Finger Y** | MIDI CC #8 | `/hand/left/middle_y` | Independent Middle Height |
| **Ring Finger Y** | MIDI CC #9 | `/hand/left/ring_y` | Independent Ring Height |
| **Pinky Finger Y** | MIDI CC #10 | `/hand/left/pinky_y` | Independent Pinky Height |
| **Thumb Finger Y** | - | `/hand/left/thumb_y` | Independent Thumb Height |
| **Finger Spread Wide** | MIDI CC #11 | `/hand/left/spread` | Reverb Width / Particle Scale |
| **Wrist Roll Angle** | MIDI CC #12 | `/hand/left/roll` | Rotary Dial / Angle Rotation |
| **Fist Gesture** | MIDI Note 60 (C3) | `/hand/left/fist` | Clip Trigger / Blackout Switch |

### 2. Right Hand Controls
| Gesture / Parameter | MIDI CC / Note (Ableton) | OSC Address (MadMapper) | Description |
|---------------------|--------------------------|-------------------------|-------------|
| **Hand Y (Height)** | MIDI CC #4 | `/hand/right/y` | Playback Speed / Master FX |
| **Hand X (Position)** | MIDI CC #5 | `/hand/right/x` | Crossfader / Surface Position |
| **Index Pinch** | MIDI CC #6 | `/hand/right/pinch` | Delay Feedback / Zoom |
| **Index Finger Y** | MIDI CC #13 | `/hand/right/index_y` | Independent Index Height |
| **Middle Finger Y** | MIDI CC #14 | `/hand/right/middle_y` | Independent Middle Height |
| **Ring Finger Y** | MIDI CC #15 | `/hand/right/ring_y` | Independent Ring Height |
| **Pinky Finger Y** | MIDI CC #16 | `/hand/right/pinky_y` | Independent Pinky Height |
| **Thumb Finger Y** | - | `/hand/right/thumb_y` | Independent Thumb Height |
| **Finger Spread Wide** | MIDI CC #17 | `/hand/right/spread` | Mesh Warp Amount / Strobe Rate |
| **Wrist Roll Angle** | MIDI CC #18 | `/hand/right/roll` | Visual Layer Rotation |
| **Fist Gesture** | MIDI Note 62 (D3) | `/hand/right/fist` | Cue Trigger / Flash FX |

### 3. Global Two-Hand Controls
| Gesture / Parameter | MIDI CC (Ableton) | OSC Address (MadMapper) | Description |
|---------------------|-------------------|-------------------------|-------------|
| **Two-Hand Distance** | MIDI CC #19 | `/hand/two_hand_distance` | Pulling Hands Apart / Pushing Together |

---

## Quick Start Guide

### Launch the Controller
```bash
cd /Users/annavladimirskaya/Documents/projects/NOTATIONS/laser_interface/Hand_Controller
./run.sh
```

### Keyboard & Quick-Map Controls
- `1`: **Solo Left Spread (CC 11)** *(Ableton Instant Mapping)*
- `2`: **Solo Left Pinch (CC 3)** *(Ableton Instant Mapping)*
- `3`: **Solo Left Fist (Note 60 / CC 30)** *(Ableton Instant Mapping)*
- `4`: **Solo Right Spread (CC 17)** *(Ableton Instant Mapping)*
- `5`: **Solo Right Pinch (CC 6)** *(Ableton Instant Mapping)*
- `6`: **Solo Right Fist (Note 62 / CC 31)** *(Ableton Instant Mapping)*
- `7`: **Solo Left Height (CC 1)**
- `8`: **Solo Right Height (CC 4)**
- `9`: **Solo Wrist Roll (CC 12 & 18)**
- `0` or `Space`: **NORMAL LIVE PERFORMANCE MODE (All Gestures Active)**
- `q`: Quit application
- `m`: Toggle MIDI output ON / OFF
- `o`: Toggle OSC output ON / OFF
