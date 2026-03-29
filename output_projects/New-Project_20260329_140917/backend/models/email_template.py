from sqlalchemy import Column, Integer, String, Text
from backend.models import Base


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)
    template_name = Column(String(120), unique=True, nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    body_html = Column(Text, nullable=False)
    body_text = Column(Text, nullable=False)