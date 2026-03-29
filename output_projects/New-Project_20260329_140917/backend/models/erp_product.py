from sqlalchemy import Column, String, Numeric
from backend.models import Base


class ErpProduct(Base):
    __tablename__ = "erp_products"

    product_id = Column(String(50), primary_key=True, nullable=False)
    name = Column(String(200), nullable=False)
    category = Column(String(100))
    price = Column(Numeric(12, 2))