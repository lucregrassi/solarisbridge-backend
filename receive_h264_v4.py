"""
SOLARIS Bridge V4 - PC-side H.264 receiver.

Replaces receive_jpeg_v4.py. The phone now forwards the RAW H.264 elementary
stream coming from the DJI video feed (no JPEG re-encode), so this script
decodes H.264 instead of decoding per-frame JPEGs.

Wire format on the TCP socket (big-endian), produced by EncodedVideoStreamer:
    MAGIC ("VSTR") + length (int32) + frame bytes
Note: there is NO 1-byte "type" field anymore (that existed only in the old
JPEG protocol).

Dependencies:
    pip install av opencv-python numpy
(`av` is PyAV, which bundles ffmpeg's H.264 decoder.)

Run:
    python receive_h264_v4.py
Press 'q' or ESC in the video window to disconnect.
"""

import socket
import struct

import av
import cv2

HOST = "0.0.0.0"
PORT = 6001
MAGIC = b"VSTR"

WINDOW_NAME = "SOLARIS Bridge V4 H.264 Stream"


def recv_exact(sock, size):
    """Read exactly `size` bytes, or return None if the peer disconnects."""
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            return None
        data += chunk
    return bytes(data)


def show_frame(frame, frame_count):
    """Display one decoded frame. Returns False if the user asked to quit."""
    img = frame.to_ndarray(format="bgr24")
    cv2.imshow(WINDOW_NAME, img)

    key = cv2.waitKey(1) & 0xFF
    if key == 27 or key == ord("q"):
        print("[PC] Window closed by user")
        return False

    if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
        print("[PC] Window manually closed")
        return False

    return True


def handle_client(conn, addr):
    print(f"[PC] Client connected from {addr}")
    conn.settimeout(10.0)

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

    # One decoder per connection. PyAV's parser reassembles NAL units from the
    # arbitrary byte chunks the phone sends, so we don't need frame alignment.
    codec = av.CodecContext.create("h264", "r")

    # --- Low-latency decode settings ---
    # Slice threading (instead of frame threading) avoids holding several frames
    # in flight, which is the main source of decoder-side latency.
    try:
        codec.thread_type = "SLICE"
    except Exception:
        pass
    # LOW_DELAY tells the decoder not to wait/reorder for B-frames (the DJI feed
    # has none anyway), so each frame is output as soon as it is decoded.
    try:
        codec.flags |= av.codec.context.Flags.low_delay
    except Exception:
        try:
            codec.flags |= av.codec.context.Flags.LOW_DELAY  # older PyAV
        except Exception:
            pass

    chunk_count = 0       # raw H.264 chunks received from the phone
    bytes_total = 0
    frame_count = 0       # successfully decoded video frames
    keep_going = True

    try:
        while keep_going:
            magic = recv_exact(conn, 4)
            if magic is None:
                print("[PC] Client disconnected (magic)")
                break
            if magic != MAGIC:
                print(f"[PC] Invalid magic: {magic!r}")
                break

            raw_len = recv_exact(conn, 4)
            if raw_len is None:
                print("[PC] Client disconnected (length)")
                break
            length = struct.unpack(">I", raw_len)[0]

            payload = recv_exact(conn, length)
            if payload is None:
                print("[PC] Client disconnected (payload)")
                break

            # --- DIAGNOSTIC: proof that bytes are arriving from the phone ---
            chunk_count += 1
            bytes_total += length
            if chunk_count <= 10 or chunk_count % 30 == 0:
                print(f"[PC] chunk #{chunk_count}: {length} B "
                      f"(tot {bytes_total // 1024} KB, decoded frames {frame_count})")

            # Feed the chunk to the H.264 parser/decoder.
            try:
                packets = codec.parse(payload)
            except Exception as e:
                print(f"[PC] parse error: {e}")
                continue

            for packet in packets:
                try:
                    frames = codec.decode(packet)
                except Exception:
                    # Corrupt/incomplete data (e.g. after a dropped frame):
                    # skip until the next keyframe arrives. Self-healing.
                    continue

                for frame in frames:
                    frame_count += 1
                    if frame_count == 1:
                        print("[PC] First frame decoded - video should appear now.")
                    if not show_frame(frame, frame_count):
                        keep_going = False
                        break
                if not keep_going:
                    break

    except socket.timeout:
        print("[PC] Timeout waiting for data")
    except Exception as e:
        print(f"[PC] Error: {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass
        cv2.destroyAllWindows()
        cv2.waitKey(1)
        print("[PC] Connection closed\n")


def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(1)

    print(f"[PC] Listening on {HOST}:{PORT}")

    while True:
        conn, addr = srv.accept()
        print(f"[PC] Incoming connection from {addr}")
        handle_client(conn, addr)


if __name__ == "__main__":
    main()