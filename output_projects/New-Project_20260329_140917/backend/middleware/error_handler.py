from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from typing import Union
import traceback
from utils.logger import logger


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    全域例外捕獲與標準化回應
    依據 PRD 非功能需求：安全性(不洩露堆疊)、可用性(統一日誌)
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            logger.error(f"Unhandled error: {exc}\n{traceback.format_exc()}")
            return self._build_response(exc)

    def _build_response(self, exc: Exception) -> JSONResponse:
        status_code, detail, code = self._parse_exception(exc)
        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": code,
                    "detail": detail,
                }
            },
            headers={"X-Content-Type-Options": "nosniff"},
        )

    def _parse_exception(
        self, exc: Exception
    ) -> Union[tuple[int, str, str], tuple[int, str, str]]:
        """
        將常見例外對應到統一格式
        回傳 (http_status, detail, code)
        """
        if isinstance(exc, ValueError):
            return (
                HTTP_400_BAD_REQUEST,
                "Invalid input value",
                "INVALID_INPUT",
            )
        if isinstance(exc, PermissionError):
            return (
                HTTP_403_FORBIDDEN,
                "Insufficient permissions",
                "FORBIDDEN",
            )
        if isinstance(exc, LookupError):
            return (
                HTTP_404_NOT_FOUND,
                "Resource not found",
                "NOT_FOUND",
            )
        # 其餘未預期例外統一 500
        return (
            HTTP_500_INTERNAL_SERVER_ERROR,
            "Internal server error",
            "INTERNAL_ERROR",
        )