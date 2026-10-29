
import os
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# --- Мини-веб-сервер для Render ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

# Запускаем веб-сервер в фоновом потоке
server_thread = threading.Thread(target=run_web_server, daemon=True)
server_thread.start()

# --- Здесь основной код бота ---
