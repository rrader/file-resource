from datetime import datetime
from urllib.parse import parse_qs
from authentication import need_authentication
import random

MAX_DELTA = 60


def need_authorization(view):
    def wrap_view(self, *args, **kwargs):
        if not self.authorized:
            self.send_response(302)
            self.send_header('location', '/re-auth')
            self.end_headers()
            return
        view(self, *args, **kwargs)
    return wrap_view


class AuthorizationMixin(object):
    AUTHORIZATION = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_delta = 0

    def do_GET(self):
        super().do_GET()
        if self.path == '/re-auth':
            return self.re_auth_view()

    def do_POST(self):
        super().do_POST()
        if self.path == '/re-auth':
            return self.re_auth_post_view()

    def authorize(self, sid):
        self.authorized = True
        if sid in self.AUTHORIZATION:
            delta = (datetime.now() - self.AUTHORIZATION[sid]['updated']).seconds
            if delta > MAX_DELTA:
                self.authorized = False
            self.auth_left = MAX_DELTA - delta
        else:
            self.AUTHORIZATION[sid] = dict(updated=datetime.now())

    @need_authentication
    def re_auth_view(self, error=None):
        x = random.randint(0, 10)
        y = random.randint(-10, 10)
        action = random.choice([(lambda a, b: a+b, '+'),
                                (lambda a, b: a-b, '-'),
                                (lambda a, b: a*b, '*'),
                                ])
        question = "({}) {} ({})".format(x, action[1], y)
        self.AUTHORIZATION[self.sid]['answer'] = str(action[0](x, y))
        self.render_template("re-auth.html", reauth=True,
                             question=question)

    @need_authentication
    def re_auth_post_view(self, error=None):
        length = int(self.headers['Content-Length'])
        data = self.rfile.read(length)
        post_data = parse_qs(data.decode('utf-8'))

        if post_data['secret'][0] == self.AUTHORIZATION[self.sid]['answer']:
            self.AUTHORIZATION[self.sid].update(dict(updated=datetime.now()))
            self.send_response(302)
            self.send_header('location', '/')
            self.end_headers()
        else:
            self.logout_view()
