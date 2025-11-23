import uuid
from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.database import DatabaseManager
from app.utils import get_week_dates 

class HomeworkService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def get_homework_for_week(self, user_id: str, week_offset: int) -> List[Dict[str, Any]]:
        """Gets all homework for a user for a specific week."""
        data = await self.db_manager.load_data()
        user_homework = data.get(str(user_id), {}).get("homework", [])
        
        start_week, end_week = get_week_dates(week_offset)
        
        weekly_homework = sorted(
            [hw for hw in user_homework if start_week <= datetime.strptime(hw['deadline_date'], '%Y-%m-%d').date() <= end_week],
            key=lambda x: x['deadline_date']
        )
        return weekly_homework

    async def add_homework(self, user_id: str, hw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Adds a new homework assignment for a user."""
        data = await self.db_manager.load_data()
        user_id_str = str(user_id)

        if user_id_str not in data:
            data[user_id_str] = {"subjects": {}, "homework": [], "settings": {}}

        new_hw = {
            "id": str(uuid.uuid4()),
            "subject_key": hw_data['subject_key'],
            "deadline_date": hw_data['deadline_date'],
            "text": hw_data.get('text'),
            "photo_id": hw_data.get('photo_id'),
            "status": "pending",
            "notification_time": hw_data.get('notification_time')
        }

        data[user_id_str]["homework"].append(new_hw)
        await self.db_manager.save_data(data)
        return new_hw

    async def get_all_homework(self, user_id: str) -> List[Dict[str, Any]]:
        """Gets all homework for a user."""
        data = await self.db_manager.load_data()
        user_homework = data.get(str(user_id), {}).get("homework", [])
        return sorted(user_homework, key=lambda x: x['deadline_date'])

    async def delete_old_homework(self, weeks: int = 3):
        """Deletes homework older than specified number of weeks."""
        data = await self.db_manager.load_data()
        cutoff_date = datetime.now().date() - timedelta(weeks=weeks)
        
        for user_id, user_data in data.items():
            if "homework" in user_data:
                user_data["homework"] = [
                    hw for hw in user_data["homework"]
                    if datetime.strptime(hw['deadline_date'], '%Y-%m-%d').date() >= cutoff_date
                ]
        
        await self.db_manager.save_data(data)

    async def update_homework_text(self, user_id: str, hw_id: str, new_text: str) -> bool:
        """Updates the text of a specific homework assignment."""
        data = await self.db_manager.load_data()
        user_homework = data.get(str(user_id), {}).get("homework", [])
        
        target_hw = next((hw for hw in user_homework if hw.get('id') == hw_id), None)
        if target_hw:
            target_hw['text'] = new_text
            await self.db_manager.save_data(data)
            return True
        return False

    async def mark_homework_as_done(self, user_id: str, hw_id: str) -> bool:
        """Marks a homework assignment as done."""
        data = await self.db_manager.load_data()
        user_homework = data.get(str(user_id), {}).get("homework", [])

        target_hw = next((hw for hw in user_homework if hw.get('id') == hw_id), None)
        if target_hw:
            target_hw['status'] = 'done'
            await self.db_manager.save_data(data)
            return True
        return False

    async def delete_homework(self, user_id: str, hw_id: str) -> bool:
        """Deletes a homework assignment."""
        data = await self.db_manager.load_data()
        user_id_str = str(user_id)
        
        if user_id_str not in data:
            return False

        user_homework = data[user_id_str].get("homework", [])
        hw_to_delete = next((hw for hw in user_homework if hw.get('id') == hw_id), None)

        if hw_to_delete:
            user_homework.remove(hw_to_delete)
            await self.db_manager.save_data(data)
            return True
        return False

    async def get_total_homework_count(self) -> int:
        """Gets total number of homework assignments across all users."""
        data = await self.db_manager.load_data()
        total_count = 0
        for user_data in data.values():
            total_count += len(user_data.get("homework", []))
        return total_count
