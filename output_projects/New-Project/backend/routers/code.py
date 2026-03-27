from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import uuid
import os
import json
from datetime import datetime

from backend.database.connection import get_db
from backend.models.user import User
from backend.models.prd import PRDHistory
from backend.models.code_version import CodeVersion
from backend.services.llm_orchestrator import LLMOrchestrator
from backend.services.zip_builder import ZipBuilder
from backend.utils.config import get_settings
from backend.utils.exceptions import V2CException
from backend.routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/code", tags=["code"])

class GenerateCodeRequest(BaseModel):
    prd_id: int
    stack: Optional[str] = None  # python, react, nodejs
    model_preference: Optional[str] = None  # gemini, groq

class GenerateCodeResponse(BaseModel):
    task_id: str
    status: str
    message: str

class CodeStatusResponse(BaseModel):
    task_id: str
    status: str
    prd_id: int
    stack: Optional[str]
    version: int
    zip_path: Optional[str]
    created_at: datetime
    error: Optional[str]

@router.post("/generate", response_model=GenerateCodeResponse)
async def generate_code(
    request: GenerateCodeRequest,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    根據已凍結的 PRD 生成代碼
    """
    # 1. 檢查 PRD 存在且屬於當前用戶
    prd = db.query(PRDHistory).filter(
        PRDHistory.id == request.prd_id,
        PRDHistory.user_id == current_user.id
    ).first()
    if not prd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PRD not found"
        )
    if not prd.frozen:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PRD must be frozen before code generation"
        )

    # 2. 生成唯一 task_id
    task_id = str(uuid.uuid4())

    # 3. 初始化 orchestrator
    orchestrator = LLMOrchestrator(
        gemini_key_enc=current_user.gemini_key_enc,
        groq_key_enc=current_user.groq_key_enc,
        model_preference=request.model_preference
    )

    # 4. 自動推薦技術棧（若未指定）
    if not request.stack:
        request.stack = orchestrator.recommend_stack(prd.prd_md)

    # 5. 生成代碼
    try:
        code_files = orchestrator.generate_code(
            prd_md=prd.prd_md,
            stack=request.stack
        )
    except V2CException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

    # 6. 打包 ZIP
    zip_builder = ZipBuilder(stack=request.stack)
    zip_path = zip_builder.build(code_files, task_id)

    # 7. 寫入 code_version 表
    code_version = CodeVersion(
        prd_id=request.prd_id,
        stack=request.stack,
        zip_path=zip_path,
        version=1
    )
    db.add(code_version)
    db.commit()
    db.refresh(code_version)

    return GenerateCodeResponse(
        task_id=task_id,
        status="completed",
        message="Code generated successfully"
    )

@router.get("/status/{task_id}", response_model=CodeStatusResponse)
async def get_code_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    查詢代碼生成狀態
    """
    # 透過 task_id 找到對應的 code_version
    code_version = db.query(CodeVersion).join(
        PRDHistory, CodeVersion.prd_id == PRDHistory.id
    ).filter(
        PRDHistory.user_id == current_user.id,
        CodeVersion.zip_path.contains(task_id)
    ).first()

    if not code_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return CodeStatusResponse(
        task_id=task_id,
        status="completed",
        prd_id=code_version.prd_id,
        stack=code_version.stack,
        version=code_version.version,
        zip_path=code_version.zip_path,
        created_at=code_version.created_at,
        error=None
    )

@router.get("/download/{task_id}")
async def download_code(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    下載生成的 ZIP 檔案
    """
    code_version = db.query(CodeVersion).join(
        PRDHistory, CodeVersion.prd_id == PRDHistory.id
    ).filter(
        PRDHistory.user_id == current_user.id,
        CodeVersion.zip_path.contains(task_id)
    ).first()

    if not code_version or not os.path.exists(code_version.zip_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ZIP file not found"
        )

    from fastapi.responses import FileResponse
    return FileResponse(
        path=code_version.zip_path,
        media_type="application/zip",
        filename=os.path.basename(code_version.zip_path)
    )

@router.post("/regenerate/{task_id}", response_model=GenerateCodeResponse)
async def regenerate_code(
    task_id: str,
    request: GenerateCodeRequest,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    重新生成代碼（增量版本）
    """
    # 檢查舊版本存在
    old_version = db.query(CodeVersion).join(
        PRDHistory, CodeVersion.prd_id == PRDHistory.id
    ).filter(
        PRDHistory.user_id == current_user.id,
        CodeVersion.zip_path.contains(task_id)
    ).first()
    if not old_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original task not found"
        )

    # 生成新版本
    new_task_id = str(uuid.uuid4())
    orchestrator = LLMOrchestrator(
        gemini_key_enc=current_user.gemini_key_enc,
        groq_key_enc=current_user.groq_key_enc,
        model_preference=request.model_preference
    )
    prd = db.query(PRDHistory).filter(PRDHistory.id == request.prd_id).first()
    code_files = orchestrator.generate_code(
        prd_md=prd.prd_md,
        stack=request.stack or old_version.stack
    )
    zip_builder = ZipBuilder(stack=request.stack or old_version.stack)
    zip_path = zip_builder.build(code_files, new_task_id)

    # 寫入新版本
    new_version = CodeVersion(
        prd_id=request.prd_id,
        stack=request.stack or old_version.stack,
        zip_path=zip_path,
        version=old_version.version + 1
    )
    db.add(new_version)
    db.commit()

    return GenerateCodeResponse(
        task_id=new_task_id,
        status="completed",
        message=f"Code regenerated at version {new_version.version}"
    )