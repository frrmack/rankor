# Import threading to have control on the server process
import threading

# Import of the configured Flask app
from rankor import app as rankor_app

# Import Werkzeug's api to create, run, and stop a server
from werkzeug.serving import make_server


class RankorServerThread(threading.Thread):
    """A Werkzeug server thread that allows initialization and shutdown
       of a simple development server at will. This is quite helpful in
       running functionality tests on the api server. Start and stop the
       server thread in the following way:
       
       server = RankorServerThread()
       server.start()
       # <work with the server>
       server.stop()
    """

    def __init__(self, ip='127.0.0.1', port=5000):
        """Create a Werkzeug server with the rankor app"""
        threading.Thread.__init__(self)
        self.name = "RankorServerThread"
        self.app = rankor_app
        self.server = make_server(ip, port, self.app)
        self.ctx = self.app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()

    def stop(self, timeout=None):
        self.server.shutdown()
        self.join(timeout=timeout)

