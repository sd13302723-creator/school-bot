import os
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler


class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

    def log_message(self, format, *args):
        return


def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    print(f"Web server started on port {port}")
    server.serve_forever()


server_thread = threading.Thread(
    target=run_web_server,
    daemon=True
)
server_thread.start()

print("Application started")

while True:
    time.sleep(60)
    
