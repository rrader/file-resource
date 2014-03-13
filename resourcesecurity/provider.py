import logging
from urllib.parse import parse_qs
from authentication import need_authentication
from authorization import need_authorization
from functools import wraps
from peewee import DoesNotExist
from resource import FileResource

logger = logging.getLogger(__name__)


def need_file_exists(view):
    @wraps(view)
    def wrap_view(self, name, *args, **kwargs):
        try:
            file = FileResource.select().where(FileResource.name == name).get()
        except DoesNotExist:
            logger.warn("requested file '{}' not found for view {}".format(name, view.__name__))
            self.render_template("message.html", message="Файл не найден", code=404)
            return
        view(self, file, *args, **kwargs)
    return wrap_view


def need_write_permission(view):
    @wraps(view)
    def wrap_view(self, file, *args, **kwargs):
        if file.can_write(self.user):
            view(self, file, *args, **kwargs)
        else:
            logger.warn("user '{}' have no write perm for '{}' in view {}".format(self.user, file.name, view.__name__))
            self.render_template("message.html", message="Прав недостаточно", code=404)
    return wrap_view


def need_read_permission(view):
    @wraps(view)
    def wrap_view(self, file, *args, **kwargs):
        if file.can_read(self.user):
            view(self, file, *args, **kwargs)
        else:
            logger.warn("user '{}' have no read perm for '{}' in view {}".format(self.user, file.name, view.__name__))
            self.render_template("message.html", message="Прав недостаточно", code=404)
    return wrap_view


class ResourceProviderMixin(object):
    def do_GET(self):
        super().do_GET()
        if self.path == '/file/create':
            return self.file_create_view()
        if self.path.startswith('/file/update?'):
            args = self.path.split('?', 1)[1]
            name = parse_qs(args)['name']
            return self.file_edit_view(name=name)
        if self.path.startswith('/file/read?'):
            args = self.path.split('?', 1)[1]
            name = parse_qs(args)['name']
            return self.file_read_view(name=name)
        if self.path.startswith('/file/delete?'):
            args = self.path.split('?', 1)[1]
            name = parse_qs(args)['name']
            return self.file_remove_view(name)
        if self.path == '/file':
            return self.file_list_view()

    def do_POST(self):
        super().do_POST()
        if self.path == '/file/update':
            return self.file_edit_post_view()
        if self.path == '/file/create':
            return self.file_create_post_view()
        if self.path == '/file/upload':
            return self.file_upload_post_view()

    # ===================================================
    # Views
    # ===================================================
    @need_authentication
    @need_authorization
    def file_list_view(self):
        self.render_template("list.html", list=FileResource.select())

    @need_authentication
    @need_authorization
    def file_create_view(self, name=None):
        method = "create"
        data = {'ru': True, 'wu': True,
                'ro': False, 'wo': False}
        self.render_template("file.html", method=method, data=data)

    @need_authentication
    @need_authorization
    @need_file_exists
    @need_write_permission
    def file_edit_view(self, file):
        method = "update"
        data = {'name': file.name, 'data': file.data,
                'ru': file.ru, 'wu': file.wu,
                'ro': file.ro, 'wo': file.wo}
        self.render_template("file.html", method=method, data=data)

    @need_authentication
    @need_authorization
    @need_file_exists
    @need_read_permission
    def file_read_view(self, file):
        data = {}
        data['name'] = file.name
        data['data'] = file.data
        self.render_template("file.html", method="read", data=data)

    @need_authentication
    @need_authorization
    def file_create_post_view(self):
        length = int(self.headers['Content-Length'])
        data = self.rfile.read(length)
        post_data = parse_qs(data.decode('utf-8'))

        if FileResource.select().where(FileResource.name == post_data['name'][0]).exists():
            logger.warn("file '{}' already exists found".format(post_data['name'][0]))
            self.render_template("message.html", message="Файл с таким именем уже существует")
            return
        file = FileResource.create(name=post_data['name'][0], owner=self.user)
        file.data = post_data['text'][0]

        file.ru = 'ru' in post_data
        file.wu = 'wu' in post_data
        file.ro = 'ro' in post_data
        file.wo = 'wo' in post_data

        file.save()
        self.send_response(302)
        self.send_header('location', '/file/update?name={}'.format(file.name))
        self.end_headers()
        logger.info("file {} <{}> created by {}".format(file.name, file.mode(), file.owner))

    @need_authentication
    @need_authorization
    def file_edit_post_view(self):
        length = int(self.headers['Content-Length'])
        data = self.rfile.read(length)
        post_data = parse_qs(data.decode('utf-8'))

        name = post_data['name'][0]
        query = FileResource.select().where(FileResource.name == name)
        if not query.exists():
            logger.warn("file '{}' not found".format(name))
            self.render_template("message.html", code=404, message="Файла с таким именем не существует")
            return

        file = query.get()
        if not file.can_write(self.user):
            logger.warn("user {} have no permission to write to '{}'<{}>".format(self.user.name, file.name, file.mode()))
            self.render_template("message.html", code=404, message="Недостаточно прав")
            return

        file.data = post_data['text'][0]
        file.ru = 'ru' in post_data
        file.wu = 'wu' in post_data
        file.ro = 'ro' in post_data
        file.wo = 'wo' in post_data
        file.save()
        self.send_response(302)
        self.send_header('location', '/file/update?name={}'.format(file.name))
        self.end_headers()
        logger.info("file '{}' <{}> updated by '{}'".format(file.name, file.mode(), file.owner))

    @need_authentication
    @need_authorization
    @need_file_exists
    @need_write_permission
    def file_remove_view(self, file):
        logger.info("file '{}' <{}> removing by '{}'".format(file.name, file.mode(), file.owner))
        file.delete_instance()
        self.send_response(302)
        self.send_header('location', '/'.format(file.name))
        self.end_headers()

    @need_authentication
    @need_authorization
    def file_upload_post_view(self):
        length = int(self.headers['Content-Length'])
        data = self.rfile.read(length)
        print(data)
