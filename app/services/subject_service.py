import uuid
from typing import Dict, Any, List
from app.database import DatabaseManager

class SubjectService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def get_subjects(self, user_id: str) -> List[Dict[str, Any]]:
        """Gets all subjects for a user as a list of dicts."""
        data = await self.db_manager.load_data()
        subjects_data = data.get(str(user_id), {}).get("subjects", {})
        if isinstance(subjects_data, dict):
            return [{"id": key, **value} for key, value in subjects_data.items()]
        return subjects_data

    async def add_subject(self, user_id: str, subject_name: str) -> str:
        data = await self.db_manager.load_data()
        user_id_str = str(user_id)

        if user_id_str not in data:
            data[user_id_str] = {"subjects": {}, "homework": [], "settings": {}}

        subjects = data[user_id_str].get("subjects", {})
        if not isinstance(subjects, dict):
            subjects = {}
            
        new_subject_key = str(uuid.uuid4())
        subjects[new_subject_key] = {"name": subject_name}
        data[user_id_str]["subjects"] = subjects

        await self.db_manager.save_data(data)
        return new_subject_key

    async def delete_subject(self, user_id: str, subject_key: str):
        """Deletes a subject and all related homework."""
        data = await self.db_manager.load_data()
        user_id_str = str(user_id)
        
        if user_id_str not in data:
            return

        user_data = data[user_id_str]

        if subject_key in user_data.get("subjects", {}):
            del user_data["subjects"][subject_key]

        homework = user_data.get("homework", [])
        user_data["homework"] = [hw for hw in homework if hw.get("subject_key") != subject_key]

        await self.db_manager.save_data(data)
