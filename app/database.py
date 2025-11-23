import json
import asyncio
from typing import Dict, Any

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.lock = asyncio.Lock()

    async def load_data(self) -> Dict[str, Any]:
        """Loads data from the JSON file."""
        async with self.lock:
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return {}

    async def save_data(self, data: Dict[str, Any]):
        """Saves data to the JSON file."""
        async with self.lock:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

# The instance will be created in the Bot class