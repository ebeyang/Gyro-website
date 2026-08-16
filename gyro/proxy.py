# proxy.py
# Simple CORS proxy for development only.
# Usage: python proxy.py
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import urllib.request, urllib.error, sys, json

# Target Apps Script exec URL (your web app)
TARGET = "https://script.google.com/macros/s/AKfycbw-sWo8Kpz0NaIEDPgrASie_7M6HXjoxs1Jgdcbqws4k9P4WwFBPh5wSVIGl7Q3SrBp/exec"
LISTEN_HOST = "localhost"
LISTEN_PORT = 8010

class ProxyHandler(BaseHTTPRequestHandler):
    def _set_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors()
        self.end_headers()

    def do_GET(self):
        # forward GET to TARGET with query string
        url = TARGET + ("?" + self.path.split("?",1)[1] if "?" in self.path else "")
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=20) as r:
                body = r.read()
                status = r.getcode()
                ctype = r.headers.get('Content-Type','application/octet-stream')
        except urllib.error.HTTPError as e:
            body = e.read()
            status = e.code
            ctype = e.headers.get('Content-Type','application/octet-stream') if e.headers else 'application/json'
        except Exception as e:
            self.send_response(502)
            self._set_cors()
            self.send_header("Content-Type","text/plain")
            self.end_headers()
            self.wfile.write(str(e).encode())
            return

        self.send_response(status)
        self._set_cors()
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        payload = self.rfile.read(length) if length else b''
        try:
            req = urllib.request.Request(TARGET, data=payload, method="POST")
            req.add_header("Content-Type", self.headers.get("Content-Type","application/json"))
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read()
                status = r.getcode()
                ctype = r.headers.get('Content-Type','application/octet-stream')
        except urllib.error.HTTPError as e:
            body = e.read()
            status = e.code
            ctype = e.headers.get('Content-Type','application/octet-stream') if e.headers else 'application/json'
        except Exception as e:
            self.send_response(502)
            self._set_cors()
            self.send_header("Content-Type","text/plain")
            self.end_headers()
            self.wfile.write(str(e).encode())
            return

        self.send_response(status)
        self._set_cors()
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(body)

if __name__ == "__main__":
    print(f"Starting CORS proxy on http://{LISTEN_HOST}:{LISTEN_PORT}/proxy -> {TARGET}")
    server = HTTPServer((LISTEN_HOST, LISTEN_PORT), ProxyHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping proxy")
        server.server_close()