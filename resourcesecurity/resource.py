import os
from peewee import Model, SqliteDatabase, CharField, TextField, DoesNotExist, BooleanField

DB = SqliteDatabase(os.path.join(os.path.curdir, 'data.sqlite'))


class User(Model):
    name = CharField(primary_key=True)
    password = CharField()
    superuser = BooleanField(default=False)
    disabled = BooleanField(default=False)

    class Meta:
        database = DB


class FileResource(Model):
    name = CharField(primary_key=True)
    data = TextField(null=True)
    owner = CharField()
    ru = BooleanField(default=True)
    wu = BooleanField(default=True)
    ro = BooleanField(default=False)
    wo = BooleanField(default=False)

    def mode(self):
        r = lambda z: 'r' if z else '-'
        w = lambda z: 'w' if z else '-'
        return "{}{}{}{}".format(r(self.ru), w(self.wu),
                                 r(self.ro), w(self.wo))

    def can_read(self, user):
        if user.superuser:
            return True
        if user.name == self.owner:
            return self.ru
        return self.ro

    def can_write(self, user):
        if user.superuser:
            return True
        if user.name == self.owner:
            return self.wu
        return self.wo

    class Meta:
        database = DB

if __name__ == "__main__":
    from authentication import make_password
    if not FileResource.table_exists():
        FileResource.create_table()
    if not User.table_exists():
        User.create_table()

    try:
        User.select().where(User.name == 'admin').get()
    except DoesNotExist:
        admin = User.create(name='admin', superuser=True,
                            password=make_password('admin', 'admin'))
        admin.save()
