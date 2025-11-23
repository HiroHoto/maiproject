import logging
from datetime import timedelta, datetime
import pytz
from telegram.ext import Application, ContextTypes
from telegram.constants import ParseMode

from app.services.user_service import UserService
from app.services.homework_service import HomeworkService
from app.services.subject_service import SubjectService
from app.utils import get_moscow_time

# Настройка логирования
logger = logging.getLogger(__name__)

def parse_time(time_str: str) -> datetime.time:
    """Парсит строку времени (например, '09:00', '14:30') в объект time."""
    if not time_str:
        return datetime.strptime("09:00", "%H:%M").time()
    return datetime.strptime(time_str, "%H:%M").time()

class JobScheduler:
    def __init__(self, application: Application, user_service: UserService, homework_service: HomeworkService, subject_service: SubjectService):
        self.application = application
        self.user_service = user_service
        self.homework_service = homework_service
        self.subject_service = subject_service

    def setup_jobs(self):
        """Настраивает и запускает все фоновые задачи."""
        job_queue = self.application.job_queue
        # Запускаем ежедневные напоминания в разное время
        self._setup_daily_reminders(job_queue)
        # Запускаем очистку старых данных раз в день
        job_queue.run_daily(self.cleanup_old_data, time=datetime.strptime("03:00", "%H:%M").time(), days=(0, 1, 2, 3, 4, 5, 6))
        logger.info("All jobs have been scheduled.")

    def _setup_daily_reminders(self, job_queue):
        """Настраивает ежедневные напоминания для всех возможных времен."""
        # Создаем задачи для всех времен от 00:00 до 23:30 с шагом 30 минут
        for hour in range(24):
            for minute in [0, 30]:
                time_str = f"{hour:02d}:{minute:02d}"
                time_obj = datetime.strptime(time_str, "%H:%M").time()
                job_queue.run_daily(
                    self.send_daily_reminders,
                    time=time_obj,
                    days=(0, 1, 2, 3, 4, 5, 6),
                    name=f"daily_reminders_{time_str}"
                )

    async def send_daily_reminders(self, context: ContextTypes.DEFAULT_TYPE):
        """Отправляет ежедневные напоминания о ДЗ в указанное время."""
        logger.info("Job: Sending daily reminders...")
        now = get_moscow_time()
        current_time_str = now.strftime("%H:%M")
        
        all_users = await self.user_service.get_all_users()
        
        for user in all_users:
            user_id = user['id']
            settings = user.get("settings", {})
            if not settings.get("reminders_enabled"):
                continue

            all_homework = await self.homework_service.get_all_homework(user_id)
            subjects = await self.subject_service.get_subjects(user_id)
            
            # Фильтруем ДЗ, для которых установлено текущее время напоминания
            homework_for_reminder = [
                hw for hw in all_homework
                if hw.get("status") != 'done' and
                   hw.get("notification_time") == current_time_str
            ]
            
            if not homework_for_reminder:
                continue
                
            # Формируем сообщение со всеми ДЗ на сегодня
            message_lines = ["🔔 *Ежедневное напоминание*\n"]
            
            for hw in homework_for_reminder:
                subject_name = subjects.get(hw.get('subject_key'), {}).get('name', "Неизвестно")
                deadline = datetime.fromisoformat(hw['deadline_date']).strftime('%d.%m.%Y')
                message_lines.append(f"• *{subject_name}*: {hw['text']} (до {deadline})")
            
            if len(message_lines) > 1:
                full_message = "\n".join(message_lines)
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=full_message,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    logger.info(f"Sent daily reminder to user {user_id} at {current_time_str}")
                except Exception as e:
                    logger.error(f"Error sending daily reminder to user {user_id}: {e}")

    async def cleanup_old_data(self, context: ContextTypes.DEFAULT_TYPE):
        """Удаляет ДЗ старше 3 недель."""
        logger.info("Job: Cleaning up old data...")
        await self.homework_service.delete_old_homework(weeks=3)
        logger.info("Old data cleanup finished.")
