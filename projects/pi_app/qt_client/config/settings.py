# config/settings.py
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_BASE_URL: str = "http://127.0.0.1:5001"
    SERIAL_PORT: str = "/dev/ttyACM0"  # Update to your serial port
    SERIAL_BAUDRATE: int = 115200
    ANCHORS: list = [  # Add anchor positions to settings
        (0, 630),
        (5000, 5300),
        (5100, 0),
        (0, 5392)
    ]

    class Config:
        env_file = Path(__file__).parent.parent / ".env"

settings = Settings()