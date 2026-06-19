import socket
import json
import time

IP = "192.168.1.18"
PORT = 7000
HZ = 20
DT = 1.0 / HZ

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def send(vx=0.0, vy=0.0, yaw=0.0, throttle=0.0):
    msg = {
        "vx": float(vx),
        "vy": float(vy),
        "yaw": float(yaw),
        "throttle": float(throttle),
    }
    sock.sendto(json.dumps(msg).encode(), (IP, PORT))


def hold(vx=0.0, vy=0.0, yaw=0.0, throttle=0.0, seconds=1.0):
    n = int(seconds * HZ)
    for _ in range(n):
        send(vx, vy, yaw, throttle)
        time.sleep(DT)


try:
    # zero iniziale
    hold(0.0, 0.0, 0.0, 0.0, 5.0)

    # avanti piano per 2 secondi
    print("Avanti piano per 2s")
    hold(vx=0.3, vy=0.0, yaw=0.0, throttle=0, seconds=5.0)

    # fermo per 5 secondi
    print("Stop per 5s")
    hold(vx=0.0, vy=0.1, yaw=0.0, throttle=0.0, seconds=5.0)

    # fermo finale
    print("Stop finale")
    hold(vx=0.0, vy=0.0, yaw=-15, throttle=0.0, seconds=5.0)

finally:
    # zero finale di sicurezza
    hold(vx=0.0, vy=0.0, yaw=0.0, throttle=-0.2, seconds=5.0)
    sock.close()
