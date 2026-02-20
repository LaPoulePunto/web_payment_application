import os
from peewee import *

DATABASE = os.environ.get("DATABASE", "inf349.db")
db = SqliteDatabase(DATABASE)


class BaseModel(Model):
    class Meta:
        database = db

class Product(BaseModel):
    id = IntegerField(primary_key=True)
    name = CharField()
    description = TextField()
    price = FloatField()
    weight = IntegerField()
    in_stock = BooleanField(default=True)
    image = CharField()

    class Meta:
        table_name = "products"

def initialize_db():
    db.connect(reuse_if_open=True)
    db.create_tables(
        [Product],
        safe=True,
    )
