import io
from pathlib import Path
from typing import Optional

import pymupdf  # PyMuPDF
from loguru import logger

from utils.azure_blob import download_file
from utils.logger import logger as app_logger


class PdfService:
    """
    將 PDF 轉為 Markdown 文字。
    1. 優先使用 PyMuPDF 抽取文字。
    2. 若文字為空或長度過短，自動 fallback 到 OCR（需額外安裝 Tesseract）。
    3. 統一輸出 UTF-8 編碼的 Markdown 字串。
    """

    def __init__(self, ocr_threshold: int = 50) -> None:
        self.ocr_threshold = ocr_threshold  # 字元數低於此值則啟用 OCR

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    async def parse(self, blob_url: str) -> str:
        """
        傳入 Azure Blob 完整 URL，回傳 Markdown 文字。
        失敗時拋出 RuntimeError，並附帶簡短原因。
        """
        try:
            pdf_bytes = await download_file(blob_url)
        except Exception as exc:
            logger.error("下載 Blob 失敗: {}", exc)
            raise RuntimeError("無法取得 PDF 檔案") from exc

        try:
            text = self._extract_text(pdf_bytes)
            if len(text.strip()) < self.ocr_threshold:
                logger.info("文字過短，啟用 OCR fallback")
                text = await self._ocr_pdf(pdf_bytes)
        except Exception as exc:
            logger.error("PDF 解析失敗: {}", exc)
            raise RuntimeError("PDF 解析失敗，請確認檔案完整或聯絡管理員") from exc

        # 簡易轉 Markdown：保留段落空行
        markdown = "\n\n".join(line.strip() for line in text.splitlines() if line.strip())
        logger.info("PDF 轉 Markdown 完成，共 {} 字元", len(markdown))
        return markdown

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    def _extract_text(self, pdf_bytes: bytes) -> str:
        """使用 PyMuPDF 抽取文字。"""
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        pages = [page.get_text() for page in doc]
        doc.close()
        return "\n".join(pages)

    async def _ocr_pdf(self, pdf_bytes: bytes) -> str:
        """
        OCR fallback，需系統安裝 tesseract + tesserocr。
        若未安裝則直接回傳空字串，讓前端提示人工補填。
        """
        try:
            from tesserocr import PyTessBaseAPI  # type: ignore
        except ImportError:
            logger.warning("tesserocr 未安裝，OCR 無法啟用")
            return ""

        import fitz  # PyMuPDF 用於轉圖片
        from PIL import Image

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        ocr_texts: list[str] = []

        with PyTessBaseAPI(lang="eng+chi_tra") as api:
            for page in doc:
                pix = page.get_pixmap(dpi=300)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                api.SetImage(img)
                ocr_texts.append(api.GetUTF8Text())

        doc.close()
        return "\n".join(ocr_texts)


# ------------------------------------------------------------------------- #
# 全域實例，供 DI 注入
# ------------------------------------------------------------------------- #
pdf_service = PdfService()