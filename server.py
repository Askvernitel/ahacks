#!/usr/bin/env python3
"""
BeeBuzz backend.

Reads amplitude values from the Arduino on a serial port (default COM7) on THIS
PC, and streams them to any browser over Server-Sent Events. This lets a phone
on the same network see the live data even though the Bluetooth/serial link is
paired to the PC.

Usage:
    python server.py                  # COM7, port 8000
    python server.py COM5             # different serial port
    python server.py COM7 8080        # serial port + http port

Requires: pyserial   ->   pip install pyserial

Then open:
    http://localhost:8000/            (on this PC)
    http://<this-PC-IP>:8000/         (from a phone on the same Wi-Fi)
and click "Connect (server)".
"""

import sys
import os
import json
import queue
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

try:
    import serial  # pyserial
except ImportError:
    print("Missing dependency. Run:  pip install pyserial")
    sys.exit(1)

SERIAL_PORT = sys.argv[1] if len(sys.argv) > 1 else "COM7"
HTTP_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
BAUD = 9600
DIR = os.path.dirname(os.path.abspath(__file__))

# Set of subscriber queues (one per connected browser).
subscribers = set()
subscribers_lock = threading.Lock()
latest = {"amp": None}


def broadcast(amp):
    latest["amp"] = amp
    with subscribers_lock:
        dead = []
        for q in subscribers:
            try:
                q.put_nowait(amp)
            except queue.Full:
                dead.append(q)
        for q in dead:
            subscribers.discard(q)


def serial_loop():
    """Continuously read the serial port, reconnecting if it drops."""
    while True:
        try:
            print(f"[serial] opening {SERIAL_PORT} @ {BAUD}...")
            with serial.Serial(SERIAL_PORT, BAUD, timeout=1) as ser:
                print(f"[serial] connected to {SERIAL_PORT}")
                while True:
                    line = ser.readline().decode("utf-8", "ignore").strip()
                    if not line:
                        continue
                    try:
                        amp = int(float(line))
                    except ValueError:
                        continue
                    broadcast(amp)
        except serial.SerialException as e:
            print(f"[serial] error: {e} — retrying in 3s")
        except Exception as e:
            print(f"[serial] unexpected: {e} — retrying in 3s")
        threading.Event().wait(3)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # quiet

    def do_GET(self):
        if self.path.startswith("/stream"):
            return self.handle_stream()
        if self.path.startswith("/status"):
            return self.handle_status()
        return self.handle_static()

    def handle_status(self):
        body = json.dumps({"port": SERIAL_PORT, "amp": latest["amp"]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def handle_stream(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        q = queue.Queue(maxsize=1000)
        with subscribers_lock:
            subscribers.add(q)
        try:
            while True:
                try:
                    amp = q.get(timeout=15)
                    self.wfile.write(f"data: {amp}\n\n".encode())
                except queue.Empty:
                    self.wfile.write(b": keep-alive\n\n")  # heartbeat
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            with subscribers_lock:
                subscribers.discard(q)

    def handle_static(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", ""):
            path = "/index.html"
        fpath = os.path.normpath(os.path.join(DIR, path.lstrip("/")))
        if not fpath.startswith(DIR) or not os.path.isfile(fpath):
            self.send_error(404)
            return
        ctype = "text/html" if fpath.endswith(".html") else "application/octet-stream"
        with open(fpath, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    threading.Thread(target=serial_loop, daemon=True).start()
    server = ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), Handler)
    print(f"[http] serving {DIR} on http://0.0.0.0:{HTTP_PORT}")
    print(f"[http] phone URL: http://<this-PC-IP>:{HTTP_PORT}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    main()
