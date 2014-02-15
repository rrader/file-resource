import logging
from urllib.parse import parse_qs
from authentication import need_authentication, make_password
from authorization import need_authorization
from resource import User

logger = logging.getLogger(__name__)


def need_superuser(view):
    def wrap_view(self, *args, **kwargs):
        if not (self.user and self.user.superuser):
            logger.warn("NON-ADMIN USER '{}' ACCESSED {}: FORBIDDEN".format(self.user.name, view.__name__))
            self.render_template("message.html", message="Вы не администратор")
            return
        view(self, *args, **kwargs)
    return wrap_view


class AdminMixin(object):
    def do_GET(self):
        super().do_GET()
        if self.path == '/admin':
            return self.admin_view()

    def do_POST(self):
        super().do_POST()
        if self.path == '/user/create':
            return self.create_user_post_view()

    @need_authentication
    @need_authorization
    @need_superuser
    def admin_view(self):
        self.render_template("admin.html", users=User.select())

    def create_user_post_view(self):
        length = int(self.headers['Content-Length'])
        data = self.rfile.read(length)
        post_data = parse_qs(data.decode('utf-8'))

        name = post_data['name'][0]
        password = post_data['password'][0]
        logger.info("attempt to create user '{}'".format(name))
        if User.select().where(User.name == name).exists():
            logger.warn("user '{}' already exists!".format(name))
            self.render_template("message.html", message="Такой пользователь уже есть")
            return
        user = User.create(name=name, password=make_password(name, password))
        user.save()
        logger.info("user '{}' created successfully".format(name))
        self.send_response(302)
        self.send_header('location', '/admin')
        self.end_headers()
