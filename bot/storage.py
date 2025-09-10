import json
from pathlib import Path
from typing import Dict, Any

BASE = Path.cwd() / "nuclear-codes"
BASE.mkdir(exist_ok=True)

USERS_FILE = BASE / "users.json"
TOKENS_FILE = BASE / "tokens.json"


class JSONStorage:
    def __init__(self, users_path: Path = USERS_FILE, tokens_path: Path = TOKENS_FILE):
        self.users_path = users_path
        self.tokens_path = tokens_path

    def _load(self, path: Path, default):
        if not path.exists():
            return default
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, path: Path, data):
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_users(self) -> Dict[str, int]:
        return self._load(self.users_path, {})

    def save_users(self, users: Dict[str, int]):
        self._save(self.users_path, users)

    def get_tokens(self) -> Dict[str, Dict[str, Any]]:
        return self._load(self.tokens_path, {})

    def save_tokens(self, tokens: Dict[str, Dict[str, Any]]):
        self._save(self.tokens_path, tokens)

