from urllib.parse import parse_qs
from peewee import DoesNotExist
from resource import FileResource


class ResourceProviderMixin(object):
    def do_GET(self):
        super().do_GET()
        if self.path == '/file/create':
            return self.file_edit_view()
        if self.path.startswith('/file/update?'):
            args = self.path.split('?', 1)[1]
            name = parse_qs(args)['name']
            return self.file_edit_view(name=name)
        if self.path == '/file/remove':
            return self.logout_view()
        if self.path == '/file':
            return self.file_list_view()

    def do_POST(self):
        super().do_POST()
        if self.path == '/file/update':
            return self.file_edit_post_view()
        if self.path == '/file/create':
            return self.file_create_post_view()

    # ===================================================
    # Views
    # ===================================================
    def file_list_view(self):
        self.render_template("list.html", list=FileResource.select())

    def file_edit_view(self, name=None):
        if not self.user:
            self.send_response(302)
            self.send_header('location', '/')
            self.end_headers()
            return
        method = "create"
        data = {}
        if name:
            method = "update"
            try:
                file = FileResource.select().where(FileResource.name == name).get()
            except DoesNotExist:
                self.render_template("message.html", message="Файл не найден", code=404)
                return
            data['name'] = file.name
            data['data'] = file.data
        self.render_template("file.html", method=method, data=data)

    def file_create_post_view(self):
        if not self.user:
            self.send_response(302)
            self.send_header('location', '/')
            self.end_headers()
            return
        length = int(self.headers['Content-Length'])
        data = self.rfile.read(length)
        post_data = parse_qs(data.decode('utf-8'))

        if FileResource.select().where(FileResource.name == post_data['name'][0]).exists():
            self.render_template("message.html", message="Файл с таким именем уже существует")
            return
        file = FileResource.create(name=post_data['name'][0], owner=self.user)
        file.data = post_data['text'][0]
        file.save()
        self.send_response(302)
        self.send_header('location', '/file/update?name={}'.format(file.name))
        self.end_headers()

    def file_edit_post_view(self):
        length = int(self.headers['Content-Length'])
        data = self.rfile.read(length)
        post_data = parse_qs(data.decode('utf-8'))

        name = post_data['name'][0]
        query = FileResource.select().where(FileResource.name == name)
        if not query.exists():
            self.render_template("message.html", code=404, message="Файла с таким именем не существует")
            return

        file = query.get()
        file.data = post_data['text'][0]
        file.save()
        self.send_response(302)
        self.send_header('location', '/file/update?name={}'.format(file.name))
        self.end_headers()
