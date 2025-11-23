from typing import Dict, Any, List
from app.database import DatabaseManager

class UserService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def get_or_create_user(self, user_id: str) -> Dict[str, Any]:
        """Gets user data or creates a new user if one doesn't exist."""
        data = await self.db_manager.load_data()
        user_id_str = str(user_id)
        if user_id_str not in data:
            data[user_id_str] = {
                "subjects": {},
                "homework": [],
                "settings": {
                    "reminders_enabled": True,
                    "default_notification_time": "09:00",
                    "ask_for_notification_time": False
                }
            }
            await self.db_manager.save_data(data)
        return data[user_id_str]

    async def get_user_settings(self, user_id: str) -> Dict[str, Any]:
        """Gets user settings."""
        user_data = await self.get_or_create_user(user_id)
        return user_data.get("settings", {})

    async def update_user_setting(self, user_id: str, setting_name: str, value: Any):
        """Updates a specific user setting."""
        data = await self.db_manager.load_data()
        user_id_str = str(user_id)
        if user_id_str in data:
            if "settings" not in data[user_id_str]:
                data[user_id_str]["settings"] = {}
            data[user_id_str]["settings"][setting_name] = value
            await self.db_manager.save_data(data)

    async def toggle_user_setting(self, user_id: str, setting_name: str) -> bool:
        """Toggles a boolean user setting."""
        settings = await self.get_user_settings(user_id)
        current_value = settings.get(setting_name, False)
        new_value = not current_value
        await self.update_user_setting(user_id, setting_name, new_value)
        return new_value

    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Gets all users from the database."""
        data = await self.db_manager.load_data()
        return [{"id": user_id, **user_data} for user_id, user_data in data.items()]

    async def get_total_users_count(self) -> int:
        """Gets total number of users."""
        data = await self.db_manager.load_data()
        return len(data)
