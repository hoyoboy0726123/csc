from typing import Optional
import requests
from requests.exceptions import RequestException
from backend.config import Settings
from backend.utils.logger import logger


class ErpService:
    """
    對接外部 ERP 以驗證產品是否存在。
    所有方法皆為同步，方便後續擴充 cache 或 async 版本。
    """

    def __init__(self, settings: Settings):
        self.base_url = settings.ERP_API_BASE_URL
        self.timeout = settings.ERP_API_TIMEOUT
        self.api_key = settings.ERP_API_KEY
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def validate_product(self, product_id: str) -> bool:
        """
        驗證 product_id 是否存在於 ERP。
        回傳 True 表示存在；False 表示不存在或查詢失敗。
        """
        if not product_id:
            return False

        url = f"{self.base_url}/products/{product_id}"
        try:
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                return True
            if resp.status_code == 404:
                logger.info("ERP 查無 product_id=%s", product_id)
                return False
            logger.warning("ERP 回應異常 status=%s product_id=%s", resp.status_code, product_id)
            return False
        except RequestException as exc:
            logger.error("ERP 連線失敗 product_id=%s error=%s", product_id, exc)
            return False