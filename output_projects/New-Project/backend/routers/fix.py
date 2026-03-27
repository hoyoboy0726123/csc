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

router = APIRouter(prefix="/api/v1", tags=["fix"])

class FixRequest(BaseModel):
    prd_id: int
    error_message: Optional[str] = None
    instruction: Optional[str] = None
    stack: str

class FixResponse(BaseModel):
    task_id: str
    status: str
    message: str

class FixStatusResponse(BaseModel):
    status: str
    fixed_code: Optional[str] = None
    zip_path: Optional[str] = None
    error: Optional[str] = None

@router.post("/fix", response_model=FixResponse)
async def create_fix_task(
    request: FixRequest,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    創建代碼修復任務
    支援兩種模式：
    1. 錯誤修復：提供 error_message，AI 自動診斷並修復
    2. 功能微調：提供 instruction，AI 根據自然語言進行增量修改
    """
    # 驗證 PRD 存在且屬於當前用戶
    prd = db.query(PRDHistory).filter(
        PRDHistory.id == request.prd_id,
        PRDHistory.user_id == current_user.id
    ).first()
    
    if not prd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PRD not found or access denied"
        )
    
    # 驗證至少提供一種修復模式
    if not request.error_message and not request.instruction:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either error_message or instruction must be provided"
        )
    
    # 獲取最新的代碼版本
    latest_code = db.query(CodeVersion).filter(
        CodeVersion.prd_id == request.prd_id,
        CodeVersion.stack == request.stack
    ).order_by(CodeVersion.version.desc()).first()
    
    if not latest_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No code version found for stack {request.stack}"
        )
    
    # 生成任務 ID
    task_id = str(uuid.uuid4())
    
    # 創建修復任務記錄（這裡簡化處理，實際可考慮存入資料庫）
    task_info = {
        "task_id": task_id,
        "user_id": current_user.id,
        "prd_id": request.prd_id,
        "stack": request.stack,
        "error_message": request.error_message,
        "instruction": request.instruction,
        "original_zip_path": latest_code.zip_path,
        "status": "processing",
        "created_at": datetime.utcnow().isoformat()
    }
    
    # 保存任務信息到臨時文件（實際生產環境應使用 Redis 或資料庫）
    tasks_dir = os.path.join(get_settings().TEMP_DIR, "fix_tasks")
    os.makedirs(tasks_dir, exist_ok=True)
    task_file = os.path.join(tasks_dir, f"{task_id}.json")
    
    with open(task_file, "w", encoding="utf-8") as f:
        json.dump(task_info, f, ensure_ascii=False, indent=2)
    
    # 異步處理修復任務（這裡簡化為同步處理，實際應使用隊列）
    try:
        orchestrator = LLMOrchestrator(
            gemini_key=current_user.gemini_key_enc,
            groq_key=current_user.groq_key_enc
        )
        
        # 讀取原始 ZIP 內容
        with open(latest_code.zip_path, "rb") as f:
            original_zip_content = f.read()
        
        # 根據模式選擇修復鏈
        if request.error_message:
            # 錯誤修復模式
            fixed_content = await orchestrator.fix_error(
                prd_content=prd.prd_md,
                stack=request.stack,
                error_message=request.error_message,
                zip_content=original_zip_content
            )
        else:
            # 功能微調模式
            fixed_content = await orchestrator.incremental_develop(
                prd_content=prd.prd_md,
                stack=request.stack,
                instruction=request.instruction,
                zip_content=original_zip_content
            )
        
        # 生成新的 ZIP 文件
        zip_builder = ZipBuilder()
        new_zip_path = await zip_builder.rebuild_zip(
            original_path=latest_code.zip_path,
            fixed_content=fixed_content,
            task_id=task_id
        )
        
        # 更新任務狀態
        task_info.update({
            "status": "completed",
            "fixed_zip_path": new_zip_path,
            "completed_at": datetime.utcnow().isoformat()
        })
        
        with open(task_file, "w", encoding="utf-8") as f:
            json.dump(task_info, f, ensure_ascii=False, indent=2)
        
    except Exception as e:
        # 記錄錯誤信息
        task_info.update({
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.utcnow().isoformat()
        })
        
        with open(task_file, "w", encoding="utf-8") as f:
            json.dump(task_info, f, ensure_ascii=False, indent=2)
    
    return FixResponse(
        task_id=task_id,
        status="processing",
        message="Fix task created successfully"
    )

@router.get("/fix/{task_id}/status", response_model=FixStatusResponse)
async def get_fix_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    獲取修復任務狀態
    """
    tasks_dir = os.path.join(get_settings().TEMP_DIR, "fix_tasks")
    task_file = os.path.join(tasks_dir, f"{task_id}.json")
    
    if not os.path.exists(task_file):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    with open(task_file, "r", encoding="utf-8") as f:
        task_info = json.load(f)
    
    # 驗證任務屬於當前用戶
    if task_info["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    response = FixStatusResponse(
        status=task_info["status"]
    )
    
    if task_info["status"] == "completed":
        response.zip_path = task_info.get("fixed_zip_path")
    elif task_info["status"] == "failed":
        response.error = task_info.get("error")
    
    return response

@router.delete("/fix/{task_id}")
async def delete_fix_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    刪除修復任務（清理臨時文件）
    """
    tasks_dir = os.path.join(get_settings().TEMP_DIR, "fix_tasks")
    task_file = os.path.join(tasks_dir, f"{task_id}.json")
    
    if not os.path.exists(task_file):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    with open(task_file, "r", encoding="utf-8") as f:
        task_info = json.load(f)
    
    # 驗證任務屬於當前用戶
    if task_info["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # 清理相關文件
    if "fixed_zip_path" in task_info and os.path.exists(task_info["fixed_zip_path"]):
        os.remove(task_info["fixed_zip_path"])
    
    os.remove(task_file)
    
    return {"message": "Task deleted successfully"}