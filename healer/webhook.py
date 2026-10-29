"""Receives Alertmanager webhooks and runs the matching Ansible remediation."""
import json
import os
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LOG_FILE = os.environ.get("LOG_FILE", "/logs/healing.log")
PLAYBOOK = os.environ.get("PLAYBOOK", "/ansible/heal.yml")
INVENTORY = os.environ.get("INVENTORY", "/ansible/inventory.ini")
PORT = int(os.environ.get("PORT", "5001"))
KNOWN_ALERTS = {"NginxDown", "HighCpuUsage"}
lock = threading.Lock()


def log(message):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def heal(alertname, instance):
    if not lock.acquire(blocking=False):
        log(f"SKIP  {alertname}: another healing run is in progress")
        return
    try:
        log(f"HEAL  start alert={alertname} instance={instance}")
        extra = ["-e", f"alertname={alertname}"]
        if os.environ.get("VERIFY_URL"):
            extra += ["-e", f"verify_url={os.environ['VERIFY_URL']}"]
        result = subprocess.run(
            ["ansible-playbook", "-i", INVENTORY, PLAYBOOK] + extra,
            capture_output=True, text=True, timeout=180,
        )
        for line in (result.stdout + result.stderr).splitlines():
            if line.strip():
                log(f"ansible | {line}")
        status = "OK" if result.returncode == 0 else "FAILED"
        log(f"HEAL  {status} alert={alertname}")
    except Exception as exc:  # keep the server alive whatever happens
        log(f"HEAL  ERROR alert={alertname}: {exc}")
    finally:
        lock.release()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"healer is running\n")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return
        for alert in payload.get("alerts", []):
            name = alert.get("labels", {}).get("alertname", "unknown")
            instance = alert.get("labels", {}).get("instance", "-")
            status = alert.get("status")
            if status == "resolved":
                log(f"ALERT resolved: {name} {instance}")
            elif name in KNOWN_ALERTS:
                log(f"ALERT firing: {name} {instance}")
                threading.Thread(target=heal, args=(name, instance), daemon=True).start()
            else:
                log(f"ALERT ignored (no playbook): {name}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok\n")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    log(f"healer listening on :{PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
