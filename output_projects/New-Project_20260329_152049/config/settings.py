import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

class Settings:
    def __init__(self):
        load_dotenv()
        self._load_logging_config()

    def _load_logging_config(self):
        cfg_path = Path(__file__).with_name("logging.yaml")
        with cfg_path.open(encoding="utf-8") as f:
            self.logging_config = yaml.safe_load(f)

    @staticmethod
    def get_db_path() -> str:
        return os.getenv("DB_PATH", str(Path(__file__).resolve().parent.parent / "data" / "ai_csm.db"))

    @staticmethod
    def get_llm_model() -> str:
        return os.getenv("LLM_MODEL", "gpt-3.5-turbo")

    @staticmethod
    def get_openai_key() -> str:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY not found in environment")
        return key

settings = Settings()