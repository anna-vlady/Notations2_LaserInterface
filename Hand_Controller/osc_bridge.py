import mido
from pythonosc import dispatcher, osc_server
import time

# --- Setup Virtual MIDI Output to Ableton Live ---
midi_port_name = None
outputs = mido.get_output_names()
print("\n=======================================================")
print("          OSC TO ABLETON LIVE BRIDGE                   ")
print("=======================================================")
print("Available MIDI Outputs:")
for name in outputs:
    print(f" - {name}")
    if "iac" in name.lower() and midi_port_name is None:
        midi_port_name = name

if midi_port_name is None and outputs:
    midi_port_name = outputs[0]

if midi_port_name:
    midi_out = mido.open_output(midi_port_name)
    print(f"--> Connected to Virtual MIDI Output: '{midi_port_name}'")
else:
    midi_out = None
    print("[WARNING] No MIDI outputs found. Enable IAC Driver in Audio MIDI Setup.")

def clamp(val, min_val, max_val):
    return max(min_val, min(max_val, val))

# --- Address Mapping Dictionary ---
# Maps incoming OSC addresses to Ableton MIDI Control Change (CC) channels/numbers
OSC_MIDI_MAP = {
    "/hand/left/y":         {"channel": 0, "cc": 1,  "label": "Left Hand Volume / Cutoff"},
    "/hand/left/x":         {"channel": 0, "cc": 2,  "label": "Left Hand Pan"},
    "/hand/left/pinch":     {"channel": 0, "cc": 3,  "label": "Left Hand FX Dry/Wet"},
    "/hand/right/y":        {"channel": 0, "cc": 4,  "label": "Right Hand Volume / Speed"},
    "/hand/right/x":        {"channel": 0, "cc": 5,  "label": "Right Hand Pan / Crossfader"},
    "/hand/right/pinch":    {"channel": 0, "cc": 6,  "label": "Right Hand Delay Feedback"},
    "/hand/left/index_y":   {"channel": 0, "cc": 7,  "label": "Left Index Finger Y"},
    "/hand/left/middle_y":  {"channel": 0, "cc": 8,  "label": "Left Middle Finger Y"},
    "/hand/left/spread":    {"channel": 0, "cc": 11, "label": "Left Finger Spread Wide"},
    "/hand/right/index_y":  {"channel": 0, "cc": 13, "label": "Right Index Finger Y"},
    "/hand/right/middle_y": {"channel": 0, "cc": 14, "label": "Right Middle Finger Y"},
    "/hand/right/spread":   {"channel": 0, "cc": 17, "label": "Right Finger Spread Wide"},
    "/hand/two_hand_distance": {"channel": 0, "cc": 19, "label": "Two-Hand Distance"}
}

def osc_handler(address, *args):
    if not args:
        return
    val = float(args[0])
    
    if address in OSC_MIDI_MAP:
        mapping = OSC_MIDI_MAP[address]
        # Convert float (0.0 - 1.0) to MIDI 7-bit (0 - 127)
        val_7bit = int(clamp(val * 127.0, 0, 127))
        
        if midi_out:
            msg = mido.Message('control_change', channel=mapping["channel"], control=mapping["cc"], value=val_7bit)
            midi_out.send(msg)
            print(f"[OSC -> Ableton] Address: {address:25s} | Value: {val:.2f} -> MIDI CC#{mapping['cc']:2d}: {val_7bit:3d} ({mapping['label']})")

def main():
    disp = dispatcher.Dispatcher()
    # Map all defined OSC addresses
    for addr in OSC_MIDI_MAP.keys():
        disp.map(addr, osc_handler)

    # Listen on port 8000
    server_ip = "127.0.0.1"
    server_port = 8000
    server = osc_server.ThreadingOSCUDPServer((server_ip, server_port), disp)
    print(f"\n[OSC Bridge Running] Listening on UDP {server_ip}:{server_port}")
    print("Press Ctrl+C to stop.\n")
    server.serve_forever()

if __name__ == "__main__":
    main()
