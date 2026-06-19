import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 6000))

print("Telemetry server listening")

while True:
    data, addr = sock.recvfrom(4096)
    print("TELEM:", data.decode())