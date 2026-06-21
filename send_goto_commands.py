import socket
import json

# --- Configurazione ---
IP = "192.168.1.18"   # IP del dispositivo Android che esegue SOLARIS Bridge
PORT = 7002           # porta dei comandi goto/waypoint

# --- Target da raggiungere ---
LAT = 44.4012         # latitudine (gradi decimali)
LON = 8.9560          # longitudine (gradi decimali)
ALT = 20.0            # quota in metri SOPRA IL PUNTO DI DECOLLO
SPEED = 3.0           # velocita di crociera in m/s
HEADING = 90.0        # orientamento all'arrivo in gradi (-180..180); None per orientarsi nella direzione di marcia

# --- Invio ---
msg = {"lat": LAT, "lon": LON, "alt": ALT, "speed": SPEED}
if HEADING is not None:
    msg["heading"] = HEADING

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(json.dumps(msg).encode(), (IP, PORT))
sock.close()

print("GOTO inviato:", msg)
