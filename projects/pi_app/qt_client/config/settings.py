# config/settings.py
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_BASE_URL: str = "http://127.0.0.1:5000"
    SERIAL_PORT: str = "/dev/ttyUSB0"
    SERIAL_BAUDRATE: int = 115200

    class Config:
        env_file = Path(__file__).parent.parent / ".env"

settings = Settings()