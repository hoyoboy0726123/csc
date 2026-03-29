import unittest
from pathlib import Path
from services.email_parser import parse_eml
from tempfile import NamedTemporaryFile
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class TestEmailParser(unittest.TestCase):

    def setUp(self):
        self.sample_eml_content = self._create_sample_eml()

    def _create_sample_eml(self) -> str:
        msg = MIMEMultipart()
        msg["Subject"] = "測試主旨"
        msg["From"] = "customer@example.com"
        msg["To"] = "support@example.com"
        body = MIMEText("這是測試內容", "plain", "utf-8")
        msg.attach(body)
        return msg.as_string()

    def test_parse_eml(self):
        result = parse_eml(self.sample_eml_content)
        self.assertEqual(result["subject"], "測試主旨")
        self.assertEqual(result["from"], "customer@example.com")
        self.assertEqual(result["to"], "support@example.com")
        self.assertIn("這是測試內容", result["body"])

if __name__ == "__main__":
    unittest.main()