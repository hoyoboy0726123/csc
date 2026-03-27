import os
import json
import uuid
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.services.prompt_chains import PromptChains
from backend.services.model_router import ModelRouter
from backend.database.connection import get_db
from backend.models.prd import PRDHistory
from backend.utils.exceptions import LLMError, ModelRouterError
from backend.utils.config import settings

logger = logging.getLogger(__name__)


class LLMOrchestrator:
    """
    統一協調 PromptChains 與 ModelRouter，對外提供高階介面：
    1. 語音/文字 → PRD
    2. PRD → 程式碼
    3. 錯誤訊息 → 修補建議
    4. 自然語言增量需求 → 增量程式碼
    """

    def __init__(self):
        self.chains = PromptChains()
        self.router = ModelRouter()

    # ------------------
    # 1. PRD 生成
    # ------------------
    async def create_prd_from_audio(
        self,
        audio_text: str,
        user_id: int,
        db: Session,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        將 STT 結果轉成 PRD，並寫入資料庫
        """
        try:
            # 使用 ModelRouter 選擇模型
            model = self.router.select_model(task="prd")
            logger.info(f"[create_prd_from_audio] 選用模型: {model}")

            # 組裝 prompt
            prompt = self.chains.prd_chain(audio_text)
            logger.debug(f"[create_prd_from_audio] prompt 前 200 字: {prompt[:200]}")

            # 呼叫 LLM
            prd_md = await self.router.generate(
                model=model,
                prompt=prompt,
                max_tokens=2000,
                temperature=0.7,
            )
            logger.info("[create_prd_from_audio] LLM 回傳成功")

            # 若無 title，自動萃取
            if not title:
                lines = prd_md.strip().splitlines()
                for line in lines:
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break
                if not title:
                    title = "Untitled PRD"

            # 寫入資料庫
            record = PRDHistory(
                user_id=user_id,
                title=title,
                prd_md=prd_md,
                frozen=False,
            )
            db.add(record)
            db.commit()
            db.refresh(record)

            return {
                "task_id": str(record.id),
                "title": title,
                "prd_md": prd_md,
                "editable": True,
            }

        except ModelRouterError as e:
            logger.error(f"[create_prd_from_audio] ModelRouterError: {e}")
            raise HTTPException(status_code=500, detail=f"模型路由錯誤: {e}")
        except Exception as e:
            logger.exception("[create_prd_from_audio] 未預期錯誤")
            raise HTTPException(status_code=500, detail=f"內部錯誤: {e}")

    # ------------------
    # 2. PRD 對話修正
    # ------------------
    async def revise_prd(
        self,
        prd_id: int,
        instruction: str,
        db: Session,
    ) -> Dict[str, Any]:
        """
        根據自然語言指令，更新 PRD
        """
        record = (
            db.query(PRDHistory)
            .filter(PRDHistory.id == prd_id, PRDHistory.frozen.is_(False))
            .first()
        )
        if not record:
            raise HTTPException(status_code=404, detail="PRD 不存在或已凍結")

        try:
            model = self.router.select_model(task="prd")
            prompt = self.chains.prd_revise_chain(
                original_prd=record.prd_md,
                instruction=instruction,
            )
            new_prd_md = await self.router.generate(
                model=model,
                prompt=prompt,
                max_tokens=2000,
                temperature=0.6,
            )

            # 更新資料庫
            record.prd_md = new_prd_md
            record.updated_at = datetime.utcnow()
            db.commit()

            return {
                "task_id": str(record.id),
                "prd_md": new_prd_md,
                "editable": True,
            }

        except ModelRouterError as e:
            logger.error(f"[revise_prd] ModelRouterError: {e}")
            raise HTTPException(status_code=500, detail=f"模型路由錯誤: {e}")
        except Exception as e:
            logger.exception("[revise_prd] 未預期錯誤")
            raise HTTPException(status_code=500, detail=f"內部錯誤: {e}")

    # ------------------
    # 3. PRD → 程式碼
    # ------------------
    async def generate_code(
        self,
        prd_id: int,
        stack: Optional[str] = None,
        db: Session = None,
    ) -> Dict[str, Any]:
        """
        根據 PRD 產生完整專案 ZIP
        """
        record = (
            db.query(PRDHistory)
            .filter(PRDHistory.id == prd_id, PRDHistory.frozen.is_(True))
            .first()
        )
        if not record:
            raise HTTPException(
                status_code=400, detail="PRD 必須先凍結才能生成代碼"
            )

        # 若未指定 stack，自動偵測
        if not stack:
            stack = self._detect_stack(record.prd_md)

        try:
            model = self.router.select_model(task="code")
            prompt = self.chains.code_chain(
                prd_md=record.prd_md,
                stack=stack,
            )
            code_json = await self.router.generate(
                model=model,
                prompt=prompt,
                max_tokens=3000,
                temperature=0.5,
            )

            # 解析 JSON
            try:
                code_struct = json.loads(code_json)
            except json.JSONDecodeError:
                logger.warning("[generate_code] LLM 回傳非 JSON，嘗試修復")
                code_struct = await self._repair_json(code_json)

            # 寫入暫存 ZIP
            zip_path = await self._write_zip(
                prd_id=prd_id,
                stack=stack,
                code_struct=code_struct,
            )

            # 寫入 code_version
            from backend.models.code_version import CodeVersion

            cv = CodeVersion(
                prd_id=prd_id,
                stack=stack,
                zip_path=zip_path,
                version=1,
            )
            db.add(cv)
            db.commit()
            db.refresh(cv)

            return {
                "code_version_id": cv.id,
                "zip_path": zip_path,
                "stack": stack,
            }

        except ModelRouterError as e:
            logger.error(f"[generate_code] ModelRouterError: {e}")
            raise HTTPException(status_code=500, detail=f"模型路由錯誤: {e}")
        except Exception as e:
            logger.exception("[generate_code] 未預期錯誤")
            raise HTTPException(status_code=500, detail=f"內部錯誤: {e}")

    # ------------------
    # 4. 錯誤修復
    # ------------------
    async def fix_code(
        self,
        code_version_id: int,
        error_log: str,
        db: Session,
    ) -> Dict[str, Any]:
        """
        根據 terminal 錯誤訊息，回傳 patch
        """
        from backend.models.code_version import CodeVersion

        cv = db.query(CodeVersion).filter(CodeVersion.id == code_version_id).first()
        if not cv:
            raise HTTPException(status_code=404, detail="CodeVersion 不存在")

        # 讀取 ZIP 內容
        code_struct = await self._read_zip(cv.zip_path)

        try:
            model = self.router.select_model(task="fix")
            prompt = self.chains.fix_chain(
                stack=cv.stack,
                code_struct=code_struct,
                error_log=error_log,
            )
            fixed_json = await self.router.generate(
                model=model,
                prompt=prompt,
                max_tokens=2500,
                temperature=0.4,
            )

            fixed_struct = json.loads(fixed_json)

            # 寫入新版 ZIP
            new_zip_path = await self._write_zip(
                prd_id=cv.prd_id,
                stack=cv.stack,
                code_struct=fixed_struct,
                version=cv.version + 1,
            )

            # 新增版本
            new_cv = CodeVersion(
                prd_id=cv.prd_id,
                stack=cv.stack,
                zip_path=new_zip_path,
                version=cv.version + 1,
            )
            db.add(new_cv)
            db.commit()
            db.refresh(new_cv)

            return {
                "code_version_id": new_cv.id,
                "zip_path": new_zip_path,
                "stack": new_cv.stack,
            }

        except ModelRouterError as e:
            logger.error(f"[fix_code] ModelRouterError: {e}")
            raise HTTPException(status_code=500, detail=f"模型路由錯誤: {e}")
        except Exception as e:
            logger.exception("[fix_code] 未預期錯誤")
            raise HTTPException(status_code=500, detail=f"內部錯誤: {e}")

    # ------------------
    # 5. 增量需求
    # ------------------
    async def incremental_feature(
        self,
        code_version_id: int,
        instruction: str,
        db: Session,
    ) -> Dict[str, Any]:
        """
        自然語言增量需求 → 增量程式碼
        """
        from backend.models.code_version import CodeVersion

        cv = db.query(CodeVersion).filter(CodeVersion.id == code_version_id).first()
        if not cv:
            raise HTTPException(status_code=404, detail="CodeVersion 不存在")

        code_struct = await self._read_zip(cv.zip_path)

        try:
            model = self.router.select_model(task="code")
            prompt = self.chains.incremental_chain(
                stack=cv.stack,
                code_struct=code_struct,
                instruction=instruction,
            )
            inc_json = await self.router.generate(
                model=model,
                prompt=prompt,
                max_tokens=2500,
                temperature=0.5,
            )

            inc_struct = json.loads(inc_json)

            new_zip_path = await self._write_zip(
                prd_id=cv.prd_id,
                stack=cv.stack,
                code_struct=inc_struct,
                version=cv.version + 1,
            )

            # 新增版本
            new_cv = CodeVersion(
                prd_id=cv.prd_id,
                stack=cv.stack,
                zip_path=new_zip_path,
                version=cv.version + 1,
            )
            db.add(new_cv)
            db.commit()
            db.refresh(new_cv)

            return {
                "code_version_id": new_cv.id,
                "zip_path": new_zip_path,
                "stack": new_cv.stack,
            }

        except ModelRouterError as e:
            logger.error(f"[incremental_feature] ModelRouterError: {e}")
            raise HTTPException(status_code=500, detail=f"模型路由錯誤: {e}")
        except Exception as e:
            logger.exception("[incremental_feature] 未預期錯誤")
            raise HTTPException(status_code=500, detail=f"內部錯誤: {e}")

    # ------------------
    # 6. 工具函式
    # ------------------
    def _detect_stack(self, prd_md: str) -> str:
        """
        根據 PRD 關鍵字自動選框架
        """
        prd_lower = prd_md.lower()
        if "react" in prd_lower or "next" in prd_lower:
            return "react"
        if "django" in prd_lower or "flask" in prd_lower:
            return "python"
        if "express" in prd_lower or "nestjs" in prd_lower:
            return "nodejs"
        # 預設
        return "python"

    async def _repair_json(self, text: str) -> Dict[str, Any]:
        """
        若 LLM 回傳非 JSON，嘗試修復
        """
        try:
            # 簡易修復：找第一個 { 與最後一個 }
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1:
                raise ValueError("無法修復 JSON")
            fixed = text[start : end + 1]
            return json.loads(fixed)
        except Exception:
            logger.error("[repair_json] 修復失敗")
            raise HTTPException(status_code=500, detail="LLM 回傳格式錯誤")

    async def _write_zip(
        self,
        prd_id: int,
        stack: str,
        code_struct: Dict[str, Any],
        version: int = 1,
    ) -> str:
        """
        將 code_struct 寫成 ZIP 檔，回傳路徑
        """
        from backend.services.zip_builder import ZipBuilder

        output_dir = settings.ZIP_CACHE_DIR
        os.makedirs(output_dir, exist_ok=True)

        zip_name = f"{prd_id}_v{version}_{stack}.zip"
        zip_path = os.path.join(output_dir, zip_name)

        builder = ZipBuilder()
        await builder.build(
            stack=stack,
            code_struct=code_struct,
            output_path=zip_path,
        )

        return zip_path

    async def _read_zip(self, zip_path: str) -> Dict[str, Any]:
        """
        讀取 ZIP 內容，回傳 code_struct
        """
        import zipfile
        import tempfile
        import shutil

        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(tmpdir)

            # 假設 ZIP 內有 manifest.json 描述結構
            manifest_path = os.path.join(tmpdir, "manifest.json")
            if not os.path.exists(manifest_path):
                # 若無 manifest，簡易回傳檔案列表
                files = []
                for root, _, fs in os.walk(tmpdir):
                    for f in fs:
                        full = os.path.join(root, f)
                        rel = os.path.relpath(full, tmpdir)
                        files.append(rel)
                return {"files": files}

            with open(manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)


# 全域 singleton
llm_orchestrator = LLMOrchestrator()