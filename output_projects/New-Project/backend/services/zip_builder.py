import os
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from utils.config import settings
from utils.exceptions import ZipBuilderError


class ZipBuilder:
    """
    根據 PRD 與技術棧產生可下載的 ZIP 專案包。
    目錄結構與依賴檔案皆遵循社群最佳實踐，確保 `python main.py` 或 `npm install && npm run dev`
    可直接零配置運行。
    """

    # 預設模板根目錄，可掛載進容器或本地開發
    TEMPLATE_DIR = Path(__file__).with_name("templates")

    # 各技術棧對應的子資料夾
    STACK_TEMPLATES = {
        "python": TEMPLATE_DIR / "python",
        "react": TEMPLATE_DIR / "react",
        "nodejs": TEMPLATE_DIR / "nodejs",
    }

    def __init__(self, stack: str, prd_md: str):
        if stack not in self.STACK_TEMPLATES:
            raise ZipBuilderError(f"Unsupported stack: {stack}")
        self.stack = stack
        self.prd_md = prd_md

    def build(self, output_dir: Optional[Path] = None) -> Path:
        """
        1. 複製模板到暫存資料夾
        2. 注入 PRD 與客製化檔案
        3. 打包成 ZIP
        4. 回傳 ZIP 絕對路徑
        """
        if output_dir is None:
            output_dir = Path(settings.ZIP_CACHE_DIR)

        output_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "project"
            self._copy_template(project_path)
            self._inject_prd(project_path)
            self._post_hook(project_path)

            zip_name = f"{self.stack}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.zip"
            zip_path = output_dir / zip_name

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for file_path in project_path.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(project_path)
                        zf.write(file_path, arcname)

        return zip_path

    def _copy_template(self, dst: Path) -> None:
        src = self.STACK_TEMPLATES[self.stack]
        if not src.exists():
            raise ZipBuilderError(f"Template not found: {src}")
        shutil.copytree(src, dst)

    def _inject_prd(self, project_path: Path) -> None:
        # 將 PRD 寫入 PRD.md 方便開發者查閱
        prd_file = project_path / "PRD.md"
        prd_file.write_text(self.prd_md, encoding="utf-8")

    def _post_hook(self, project_path: Path) -> None:
        """
        依技術棧進行最後微調，例如：
        - Python: 確保 requirements 包含常用套件
        - React: 若缺少 next.config.js 則補上
        """
        if self.stack == "python":
            req = project_path / "requirements.txt"
            if req.exists():
                content = req.read_text()
                if "fastapi" not in content:
                    content += "\nfastapi>=0.110.0\nuvicorn[standard]>=0.29.0\n"
                    req.write_text(content)
        elif self.stack == "react":
            nxt = project_path / "next.config.js"
            if not nxt.exists():
                nxt.write_text("/** @type {import('next').NextConfig} */\nmodule.exports = {};\n")
        elif self.stack == "nodejs":
            pkg = project_path / "package.json"
            if pkg.exists():
                # 確保有 start script
                import json
                data = json.loads(pkg.read_text())
                scripts = data.setdefault("scripts", {})
                scripts.setdefault("start", "node index.js")
                pkg.write_text(json.dumps(data, indent=2))


def generate_zip(stack: str, prd_md: str) -> Path:
    """
    對外簡易介面，直接回傳 ZIP 路徑。
    """
    builder = ZipBuilder(stack=stack, prd_md=prd_md)
    return builder.build()