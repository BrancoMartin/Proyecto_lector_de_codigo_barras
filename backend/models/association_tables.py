
from sqlalchemy import Table, Column, Integer, ForeignKey
from database import Base

product_attribute = Table(
    "product_attribute",
    Base.metadata,
    Column("product_id", Integer, ForeignKey("products.id"), primary_key=True),
    Column("attribute_id", Integer, ForeignKey("attributes.id"), primary_key=True)
)

product_category = Table(
    "product_category",
    Base.metadata,
    Column("product_id", Integer, ForeignKey("products.id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id"), primary_key=True)
)
