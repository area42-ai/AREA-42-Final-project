import os
import sys
import http.server
import socketserver

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def main():
    port = PORT
    server = None
    while port < PORT + 10:
        try:
            # Allow address reuse to prevent "address already in use" errors on quick restarts
            socketserver.TCPServer.allow_reuse_address = True
            server = socketserver.TCPServer(("", port), Handler)
            break
        except OSError:
            print(f"Port {port} is busy, trying next...")
            port += 1
            
    if not server:
        print("Error: Could not bind to any port in range 8080-8090.")
        sys.exit(1)
        
    print(f"\n=======================================================")
    print(f" WATCH OUT - SAFETY DASHBOARD WEB SERVER RUNNING")
    print(f"=======================================================")
    print(f" Access the dashboard in your browser at:")
    print(f" --> http://localhost:{port}/index.html")
    print(f"=======================================================")
    print(f" Press Ctrl+C to stop the server\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard server...")
        server.server_close()

if __name__ == "__main__":
    main()
