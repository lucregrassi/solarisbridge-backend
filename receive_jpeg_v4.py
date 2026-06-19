import socket
import struct
import cv2
import numpy as np

HOST = "0.0.0.0"
PORT = 6001
MAGIC = b"VSTR"
TYPE_JPEG = 2


def recv_exact(sock, size):
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            return None
        data += chunk
    return data


def handle_client(conn, addr):
    print(f"[PC] Client connected from {addr}")
    conn.settimeout(10.0)

    window_name = "SOLARIS Bridge V4 JPEG Stream"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    frame_count = 0

    try:
        while True:
            magic = recv_exact(conn, 4)
            if magic is None:
                print("[PC] Client disconnected (magic)")
                break

            if magic != MAGIC:
                print(f"[PC] Invalid magic: {magic}")
                break

            raw_type = recv_exact(conn, 1)
            if raw_type is None:
                print("[PC] Client disconnected (type)")
                break

            packet_type = raw_type[0]

            raw_len = recv_exact(conn, 4)
            if raw_len is None:
                print("[PC] Client disconnected (length)")
                break

            length = struct.unpack(">I", raw_len)[0]
            payload = recv_exact(conn, length)
            if payload is None:
                print("[PC] Client disconnected (payload)")
                break

            if packet_type != TYPE_JPEG:
                print(f"[PC] Unsupported packet type: {packet_type}")
                continue

            arr = np.frombuffer(payload, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

            if img is None:
                print("[PC] JPEG decode failed")
                continue

            frame_count += 1
            h, w = img.shape[:2]
            print(f"[PC] frame #{frame_count}: {w}x{h}")

            cv2.imshow(window_name, img)

            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord("q"):
                print("[PC] Window closed by user")
                break

            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                print("[PC] Window manually closed")
                break

    except socket.timeout:
        print("[PC] Timeout waiting for data")
    except Exception as e:
        print(f"[PC] Error: {e}")
    finally:
        try:
            conn.close()
        except:
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