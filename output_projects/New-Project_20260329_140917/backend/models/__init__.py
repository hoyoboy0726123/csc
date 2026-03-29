from sqlalchemy.orm import declarative_base

from .case import Case
from .user import User
from .attachment import Attachment
from .erp_product import ErpProduct
from .email_template import EmailTemplate

Base = declarative_base()

__all__ = ["Base", "User", "Case", "Attachment", "ErpProduct", "EmailTemplate"]