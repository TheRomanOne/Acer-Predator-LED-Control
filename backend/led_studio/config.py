"""Runtime configuration, read from LED_STUDIO_* environment variables."""

import os
import sys
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def default_data_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "led-studio"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LED_STUDIO_")

    data_dir: Path = Field(default_factory=default_data_dir)
    host: str = "127.0.0.1"
    port: int = 8765
    fps: int = Field(default=30, ge=1, le=60)  # the LampArrays report a 33 ms minimum interval
    # Frames pushed to browser previews; lower than the hardware rate to keep the UI light.
    preview_fps: int = Field(default=15, ge=1, le=60)
