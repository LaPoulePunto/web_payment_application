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
    type = CharField()
    description = TextField()
    image = CharField()
    height = IntegerField()
    weight = IntegerField()
    price = FloatField()
    in_stock = BooleanField(default=True)

    class Meta:
        table_name = "products"

class Order(BaseModel):
    email = CharField(null=True)
    product = ForeignKeyField(Product, backref="orders")
    quantity = IntegerField()
    paid = BooleanField(default=False)

    class Meta:
        table_name = "orders"

class ShippingInformation(BaseModel):
    order = ForeignKeyField(Order, backref="shipping_information", unique=True)
    country = CharField()
    address = CharField()
    postal_code = CharField()
    city = CharField()
    province = CharField()

    class Meta:
        table_name = "shipping_information"


class CreditCard(BaseModel):
    order = ForeignKeyField(Order, backref="credit_card", unique=True)
    name = CharField()
    first_digits = CharField()
    last_digits = CharField()
    expiration_year = IntegerField()
    expiration_month = IntegerField()

    class Meta:
        table_name = "credit_cards"


class Transaction(BaseModel):
    order = ForeignKeyField(Order, backref="transaction", unique=True)
    transaction_id = CharField()
    success = BooleanField()
    amount_charged = IntegerField()

    class Meta:
        table_name = "transactions"


def initialize_db(db_path: str = "app.db") -> None:
    db.init(db_path)
    if db.is_closed():
        db.connect()
    db.create_tables(
        [Product, Order, ShippingInformation, CreditCard, Transaction],
        safe=True,
    )
