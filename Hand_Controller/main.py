import os
import cv2
import math
import time
import numpy as np
from pythonosc import udp_client
import mido

# Suppress warnings & disable background clearcut telemetry
os.environ['MEDIAPIPE_DISABLE_CLEARCUT_LOGGING'] = '1'
os.environ['GLOG_minloglevel'] = '3'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib_cache'

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Hand Landmark Connections for custom skeleton drawing
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (5, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20) # Pinky & Palm
]

class HandController:
    def __init__(self, osc_ip="127.0.0.1", osc_port=8000, midi_port_keyword="IAC"):
        # OSC Setup (for MadMapper)
        self.osc_client = udp_client.SimpleUDPClient(osc_ip, osc_port)
        self.osc_enabled = True
        self.osc_ip = osc_ip
        self.osc_port = osc_port
        
        # MIDI Setup (for Ableton Live)
        self.midi_output = None
        self.midi_enabled = False
        self.solo_mode = "ALL"
        self.solo_timestamp = time.time()
        self.init_midi(midi_port_keyword)

        # MediaPipe HandLandmarker Setup
        model_path = os.path.join(os.path.dirname(__file__), 'hand_landmarker.task')
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_hands=2,
            min_hand_detection_confidence=0.6,
            min_hand_presence_confidence=0.6,
            min_tracking_confidence=0.6
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        
        # Smoothing memory (Exponential Moving Average)
        self.prev_vals = {}
        self.alpha = 0.35  # Smoothing factor (0.1 = smooth, 0.9 = fast)

    def set_solo_mode(self, mode):
        self.solo_mode = mode
        self.solo_timestamp = time.time()
        
    def init_midi(self, keyword):
        outputs = mido.get_output_names()
        print("\n--- Available MIDI Output Ports ---")
        target_port = None
        for name in outputs:
            print(f" - {name}")
            if keyword.lower() in name.lower() and target_port is None:
                target_port = name
                
        if target_port:
            try:
                self.midi_output = mido.open_output(target_port)
                self.midi_enabled = True
                print(f"--> Connected to MIDI Output: {target_port}")
            except Exception as e:
                print(f"--> Failed to open MIDI port {target_port}: {e}")
        else:
            if outputs:
                try:
                    self.midi_output = mido.open_output(outputs[0])
                    self.midi_enabled = True
                    print(f"--> Keyword '{keyword}' not found. Connected fallback MIDI port: {outputs[0]}")
                except Exception as e:
                    print(f"--> Failed to open fallback MIDI port: {e}")
            else:
                print("--> No virtual MIDI ports available!")
                self.midi_enabled = False

    def smooth(self, key, value):
        if key not in self.prev_vals:
            self.prev_vals[key] = value
        else:
            self.prev_vals[key] = self.alpha * value + (1 - self.alpha) * self.prev_vals[key]
        return self.prev_vals[key]

    def send_midi_cc(self, channel, control, value):
        if self.midi_enabled and self.midi_output:
            if self.solo_mode != "ALL":
                allowed_ccs = {
                    "left_spread": [11],
                    "left_pinch": [3],
                    "left_fist": [30],
                    "right_spread": [17],
                    "right_pinch": [6],
                    "right_fist": [31],
                    "left_height": [1],
                    "right_height": [4],
                    "wrist_roll": [12, 18],
                }
                if control not in allowed_ccs.get(self.solo_mode, []):
                    return
            val_7bit = int(clamp(value, 0, 127))
            msg = mido.Message('control_change', channel=channel, control=control, value=val_7bit)
            self.midi_output.send(msg)

    def send_midi_note(self, channel, note, velocity):
        if self.midi_enabled and self.midi_output:
            if self.solo_mode != "ALL":
                allowed_notes = {
                    "left_fist": [60],
                    "right_fist": [62],
                }
                if note not in allowed_notes.get(self.solo_mode, []):
                    return
            vel_7bit = int(clamp(velocity, 0, 127))
            msg_type = 'note_on' if vel_7bit > 0 else 'note_off'
            msg = mido.Message(msg_type, channel=channel, note=note, velocity=vel_7bit)
            self.midi_output.send(msg)

    def send_osc(self, address, value):
        if self.osc_enabled and self.osc_client:
            self.osc_client.send_message(address, float(value))

    def send_osc_and_midi(self, address, float_val, midi_ch, midi_cc):
        # 1. Send OSC (for MadMapper)
        self.send_osc(address, float_val)
        
        # 2. Send MIDI (for Ableton Live)
        val_7bit = int(clamp(float_val * 127.0, 0, 127))
        self.send_midi_cc(midi_ch, midi_cc, val_7bit)

def clamp(val, min_val, max_val):
    return max(min_val, min(max_val, val))

def distance_3d(p1, p2):
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)

def calculate_roll_angle(wrist, middle_mcp):
    # Calculate angle in radians between wrist and middle knuckle
    dx = middle_mcp.x - wrist.x
    dy = middle_mcp.y - wrist.y
    angle = math.atan2(dy, dx) # -pi to +pi
    norm_angle = (angle + math.pi) / (2 * math.pi) # 0.0 to 1.0
    return norm_angle

def draw_hand_skeleton(image, landmarks, color):
    h, w, _ = image.shape
    coords = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]
    
    # Draw connections
    for start_idx, end_idx in HAND_CONNECTIONS:
        cv2.line(image, coords[start_idx], coords[end_idx], color, 2)
        
    # Draw joint points
    for pt in coords:
        cv2.circle(image, pt, 4, (255, 255, 255), -1)

def get_working_camera():
    print("Searching for active camera...")
    for idx in range(4):
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                print(f"--> Successfully connected to Camera Index {idx}!")
                return cap
            cap.release()
    return None

def run():
    cap = get_working_camera()
    if cap is None:
        print("\n[ERROR] Could not open any camera (indices 0-3).")
        print("Please check:")
        print(" 1. Camera permissions in System Settings -> Privacy & Security -> Camera -> Terminal.")
        print(" 2. Ensure no other application (Zoom, Photo Booth, FaceTime) is locking the camera.\n")
        return

    controller = HandController(osc_ip="127.0.0.1", osc_port=8000, midi_port_keyword="IAC")
    
    print("\n=======================================================================")
    print("   ADVANCED HAND & FINGER MOTION CONTROLLER - ABLETON & MADMAPPER     ")
    print("=======================================================================")
    print(" Features:")
    print("  - Individual Finger Height Tracking (Thumb, Index, Middle, Ring, Pinky)")
    print("  - Finger Spread Wide vs Together Fan Gesture")
    print("  - Wrist Roll / Rotation Angle")
    print("  - Two-Hand Distance Modulation")
    print(" Controls:")
    print("  'q' - Quit application")
    print("  'm' - Toggle MIDI output ON/OFF")
    print("  'o' - Toggle OSC output ON/OFF")
    window_name = "Advanced Hand Motion Controller"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 960, 540)

    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if 10 <= x <= 620 and 55 <= y <= 75:
                if x < 210:
                    controller.solo_mode = "left_spread"
                    controller.send_midi_cc(0, 11, 64)
                    print("--> CLICKED: LEFT SPREAD (CC 11)")
                elif x < 410:
                    controller.solo_mode = "left_pinch"
                    controller.send_midi_cc(0, 3, 64)
                    print("--> CLICKED: LEFT PINCH (CC 3)")
                else:
                    controller.solo_mode = "left_fist"
                    controller.send_midi_note(0, 60, 100)
                    controller.send_midi_cc(0, 30, 127)
                    print("--> CLICKED: LEFT FIST (Note 60 / CC 30)")
            elif 10 <= x <= 620 and 75 < y <= 95:
                if x < 210:
                    controller.solo_mode = "right_spread"
                    controller.send_midi_cc(0, 17, 64)
                    print("--> CLICKED: RIGHT SPREAD (CC 17)")
                elif x < 410:
                    controller.solo_mode = "right_pinch"
                    controller.send_midi_cc(0, 6, 64)
                    print("--> CLICKED: RIGHT PINCH (CC 6)")
                else:
                    controller.solo_mode = "right_fist"
                    controller.send_midi_note(0, 62, 100)
                    controller.send_midi_cc(0, 31, 127)
                    print("--> CLICKED: RIGHT FIST (Note 62 / CC 31)")
            elif 10 <= x <= 620 and 95 < y <= 120:
                controller.solo_mode = "ALL"
                print("--> CLICKED: LIVE PERFORMANCE MODE (ALL ACTIVE)")

    cv2.setMouseCallback(window_name, mouse_callback)

    fist_state = {"Left": False, "Right": False}
    frame_count = 0
    
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            continue

        image = cv2.flip(image, 1)
        h, w, _ = image.shape
        
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        
        results = controller.detector.detect(mp_image)

        detected_wrists = {}

        if results.hand_landmarks and results.handedness:
            for hand_landmarks, handedness in zip(results.hand_landmarks, results.handedness):
                hand_label = handedness[0].category_name  # "Left" or "Right"
                skeleton_color = (0, 255, 255) if hand_label == "Left" else (255, 0, 255)
                
                # Draw skeleton
                draw_hand_skeleton(image, hand_landmarks, skeleton_color)

                # Key Landmarks
                wrist = hand_landmarks[0]
                thumb_mcp, thumb_tip = hand_landmarks[2], hand_landmarks[4]
                index_mcp, index_tip = hand_landmarks[5], hand_landmarks[8]
                middle_mcp, middle_tip = hand_landmarks[9], hand_landmarks[12]
                ring_mcp, ring_tip = hand_landmarks[13], hand_landmarks[16]
                pinky_mcp, pinky_tip = hand_landmarks[17], hand_landmarks[20]

                detected_wrists[hand_label] = wrist

                # --- Fist Detection (Average distance of fingertips to wrist) ---
                avg_fingers_to_wrist = (
                    distance_3d(index_tip, wrist) +
                    distance_3d(middle_tip, wrist) +
                    distance_3d(ring_tip, wrist) +
                    distance_3d(pinky_tip, wrist)
                ) / 4.0
                is_fist = avg_fingers_to_wrist < 0.23

                # --- Metric 1: Individual Finger Heights & Extensions ---
                palm_scale = distance_3d(wrist, middle_mcp) + 1e-6
                
                if is_fist:
                    thumb_extension = 0.0
                    raw_index_h = 0.0
                    raw_middle_h = 0.0
                    raw_ring_h = 0.0
                    raw_pinky_h = 0.0
                else:
                    # Thumb Extension (Distance from thumb tip to index MCP normalized by palm scale)
                    # Tucked against palm = ~0.65, Stretched out wide = ~1.25
                    raw_thumb_dist = distance_3d(thumb_tip, index_mcp) / palm_scale
                    thumb_extension = clamp((raw_thumb_dist - 0.62) / 0.55, 0.0, 1.0)

                    # Individual finger extension (distance from tip to wrist normalized by full finger length)
                    raw_index_h = clamp((distance_3d(index_tip, wrist) / (1.55 * palm_scale) - 0.45) / 0.55, 0.0, 1.0)
                    raw_middle_h = clamp((distance_3d(middle_tip, wrist) / (1.65 * palm_scale) - 0.45) / 0.55, 0.0, 1.0)
                    raw_ring_h = clamp((distance_3d(ring_tip, wrist) / (1.60 * palm_scale) - 0.45) / 0.55, 0.0, 1.0)
                    raw_pinky_h = clamp((distance_3d(pinky_tip, wrist) / (1.45 * palm_scale) - 0.45) / 0.55, 0.0, 1.0)

                thumb_y = controller.smooth(f"{hand_label}_thumb_y", thumb_extension)
                index_y = controller.smooth(f"{hand_label}_index_y", raw_index_h)
                middle_y = controller.smooth(f"{hand_label}_middle_y", raw_middle_h)
                ring_y = controller.smooth(f"{hand_label}_ring_y", raw_ring_h)
                pinky_y = controller.smooth(f"{hand_label}_pinky_y", raw_pinky_h)

                # Hand Overall Center (Wrist)
                norm_x = controller.smooth(f"{hand_label}_x", wrist.x)
                norm_y = controller.smooth(f"{hand_label}_y", 1.0 - wrist.y)

                # --- Metric 2: Pinch Distance (Thumb Tip to Index Tip) ---
                raw_pinch = distance_3d(thumb_tip, index_tip)
                norm_pinch = controller.smooth(f"{hand_label}_pinch", clamp(raw_pinch / 0.22, 0.0, 1.0))

                # --- Metric 3: Finger Spread (Fan Gesture: Fingers Wide vs Together) ---
                if is_fist:
                    norm_spread = 0.0
                else:
                    spread_gap = (
                        distance_3d(thumb_tip, index_tip) +
                        distance_3d(index_tip, middle_tip) +
                        distance_3d(middle_tip, ring_tip) +
                        distance_3d(ring_tip, pinky_tip)
                    ) / palm_scale
                    # Together ~ 0.8, Wide open spread ~ 1.8
                    norm_spread = clamp((spread_gap - 0.75) / 0.95, 0.0, 1.0)
                    
                norm_spread = controller.smooth(f"{hand_label}_spread", norm_spread)

                # --- Metric 4: Wrist Roll / Rotation Angle ---
                roll_angle = calculate_roll_angle(wrist, middle_mcp)
                norm_roll = controller.smooth(f"{hand_label}_roll", roll_angle)

                # --- Metric 5: Fist Detection ---
                avg_fingers_to_wrist = (
                    distance_3d(index_tip, wrist) +
                    distance_3d(middle_tip, wrist) +
                    distance_3d(ring_tip, wrist) +
                    distance_3d(pinky_tip, wrist)
                ) / 4.0
                is_fist = avg_fingers_to_wrist < 0.22

                # Convert values to 7-bit MIDI (0 - 127)
                midi_x = int(clamp(norm_x * 127, 0, 127))
                midi_y = int(clamp(norm_y * 127, 0, 127))
                midi_pinch = int(clamp(norm_pinch * 127, 0, 127))
                
                midi_index_y = int(clamp(index_y * 127, 0, 127))
                midi_middle_y = int(clamp(middle_y * 127, 0, 127))
                midi_ring_y = int(clamp(ring_y * 127, 0, 127))
                midi_pinky_y = int(clamp(pinky_y * 127, 0, 127))
                midi_thumb_y = int(clamp(thumb_y * 127, 0, 127))
                
                midi_spread = int(clamp(norm_spread * 127, 0, 127))
                midi_roll = int(clamp(norm_roll * 127, 0, 127))

                # --- Route Signals (OSC Address matches Variable Name 1-to-1) ---
                osc_prefix = f"/hand/{hand_label.lower()}"
                
                # Send OSC (MadMapper) - Address matching exact variable names
                controller.send_osc(f"{osc_prefix}/x", norm_x)
                controller.send_osc(f"{osc_prefix}/y", norm_y)
                controller.send_osc(f"{osc_prefix}/pinch", norm_pinch)
                controller.send_osc(f"{osc_prefix}/spread", norm_spread)
                controller.send_osc(f"{osc_prefix}/roll", norm_roll)
                controller.send_osc(f"{osc_prefix}/fist", 1.0 if is_fist else 0.0)

                # Individual finger OSC addresses (matching variable names)
                controller.send_osc(f"{osc_prefix}/thumb_y", thumb_y)
                controller.send_osc(f"{osc_prefix}/index_y", index_y)
                controller.send_osc(f"{osc_prefix}/middle_y", middle_y)
                controller.send_osc(f"{osc_prefix}/ring_y", ring_y)
                controller.send_osc(f"{osc_prefix}/pinky_y", pinky_y)

                # Send MIDI (Ableton Live)
                if hand_label == "Left":
                    controller.send_midi_cc(0, 1, int(clamp(norm_y * 127, 0, 127)))
                    controller.send_midi_cc(0, 2, int(clamp(norm_x * 127, 0, 127)))
                    controller.send_midi_cc(0, 3, int(clamp(norm_pinch * 127, 0, 127)))
                    controller.send_midi_cc(0, 7, int(clamp(index_y * 127, 0, 127)))
                    controller.send_midi_cc(0, 8, int(clamp(middle_y * 127, 0, 127)))
                    controller.send_midi_cc(0, 9, int(clamp(ring_y * 127, 0, 127)))
                    controller.send_midi_cc(0, 10, int(clamp(pinky_y * 127, 0, 127)))
                    controller.send_midi_cc(0, 11, int(clamp(norm_spread * 127, 0, 127)))
                    controller.send_midi_cc(0, 12, int(clamp(norm_roll * 127, 0, 127)))

                    if is_fist and not fist_state["Left"]:
                        controller.send_midi_note(0, 60, 100)
                        controller.send_midi_cc(0, 30, 127)
                        fist_state["Left"] = True
                    elif not is_fist and fist_state["Left"]:
                        controller.send_midi_note(0, 60, 0)
                        controller.send_midi_cc(0, 30, 0)
                        fist_state["Left"] = False

                elif hand_label == "Right":
                    controller.send_midi_cc(0, 4, int(clamp(norm_y * 127, 0, 127)))
                    controller.send_midi_cc(0, 5, int(clamp(norm_x * 127, 0, 127)))
                    controller.send_midi_cc(0, 6, int(clamp(norm_pinch * 127, 0, 127)))
                    controller.send_midi_cc(0, 13, int(clamp(index_y * 127, 0, 127)))
                    controller.send_midi_cc(0, 14, int(clamp(middle_y * 127, 0, 127)))
                    controller.send_midi_cc(0, 15, int(clamp(ring_y * 127, 0, 127)))
                    controller.send_midi_cc(0, 16, int(clamp(pinky_y * 127, 0, 127)))
                    controller.send_midi_cc(0, 17, int(clamp(norm_spread * 127, 0, 127)))
                    controller.send_midi_cc(0, 18, int(clamp(norm_roll * 127, 0, 127)))

                    if is_fist and not fist_state["Right"]:
                        controller.send_midi_note(0, 62, 100)
                        controller.send_midi_cc(0, 31, 127)
                        fist_state["Right"] = True
                    elif not is_fist and fist_state["Right"]:
                        controller.send_midi_note(0, 62, 0)
                        controller.send_midi_cc(0, 31, 0)
                        fist_state["Right"] = False

                # Convert to Percentages (0% - 100%)
                thumb_pct = int(clamp(thumb_y * 100, 0, 100))
                index_pct = int(clamp(index_y * 100, 0, 100))
                middle_pct = int(clamp(middle_y * 100, 0, 100))
                ring_pct = int(clamp(ring_y * 100, 0, 100))
                pinky_pct = int(clamp(pinky_y * 100, 0, 100))
                spread_pct = int(clamp(norm_spread * 100, 0, 100))
                roll_pct = int(clamp(norm_roll * 100, 0, 100))
                pinch_pct = int(clamp(norm_pinch * 100, 0, 100))

                # Floating Telemetry Box near wrist
                wx, wy = int(wrist.x * w), int(wrist.y * h)
                box_w = 280
                box_h = 160
                
                # Keep box within screen boundaries
                box_x = max(10, min(w - box_w - 10, wx - 10))
                box_y = max(10, min(h - box_h - 10, wy + 15))

                cv2.rectangle(image, (box_x, box_y), (box_x + box_w, box_y + box_h), (10, 10, 10), -1)
                cv2.rectangle(image, (box_x, box_y), (box_x + box_w, box_y + box_h), skeleton_color, 1)

                cv2.putText(image, f"{hand_label.upper()} HAND TELEMETRY", (box_x + 10, box_y + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 2)
                
                # Finger Percentages Row 1
                cv2.putText(image, f"Thumb: {thumb_pct:3d}%  |  Index: {index_pct:3d}%", (box_x + 10, box_y + 45), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
                cv2.putText(image, f"Middle:{middle_pct:3d}%  |  Ring:  {ring_pct:3d}%", (box_x + 10, box_y + 65), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
                cv2.putText(image, f"Pinky: {pinky_pct:3d}%", (box_x + 10, box_y + 85), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
                
                # Gesture Percentages Row 2
                cv2.putText(image, f"Spread (Fan):  {spread_pct:3d}%", (box_x + 10, box_y + 110), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
                cv2.putText(image, f"Pinch: {pinch_pct:3d}%  |  Roll: {roll_pct:3d}%", (box_x + 10, box_y + 130), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 255), 1)
                cv2.putText(image, f"Fist: {'YES' if is_fist else 'NO'}", (box_x + 10, box_y + 150), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)

                # Fingertip visual indicators for all 5 fingers with percentage labels
                fingers_info = [
                    (thumb_tip, thumb_pct, "T"),
                    (index_tip, index_pct, "I"),
                    (middle_tip, middle_pct, "M"),
                    (ring_tip, ring_pct, "R"),
                    (pinky_tip, pinky_pct, "P")
                ]
                for tip, pct, name in fingers_info:
                    fx, fy = int(tip.x * w), int(tip.y * h)
                    cv2.circle(image, (fx, fy), 6, (0, 255, 0), -1)
                    cv2.putText(image, f"{pct}%", (fx - 12, fy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)

        # --- Metric 6: Two-Hand Distance (When both hands visible) ---
        if "Left" in detected_wrists and "Right" in detected_wrists:
            lw = detected_wrists["Left"]
            rw = detected_wrists["Right"]
            raw_dist = distance_3d(lw, rw)
            norm_two_hand_dist = controller.smooth("two_hand_dist", clamp(raw_dist / 0.8, 0.0, 1.0))
            midi_two_hand = int(clamp(norm_two_hand_dist * 127, 0, 127))

            controller.send_osc("/hand/two_hand_distance", norm_two_hand_dist)
            controller.send_midi_cc(0, 19, midi_two_hand) # CC 19: Two-Hand Distance

            # Draw connecting line between hands
            lx, ly = int(lw.x * w), int(lw.y * h)
            rx, ry = int(rw.x * w), int(rw.y * h)
            cv2.line(image, (lx, ly), (rx, ry), (0, 255, 255), 2)
            
            # Midpoint text
            mx, my = (lx + rx) // 2, (ly + ry) // 2
            cv2.putText(image, f"2-Hand Dist: {norm_two_hand_dist:.2f} (CC#19)", (mx - 80, my - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 2)

        # --- Auto-reset solo_mode to LIVE MODE after 5s ---
        if controller.solo_mode != "ALL" and (time.time() - controller.solo_timestamp > 5.0):
            controller.solo_mode = "ALL"
            print("--> Auto-returned to LIVE PERFORMANCE MODE (All Gestures Active)")

        # --- Top HUD Header & Quick-Map Menu ---
        cv2.rectangle(image, (10, 10), (620, 115), (15, 15, 15), -1)
        cv2.rectangle(image, (10, 10), (620, 115), (80, 80, 80), 1)

        midi_status_color = (0, 255, 0) if controller.midi_enabled else (0, 0, 255)
        osc_status_color = (0, 255, 0) if controller.osc_enabled else (0, 0, 255)
        
        cv2.putText(image, f"MIDI Out (IAC Bus 1): {'ACTIVE' if controller.midi_enabled else 'OFF'}  |  OSC Out (8000): {'ACTIVE' if controller.osc_enabled else 'OFF'}", (20, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (220, 220, 220), 1)

        cv2.putText(image, "QUICK-MAP KEYS (In Ableton Cmd+M):", (20, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 255, 255), 1)
        cv2.putText(image, "[1] L-Spread (CC11)  [2] L-Pinch (CC3)  [3] L-Fist (Note60/CC30)", (20, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 200, 200), 1)
        cv2.putText(image, "[4] R-Spread (CC17)  [5] R-Pinch (CC6)  [6] R-Fist (Note62/CC31)", (20, 88), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 200, 200), 1)
        
        mode_text = f"ACTIVE MODE: {controller.solo_mode.upper()}  ([0] LIVE MODE)"
        mode_color = (0, 255, 0) if controller.solo_mode == "ALL" else (0, 255, 255)
        cv2.putText(image, mode_text, (20, 108), cv2.FONT_HERSHEY_SIMPLEX, 0.40, mode_color, 2)

        cv2.imshow("Advanced Hand Motion Controller", image)

        key = cv2.waitKey(5) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('m'):
            controller.midi_enabled = not controller.midi_enabled
            print(f"MIDI Toggled: {controller.midi_enabled}")
        elif key == ord('o'):
            controller.osc_enabled = not controller.osc_enabled
            print(f"OSC Toggled: {controller.osc_enabled}")
        elif key == ord('1'):
            controller.set_solo_mode("left_spread")
            controller.send_midi_cc(0, 11, 64)
            print("--> QUICK-MAP TRIGGER: LEFT SPREAD (CC 11)")
        elif key == ord('2'):
            controller.set_solo_mode("left_pinch")
            controller.send_midi_cc(0, 3, 64)
            print("--> QUICK-MAP TRIGGER: LEFT PINCH (CC 3)")
        elif key == ord('3'):
            controller.set_solo_mode("left_fist")
            controller.send_midi_note(0, 60, 100)
            controller.send_midi_cc(0, 30, 127)
            print("--> QUICK-MAP TRIGGER: LEFT FIST (Note 60 / CC 30)")
        elif key == ord('4'):
            controller.set_solo_mode("right_spread")
            controller.send_midi_cc(0, 17, 64)
            print("--> QUICK-MAP TRIGGER: RIGHT SPREAD (CC 17)")
        elif key == ord('5'):
            controller.set_solo_mode("right_pinch")
            controller.send_midi_cc(0, 6, 64)
            print("--> QUICK-MAP TRIGGER: RIGHT PINCH (CC 6)")
        elif key == ord('6'):
            controller.set_solo_mode("right_fist")
            controller.send_midi_note(0, 62, 100)
            controller.send_midi_cc(0, 31, 127)
            print("--> QUICK-MAP TRIGGER: RIGHT FIST (Note 62 / CC 31)")
        elif key == ord('7'):
            controller.set_solo_mode("left_height")
            controller.send_midi_cc(0, 1, 64)
            print("--> QUICK-MAP TRIGGER: LEFT HEIGHT (CC 1)")
        elif key == ord('8'):
            controller.set_solo_mode("right_height")
            controller.send_midi_cc(0, 4, 64)
            print("--> QUICK-MAP TRIGGER: RIGHT HEIGHT (CC 4)")
        elif key == ord('9'):
            controller.set_solo_mode("wrist_roll")
            controller.send_midi_cc(0, 12, 64)
            controller.send_midi_cc(0, 18, 64)
            print("--> QUICK-MAP TRIGGER: WRIST ROLL (CC 12 & 18)")
        elif key in (ord('0'), ord(' ')):
            controller.solo_mode = "ALL"
            print("--> NORMAL LIVE PERFORMANCE MODE (ALL GESTURES ACTIVE)")

    cap.release()
    cv2.destroyAllWindows()
    if controller.midi_output:
        controller.midi_output.close()
    print("Application closed successfully.")

if __name__ == "__main__":
    run()
