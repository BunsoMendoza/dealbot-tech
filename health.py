import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from datetime import datetime

POSTED_DB = os.getenv("POSTED_DB", "posted.json")
LAST_RUN_FILE = os.getenv("LAST_RUN_FILE", "last_run.txt")


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/health"):
            info = {"status": "ok", "timestamp": datetime.utcnow().isoformat() + "Z"}
            # posted count
            try:
                if os.path.exists(POSTED_DB):
                    with open(POSTED_DB, "r", encoding="utf-8") as fh:
                        posted = json.load(fh)
                        info["posted_count"] = len(posted)
                else:
                    info["posted_count"] = 0
            except Exception:
                info["posted_count"] = None

            # last run
            try:
                if os.path.exists(LAST_RUN_FILE):
                    with open(LAST_RUN_FILE, "r", encoding="utf-8") as fh:
                        info["last_run"] = fh.read().strip()
                else:
                    info["last_run"] = None
            except Exception:
                info["last_run"] = None

            payload = json.dumps(info).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(404)
            self.end_headers()


def run_health_server(port: int = 8000):
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


if __name__ == "__main__":
    port = int(os.getenv("HEALTH_PORT", "8000"))
    print(f"Starting health server on :{port}")
    run_health_server(port)
    import time
    while True:
        time.sleep(60)
