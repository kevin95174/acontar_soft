"""Small authenticated HTTP endpoint for printing labels over the local Wi-Fi."""

import json
import queue
import secrets
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class LocalPrintServer:
    def __init__(self, port=8765):
        self.port = port
        self.token = secrets.token_urlsafe(18)
        self.jobs = queue.Queue()
        self.server = ThreadingHTTPServer(("0.0.0.0", port), self._handler_type())
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()

    def _handler_type(self):
        service = self

        class RequestHandler(BaseHTTPRequestHandler):
            def _send(self, status, body):
                payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
                self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS, GET")
                self.end_headers()
                self.wfile.write(payload)

            def do_OPTIONS(self):
                self._send(204, {})

            def do_GET(self):
                if self.path == "/health":
                    self._send(200, {"ok": True, "service": "local-label-printer"})
                else:
                    self._send(404, {"ok": False, "error": "Ruta no encontrada"})

            def do_POST(self):
                if self.path != "/api/imprimir":
                    self._send(404, {"ok": False, "error": "Ruta no encontrada"})
                    return
                if self.headers.get("Authorization", "") != f"Bearer {service.token}":
                    self._send(401, {"ok": False, "error": "PIN inválido"})
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if length < 1 or length > 16384:
                        raise ValueError("Tamaño de solicitud inválido")
                    data = json.loads(self.rfile.read(length).decode("utf-8"))
                    codigo = str(data.get("codigo", "")).strip()
                    acta = str(data.get("acta", "")).strip()
                    if not codigo or not acta:
                        raise ValueError("Se requieren codigo y acta")
                except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                    self._send(400, {"ok": False, "error": str(exc)})
                    return

                job = {"codigo": codigo, "acta": acta, "done": threading.Event()}
                service.jobs.put(job)
                if not job["done"].wait(60):
                    self._send(504, {"ok": False, "error": "La impresión tardó demasiado"})
                    return
                status, result = job["result"]
                self._send(status, result)

            def log_message(self, _format, *_args):
                return

        return RequestHandler

    @staticmethod
    def local_ip():
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            probe.connect(("192.0.2.1", 80))
            return probe.getsockname()[0]
        except OSError:
            return "127.0.0.1"
        finally:
            probe.close()
