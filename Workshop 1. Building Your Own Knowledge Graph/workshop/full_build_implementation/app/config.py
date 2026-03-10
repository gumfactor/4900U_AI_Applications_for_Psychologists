from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_dotenv(dotenv_path: Path) -> None:
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class Settings:
    base_dir: Path
    data_dir: Path
    notes_dir: Path
    sources_dir: Path
    prompts_dir: Path
    logs_dir: Path
    history_dir: Path
    templates_dir: Path
    static_dir: Path
    gemini_api_key: str
    default_model: str
    high_quality_model: str
    app_host: str
    app_port: int

    @property
    def ai_enabled(self) -> bool:
        return bool(self.gemini_api_key)


def get_settings(base_dir: Path | None = None) -> Settings:
    resolved_base_dir = base_dir or Path(__file__).resolve().parent.parent
    load_dotenv(resolved_base_dir / ".env")
    data_dir = resolved_base_dir / "data"
    return Settings(
        base_dir=resolved_base_dir,
        data_dir=data_dir,
        notes_dir=data_dir / "notes",
        sources_dir=data_dir / "sources",
        prompts_dir=data_dir / "prompts",
        logs_dir=data_dir / "logs",
        history_dir=data_dir / "history",
        templates_dir=resolved_base_dir / "app" / "templates",
        static_dir=resolved_base_dir / "app" / "static",
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        default_model=os.getenv("GEMINI_DEFAULT_MODEL", "gemini-2.5-flash-lite").strip(),
        high_quality_model=os.getenv("GEMINI_HIGH_QUALITY_MODEL", "gemini-2.5-flash").strip(),
        app_host=os.getenv("APP_HOST", "127.0.0.1").strip(),
        app_port=int(os.getenv("APP_PORT", "8000")),
    )
