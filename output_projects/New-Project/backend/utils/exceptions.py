from fastapi import HTTPException, status
from typing import Optional, Dict, Any


class V2CException(HTTPException):
    """Base exception for Voice-to-Code Pipeline"""
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class AudioProcessingError(V2CException):
    """Raised when audio file processing fails"""
    def __init__(self, detail: str = "Audio processing failed"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class STTError(V2CException):
    """Raised when speech-to-text conversion fails"""
    def __init__(self, detail: str = "Speech-to-text conversion failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class LLMError(V2CException):
    """Raised when LLM orchestration fails"""
    def __init__(self, detail: str = "LLM processing failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class PRDGenerationError(V2CException):
    """Raised when PRD generation fails"""
    def __init__(self, detail: str = "PRD generation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class CodeGenerationError(V2CException):
    """Raised when code generation fails"""
    def __init__(self, detail: str = "Code generation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class CodeFixError(V2CException):
    """Raised when code fixing fails"""
    def __init__(self, detail: str = "Code fix failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class ZipBuildError(V2CException):
    """Raised when ZIP building fails"""
    def __init__(self, detail: str = "ZIP building failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class AuthenticationError(V2CException):
    """Raised when authentication fails"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )


class AuthorizationError(V2CException):
    """Raised when authorization fails"""
    def __init__(self, detail: str = "Authorization failed"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class ResourceNotFoundError(V2CException):
    """Raised when resource is not found"""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class ValidationError(V2CException):
    """Raised when validation fails"""
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


class QuotaExceededError(V2CException):
    """Raised when user quota is exceeded"""
    def __init__(self, detail: str = "Quota exceeded"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
        )


class EncryptionError(V2CException):
    """Raised when encryption/decryption fails"""
    def __init__(self, detail: str = "Encryption operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class DatabaseError(V2CException):
    """Raised when database operation fails"""
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class ModelRouterError(V2CException):
    """Raised when model routing fails"""
    def __init__(self, detail: str = "Model routing failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class PromptChainError(V2CException):
    """Raised when prompt chain execution fails"""
    def __init__(self, detail: str = "Prompt chain execution failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


def handle_exception(exc: Exception) -> V2CException:
    """Convert generic exceptions to V2C exceptions"""
    if isinstance(exc, V2CException):
        return exc
    
    # Handle specific exception types
    if "audio" in str(exc).lower() or "whisper" in str(exc).lower():
        return STTError(str(exc))
    
    if "llm" in str(exc).lower() or "gemini" in str(exc).lower() or "groq" in str(exc).lower():
        return LLMError(str(exc))
    
    if "encryption" in str(exc).lower() or "crypto" in str(exc).lower():
        return EncryptionError(str(exc))
    
    if "database" in str(exc).lower() or "sqlite" in str(exc).lower():
        return DatabaseError(str(exc))
    
    # Default to generic internal server error
    return V2CException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Internal server error: {str(exc)}"
    )