from fastapi import APIRouter
from .auth import router as auth_router
from .cases import router as cases_router
from .analytics import router as analytics_router
from .upload import router as upload_router
from .assignment import router as assignment_router
from .export import router as export_router
from .ai import router as ai_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(cases_router, prefix="/cases", tags=["cases"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_router.include_router(upload_router, prefix="/upload", tags=["upload"])
api_router.include_router(assignment_router, prefix="/assignment", tags=["assignment"])
api_router.include_router(export_router, prefix="/export", tags=["export"])
api_router.include_router(ai_router, prefix="/ai", tags=["ai"])