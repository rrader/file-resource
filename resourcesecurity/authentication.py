from http import cookies
from urllib.parse import parse_qs
import uuid
import hashlib
from peewee import DoesNotExist
from resource import User

SALT = 'YJVz4amAuw'


def make_password(user, password):
    secret = "{}{}{}".format(password, user, SALT).encode("utf-8")
    return hashlib.sha1(secret).hexdigest()


def authenticate(username, password):
    try:
        user = User.select().where(User.name == username).get()
    except DoesNotExist:
        return
    if make_password(username, password) == user.password:
        # authenticated OK
        # TODO: logging
        return user


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

    def auth_view(self, error=None):
        if not self.user:
            self.render_template("auth.html", error=error)
            return
        else:
            self.send_response(302)
            self.send_header('location', '/')
            self.end_headers()
            return

    def logout_view(self):
        self.send_response(302)
        self.cookie['session'] = ''
        self.send_header('location', '/')
        self.flush_headers()
        self.wfile.write(self.cookie.output().encode())
        self.wfile.write(b'\n')
        self.end_headers()
