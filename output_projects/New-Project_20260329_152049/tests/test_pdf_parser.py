import os
import tempfile
import unittest
from pathlib import Path
from services.pdf_parser import parse

class TestPdfParser(unittest.TestCase):
    """Unit tests for PDF parsing functionality."""

    def setUp(self) -> None:
        """Create a temporary directory for test PDFs."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        """Clean up temporary directory."""
        for file in Path(self.test_dir).glob("*"):
            file.unlink()
        os.rmdir(self.test_dir)

    def _write_dummy_pdf(self, name: str, content: bytes = b"%PDF-1.4 dummy") -> Path:
        """Helper to write a minimal PDF file for testing."""
        path = Path(self.test_dir) / name
        path.write_bytes(content)
        return path

    def test_parse_success(self):
        """Test successful parsing returns expected dict."""
        pdf_path = self._write_dummy_pdf("valid.pdf")
        result = parse(pdf_path)
        self.assertIsInstance(result, str)

    def test_parse_nonexistent_file(self):
        """Test parsing a non-existent file raises FileNotFoundError."""
        fake = Path(self.test_dir) / "missing.pdf"
        with self.assertRaises(FileNotFoundError):
            parse(fake)

    def test_parse_empty_file(self):
        """Test parsing an empty file returns empty text."""
        empty = self._write_dummy_pdf("empty.pdf", b"")
        result = parse(empty)
        self.assertEqual(result, "")

    def test_parse_corrupted_pdf(self):
        """Test parsing corrupted PDF returns empty or raises handled exception."""
        bad = self._write_dummy_pdf("bad.pdf", b"not a pdf")
        try:
            result = parse(bad)
            self.assertEqual(result, "")
        except ValueError:
            pass

if __name__ == "__main__":
    unittest.main()