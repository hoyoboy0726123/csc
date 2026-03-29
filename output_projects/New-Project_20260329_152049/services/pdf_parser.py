import fitz  # PyMuPDF
from pathlib import Path
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def parse(file_path: str) -> str:
    """
    將 PDF 檔案解析為純文字。

    參數
    ----
    file_path : str
        本地 PDF 檔案路徑。

    回傳
    ----
    str
        提取出的全文文字；若檔案不存在或解析失敗，回傳空字串。
    """
    path = Path(file_path)

    if not path.exists():
        logger.error("PDF 檔案不存在: %s", file_path)
        return ""

    try:
        doc = fitz.open(path)
        text = ""
        for page in doc:
            text += page.get_text("text")
        doc.close()
        logger.info("PDF 解析完成，共 %s 頁", len(doc))
        return text.strip()
    except Exception as e:
        logger.exception("PDF 解析錯誤: %s", e)
        return ""