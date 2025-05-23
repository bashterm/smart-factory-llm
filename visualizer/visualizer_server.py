from filelock    import Timeout, FileLock
from http.server import BaseHTTPRequestHandler, HTTPServer
from json        import loads

import sys


# Server Configuration
hostName    = "localhost" 
serverPort  = 8080
config_path = sys.argv[1]

# File Configuration
with open(config_path) as file:
    config = loads(file.read())


# Lock to prevent the partition system from writing the file vis_agents when the visualizer server
# is reading it.
vis_state_lock = FileLock(config['vis_state_lock'], timeout=config['vis_lock_timeout'])  


class MyServer(BaseHTTPRequestHandler):

  # GET requests
  def do_GET(self):
    print(f"Received get request for file: {self.path}")
    # By default, serve the visualizer
    if self.path == "" or self.path == "/":
      self.serve_vis_html()

    # Ignore requests for '/favicon.ico'
    elif self.path == "/favicon.ico":
      pass

    # Serve vis agents
    elif self.path == config['vis_state']:
      self.serve_vis_state()

    # Serve a targeted JSON file. This file will be in the folder tmp
    elif "tmp" in self.path:
      self.serve_json()

    else:
      assert False, f"Path '{self.path}' not recognized "
        

  # Serve the visualizer HTML
  def serve_vis_html(self): 
    self.send_response(200)
    self.send_header("Content-type", "text/html")
    self.end_headers()
    with open(config['vis_html'], "rb") as vis_f:
      self.wfile.write(vis_f.read())


  # Serve a targeted JSON file from the folder tmp
  def serve_json(self):
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()

    print(self.path[1:])
    with open(self.path[1:], "rb") as f:
      self.wfile.write(f.read())


  # Serve vis_agents, a JSON file containing information about the partition system's agents
  def serve_vis_state(self):
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()

    with visDB_lock:
      with open(config['vis_state'], "rb") as f:
        self.wfile.write(f.read())


if __name__ == "__main__":        
  webServer = HTTPServer((hostName, serverPort), MyServer)
  print("Server started http://%s:%s" % (hostName, serverPort))

  try:
    webServer.serve_forever()
  except KeyboardInterrupt:
    pass

  webServer.server_close()
  print("Server stopped.")