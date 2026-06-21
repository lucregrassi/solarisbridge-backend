# SOLARIS Bridge — Backend (PC side)

PC-side companion scripts for the **SOLARIS Bridge** Android apps. They talk to the app over the
local network: they **receive** telemetry and video from the drone/app, and **send** flight, gimbal
and goto commands to it.

This repository is the counterpart of the Android project: the app runs on a device connected to the
DJI remote controller, and these scripts run on a PC on the same network.

---

## Requirements

- Python 3.8+
- Dependencies (see `requirements.txt`):

```bash
pip install -r requirements.txt
```

- `opencv-python` and `numpy` — video display
- `av` (PyAV, bundles ffmpeg's H.264 decoder) — H.264 video decoding

---

## Network configuration

The ports must match the ones configured in the app's settings screen. Defaults:

| Direction      | Purpose                 | Protocol | Default port |
|----------------|-------------------------|----------|--------------|
| Drone → PC     | telemetry               | UDP      | `6000`       |
| Drone → PC     | video                   | TCP      | `6001`       |
| PC → Drone     | flight commands         | UDP      | `7000`       |
| PC → Drone     | gimbal commands         | UDP      | `7001`       |
| PC → Drone     | goto / waypoint (V4)    | UDP      | `7002`       |

**How addressing works:**

- **Receivers** (`receive_*.py`) bind `0.0.0.0` on the PC and just listen — no IP to configure.
- **Senders** (`send_*.py`) must target the **Android device IP**: edit the `IP` constant at the top
  of each script (you can read the device IP in the app's Settings screen).

---

## Scripts

### Receiving (Drone → PC)

- **`receive_telemetry.py`** — listens on UDP `6000` and prints the telemetry JSON. For the V4 app
  this includes the autonomous-navigation fields `goto_state` (`idle`/`enroute`/`arrived`/`failed`),
  `altitude_rel_takeoff` and `is_flying`.
- **`receive_h264_v4.py`** — preferred V4 video receiver. Decodes the raw H.264 stream forwarded by
  the app and shows it with OpenCV. Low-latency decode settings.
- **`receive_h264_v5.py`** — V5 video receiver (encoded camera stream).

Video wire format on TCP `6001` (big-endian):

- H.264 (V4/V5): `MAGIC ("VSTR")` + `length (int32)` + frame bytes

In the video windows, press `q` or `ESC` to disconnect.

### Sending (PC → Drone)

- **`send_drone_commands.py`** — streams Virtual Stick commands on UDP `7000` at 20 Hz:
  `{vx, vy, yaw, throttle}`. A continuous stream is required (the app zeroes the command after
  ~250 ms via a watchdog).
- **`send_gimbal_commands.py`** — sends a gimbal command on UDP `7001`: `{yaw, pitch, roll}` (degrees).
- **`send_goto_commands.py`** — sends a goto/waypoint command on UDP `7002` (**V4 only**):
  `{lat, lon, alt, speed, heading?}`. Edit the target values at the top of the script and run it.

```jsonc
// goto message format (port 7002)
{ "lat": 44.4012, "lon": 8.9560, "alt": 20.0, "speed": 3.0, "heading": 90.0 }
```

- `lat`, `lon` — target coordinates (WGS84 decimal degrees)
- `alt` — target altitude in metres **relative to the takeoff point**
- `speed` — cruise speed in m/s
- `heading` — *optional* aircraft heading at the target (degrees, `-180..180`); omit to follow the
  direction of travel

---

## Typical usage

Edit the `IP` at the top of the send scripts to your device IP, then in separate terminals:

```bash
# Terminal 1 — telemetry (also shows goto_state for the V4 mission)
python receive_telemetry.py

# Terminal 2 — video (V4)
python receive_h264_v4.py

# Terminal 3 — send commands
python send_drone_commands.py     # manual Virtual Stick stream
python send_gimbal_commands.py    # gimbal
python send_goto_commands.py      # autonomous goto (V4)
```

### Autonomous goto workflow (V4)

The V4 app can fly the drone autonomously to a GPS target (DJI Waypoint Mission) and reports progress
through the `goto_state` telemetry field. Typical flow:

1. Arm PC control on the **phone** (command button) — arming cannot be done from the PC.
2. Run `receive_telemetry.py` to watch `goto_state`.
3. Edit the target in `send_goto_commands.py` and run it. You should see
   `goto_state: idle → enroute → arrived` (or `failed` if something goes wrong).
4. After arrival the app re-enables manual control: resume sending `send_drone_commands.py`.

A valid, non-zero flight command sent during a mission aborts it and returns to manual control
(manual override).

---

## Safety

These scripts drive a real DJI aircraft. Always test in a safe environment.

- Test first with **propellers removed** whenever possible.
- The goto requires a healthy GPS fix and the aircraft to be flying; indoors the mission is rejected
  by design. A successful `arrived` can only be observed in real flight or in the DJI simulator.
- Verify the command axis mapping and the goto altitude reference (relative to takeoff) before flight.
- Keep a manual recovery procedure available at all times.

---

## Acknowledgment

This repository was developed within the framework of the European Union SOLARIS project.

The work was supported by the European Union under the SOLARIS project (grant agreement no. 101146377).

More information is available on the [SOLARIS project website](https://solaris-heu.eu/).

---

## Author

Lucrezia Grassi
GitHub: [lucregrassi](https://github.com/lucregrassi)

Email: [lucrezia.grassi@unige.it](mailto:lucrezia.grassi@unige.it)
