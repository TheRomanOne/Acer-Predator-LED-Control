"""Patterns and playback state persisted as JSON files under the data directory."""

import json
import secrets
from pathlib import Path

from pydantic import BaseModel, ValidationError

from led_studio.patterns.model import Pattern, PatternBody


class PatternNotFound(LookupError):
    pass


class _PlaybackState(BaseModel):
    active_pattern_id: str | None = None


class PatternStore:
    def __init__(self, data_dir: Path) -> None:
        self._patterns_dir = data_dir / "patterns"
        self._state_file = data_dir / "state.json"
        self._patterns_dir.mkdir(parents=True, exist_ok=True)

    def list(self) -> list[Pattern]:
        patterns = [self._read(path) for path in self._patterns_dir.glob("*.json")]
        return sorted(patterns, key=lambda p: p.name.casefold())

    def get(self, pattern_id: str) -> Pattern:
        return self._read(self._path(pattern_id))

    def create(self, body: PatternBody) -> Pattern:
        pattern = Pattern(id=secrets.token_urlsafe(8), **body.model_dump())
        self._write(pattern)
        return pattern

    def update(self, pattern_id: str, body: PatternBody) -> Pattern:
        self.get(pattern_id)  # raises if missing
        pattern = Pattern(id=pattern_id, **body.model_dump())
        self._write(pattern)
        return pattern

    def delete(self, pattern_id: str) -> None:
        path = self._path(pattern_id)
        if not path.exists():
            raise PatternNotFound(pattern_id)
        path.unlink()

    def active_pattern_id(self) -> str | None:
        if not self._state_file.exists():
            return None
        return _PlaybackState.model_validate_json(
            self._state_file.read_text("utf-8")
        ).active_pattern_id

    def set_active_pattern_id(self, pattern_id: str | None) -> None:
        state = _PlaybackState(active_pattern_id=pattern_id)
        self._state_file.write_text(state.model_dump_json(), "utf-8")

    def _path(self, pattern_id: str) -> Path:
        path = self._patterns_dir / f"{pattern_id}.json"
        if path.parent != self._patterns_dir:  # ids come from clients; never escape the dir
            raise PatternNotFound(pattern_id)
        return path

    def _read(self, path: Path) -> Pattern:
        if not path.exists():
            raise PatternNotFound(path.stem)
        try:
            return Pattern.model_validate_json(path.read_text("utf-8"))
        except (ValidationError, json.JSONDecodeError, ValueError) as exc:
            raise ValueError(f"pattern file {path} is corrupt: {exc}") from exc

    def _write(self, pattern: Pattern) -> None:
        self._path(pattern.id).write_text(pattern.model_dump_json(indent=2), "utf-8")
