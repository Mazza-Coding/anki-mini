"""Global configuration management."""

from pathlib import Path
from typing import Dict, Any
from .utils import read_json, atomic_write_json, get_data_dir


DEFAULT_CONFIG = {
    "daily_new": 20,
    "daily_review": 200,
    "lenient_threshold": 2,
    "autosave_every": 10,
    "timezone": "local",
    "default_deck_on_init": "default"
}


class Config:
    """Global configuration singleton."""
    
    def __init__(self, data_dir: Path):
        self.path = data_dir.parent / 'settings.json'
        self.data = self._load()
    
    def _load(self) -> Dict[str, Any]:
        """Load config from disk; create with defaults if missing."""
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_json(self.path, DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()
        return {**DEFAULT_CONFIG, **read_json(self.path)}
    
    def save(self) -> None:
        """Save config to disk."""
        atomic_write_json(self.path, self.data)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value."""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set config value and save."""
        self.data[key] = value
        self.save()


def load_config(data_dir: Path = None) -> Config:
    """Load global config."""
    if data_dir is None:
        data_dir = get_data_dir()
    return Config(data_dir)
