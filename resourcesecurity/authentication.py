from http import cookies
import logging
from urllib.parse import parse_qs
import uuid
from functools import wraps
import hashlib
from peewee import DoesNotExist
from resource import User

logger = logging.getLogger(__name__)

SALT = 'YJVz4amAuw'


def make_password(user, password):
    secret = "{}{}{}".format(password, user, SALT).encode("utf-8")
    return hashlib.sha1(secret).hexdigest()


def authenticate(username, password):
    try:
        user = User.select().where(User.name == username).get()
    except DoesNotExist:
        logger.warn("user '{}' not found".format(username))
        return
    if make_password(username, password) == user.password:
        logger.info("user '{}' authenticated OK".format(username))
        return user
    logger.warn("wrong password for user '{}'".format(username))


def need_authentication(view):
    @wraps(view)
    def wrap_view(self, *args, **kwargs):
        if not self.user:
            logger.warn("not authenticated in view '{}'".format(view.__name__))
            self.send_response(302)
            self.send_header('location', '/auth')
            self.end_headers()
            return
        view(self, *args, **kwargs)
    return wrap_view


class AuthenticationMixin(object):
    SESSIONS = {}

    def do_GET(self):
        super().do_GET()
        self.authenticate()
        if self.path == '/auth':
            return self.auth_view()
        if self.path == '/logout':
            return self.logout_view()

    def do_POST(self):
        super().do_POST()
        self.authenticate()
        if self.path == '/auth':
            return self.auth_post_view()

    @property
    def username(self):
        if self.user:
            return self.user.name
        else:
            return '<nobody>'

    def auth_post_view(self):
        length = int(self.headers['Content-Length'])
        data = self.rfile.read(length)
        post_data = parse_qs(data.decode('utf-8'))

        user = authenticate(post_data['user'][0],
                            post_data['password'][0])
        sid = None
        if user:
            self.user = user
            sid = uuid.uuid1().hex
            self.SESSIONS[sid] = user
            self.authorize(sid)

        if sid:
            self.send_response(302)
            self.cookie['session'] = sid
            self.send_header('location', '/')
            self.flush_headers()
            self.wfile.write(self.cookie.output().encode())
            self.wfile.write(b'\n')
            self.end_headers()
            return
        else:
            return self.auth_view(error="Ошибка аутентификации")

    def authenticate(self):
        self.cookie = cookies.SimpleCookie()
        self.user = None
        if 'cookie' in self.headers:
            self.cookie = cookies.SimpleCookie(self.headers["cookie"])
        if 'session' in self.cookie:
            if self.cookie['session'].value in self.SESSIONS:
                self.user = self.SESSIONS[self.cookie['session'].value]
        if self.cookie and 'session' in self.cookie:
            self.sid = self.cookie['session'].value
            self.authorize(self.sid)

    def auth_view(self, error=None):
        if not self.user:
            self.render_template("auth.html", error=error)
            return
        else:
            self.send_response(302)
            self.send_header('location', '/')
            self.end_headers()
            return

    @need_authentication
    def logout_view(self):
        self.send_response(302)
        self.cookie['session'] = ''
        self.send_header('location', '/')
        self.flush_headers()
        self.wfile.write(self.cookie.output().encode())
        self.wfile.write(b'\n')
        self.end_headers()
        logger.info("user '{}' logged out".format(self.user.name))
