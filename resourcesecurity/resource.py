import os
from peewee import Model, SqliteDatabase, CharField, TextField, DoesNotExist, BooleanField

DB = SqliteDatabase(os.path.join(os.path.curdir, 'data.sqlite'))


class User(Model):
    name = CharField(primary_key=True)
    password = CharField()
    superuser = BooleanField(default=False)

    class Meta:
        database = DB


class FileResource(Model):
    name = CharField(primary_key=True)
    data = TextField(null=True)
    owner = CharField()

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
