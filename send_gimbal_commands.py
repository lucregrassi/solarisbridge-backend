import socket, json

IP = "10.186.13.8"
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dt = 1/20


msg = {"yaw": 0, "pitch": 0, "roll": 0}
s.sendto(json.dumps(msg).encode(), (IP, 7001))
