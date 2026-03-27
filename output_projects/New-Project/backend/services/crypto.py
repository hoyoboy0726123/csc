import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from backend.utils.config import settings

class CryptoService:
    """
    統一加密/解密服務，用於儲存 API 金鑰等敏感資料。
    採用 AES-256 (Fernet) 加密，並以 PBKDF2 從固定密碼衍生金鑰。
    """

    def __init__(self):
        # 若環境變數未提供 MASTER_KEY，則使用預設值（僅供開發）
        master_key = settings.MASTER_KEY or "Voice2CodePipeline2024"
        salt = settings.CRYPTO_SALT or b"Voice2CodeSalt"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        self.cipher = Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        """
        加密明文，回傳 base64 編碼的密文。
        """
        token = self.cipher.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(token).decode()

    def decrypt(self, ciphertext: str) -> str:
        """
        解密 base64 編碼的密文，回傳明文。
        """
        token = base64.urlsafe_b64decode(ciphertext.encode())
        return self.cipher.decrypt(token).decode()

    def encrypt_key(self, api_key: str) -> str:
        """
        專門用於加密 API 金鑰，統一介面方便未來更換演算法。
        """
        return self.encrypt(api_key)

    def decrypt_key(self, encrypted_key: str) -> str:
        """
        專門用於解密 API 金鑰，統一介面方便未來更換演算法。
        """
        return self.decrypt(encrypted_key)


# 全域單例
crypto_service = CryptoService()