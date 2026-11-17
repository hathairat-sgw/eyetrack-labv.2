import os
import threading
import sys
import uvicorn

server = uvicorn.Server(uvicorn.Config('backend.main:app', host='127.0.0.1', port=int(os.environ.get("EYETRACK_BACKEND_PORT", "8000"))))
def watch_launcher():
    sys.stdin.readline()
    server.should_exit = True
threading.Thread(target=watch_launcher, daemon=True).start()
server.run()
