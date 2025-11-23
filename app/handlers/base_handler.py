from app.services.user_service import UserService
from app.services.subject_service import SubjectService
from app.services.homework_service import HomeworkService
# from app.ui.keyboards import KeyboardFactory # Will be uncommented later

class BaseHandler:
    def __init__(self, user_service: UserService, subject_service: SubjectService, homework_service: HomeworkService):
        self.user_service = user_service
        self.subject_service = subject_service
        self.homework_service = homework_service
        # self.keyboard_factory = KeyboardFactory()
