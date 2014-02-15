from admin import AdminMixin
from authorization import AuthorizationMixin
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
import sys
from jinja2 import Environment, FileSystemLoader
from authentication import AuthenticationMixin
from provider import ResourceProviderMixin

logger = logging.getLogger(__name__)


class HTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pass

    def do_POST(self):
        pass


class ResourceHandler(AdminMixin, ResourceProviderMixin,
                      AuthorizationMixin, AuthenticationMixin,
                      HTTPRequestHandler):
    @property
    def context(self):
        return {'username': self.username,
                'user': self.user,
                'path': self.path,
                'auth_left': self.auth_left,
               }

    def render_template(self, name, code=200, *args, **kwargs):
        kwargs = kwargs.copy()
        kwargs.update(self.context)
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template(name).render(**kwargs)
        encoded = template.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    # ===================================================
    # Routing
    # ===================================================
    def do_GET(self):
        super().do_GET()
        if self.path == '/':
            self.send_response(302)
            self.send_header('location', '/file')
            self.end_headers()
            return
        if self.path.startswith('/static'):
            return self.send_file(self.path[1:])

    def do_POST(self):
        super().do_POST()

    # ===================================================
    # Static files
    # ===================================================
    def send_file(self, param):
        logger.debug("static file {} requested".format(param))
        file = open(os.path.join(os.path.curdir, param), 'rb').read()
        self.wfile.write(file)


if __name__ == "__main__":
    logging.basicConfig(filename='journal.log', level=logging.INFO,
                        format='%(asctime)s %(name)s:%(levelname)s: %(message)s')
    httpd = HTTPServer(("0.0.0.0", 8000), ResourceHandler)
    logger.info("Starting server")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, exiting.")
        httpd.server_close()
        sys.exit(0)
