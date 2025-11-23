import logging
import re
from telegram.ext import (
    Application,
    CommandHandler as TGCommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.config import BOT_TOKEN, ADMIN_COMMAND
from app.database import DatabaseManager
from app.services.user_service import UserService
from app.services.subject_service import SubjectService
from app.services.homework_service import HomeworkService
from app.handlers.commands import CommandHandler as AppCommandHandler
from app.handlers.homework import HomeworkHandler
from app.handlers.settings import SettingsHandler
from app.jobs import JobScheduler

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

class Bot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.db_manager = DatabaseManager("database.json")

        # Инициализация сервисов
        self.user_service = UserService(self.db_manager)
        self.subject_service = SubjectService(self.db_manager)
        self.homework_service = HomeworkService(self.db_manager)

        # Инициализация обработчиков
        self.command_handler = AppCommandHandler(self.user_service, self.subject_service, self.homework_service)
        self.homework_handler = HomeworkHandler(self.user_service, self.subject_service, self.homework_service)
        self.settings_handler = SettingsHandler(self.user_service, self.subject_service, self.homework_service)
        
        # Инициализация планировщика задач
        self.job_scheduler = JobScheduler(self.application, self.user_service, self.homework_service, self.subject_service)

    def register_handlers(self):
        """Регистрирует все обработчики в приложении."""
        
        # Диалог для управления предметами в настройках
        subjects_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.settings_handler.add_subject_start, pattern="^add_subject$")],
            states={
                SettingsHandler.CREATING_SUBJECT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.settings_handler.add_subject_receive_name),
                ],
            },
            fallbacks=[CallbackQueryHandler(self.settings_handler.cancel_conversation, pattern="^cancel$")],
            map_to_parent={
                # Завершение и возврат к родительскому диалогу (если есть)
                ConversationHandler.END: ConversationHandler.END,
            },
            per_user=True,
            per_chat=True,
        )
        
        # Вложенный диалог для создания нового предмета
        create_subject_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.homework_handler.ask_new_subject_name, pattern="^new_subject$")],
            states={
                HomeworkHandler.CREATING_SUBJECT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.homework_handler.create_new_subject),
                ],
            },
            fallbacks=[CallbackQueryHandler(self.homework_handler.cancel_subject_creation, pattern="^cancel$")],
            map_to_parent={
                # После завершения (END) вложенного диалога, управление вернется
                # к состоянию родительского диалога SELECTING_SUBJECT
                ConversationHandler.END: HomeworkHandler.SELECTING_SUBJECT
            },
            per_user=True,
            per_chat=True,
        )

        # Основной диалог для добавления/редактирования ДЗ
        homework_conv_handler = ConversationHandler(
            entry_points=[
                MessageHandler(filters.TEXT & ~filters.COMMAND, self.homework_handler.start_add_homework),
                # Добавим точку входа по кнопке, чтобы было надежнее
                CallbackQueryHandler(self.homework_handler.start_add_homework, pattern="^add_homework$")
            ],
            states={
                HomeworkHandler.SELECTING_SUBJECT: [
                    # Сначала обрабатываем вложенный диалог
                    create_subject_conv,
                    # Затем - выбор существующего предмета
                    CallbackQueryHandler(self.homework_handler.handle_subject_selection, pattern="^select_subject:"),
                ],
                HomeworkHandler.SELECTING_DATE: [
                    CallbackQueryHandler(self.homework_handler.ask_for_day, pattern="^select_week:"),
                    CallbackQueryHandler(self.homework_handler.handle_date_selection, pattern="^select_date:"),
                    CallbackQueryHandler(self.homework_handler.back_to_week_selection, pattern="^back_to_week_selection$"),
                ],
                HomeworkHandler.SELECTING_TIME: [
                    CallbackQueryHandler(self.homework_handler.handle_time_selection, pattern="^select_hw_time:"),
                ],
            },
            fallbacks=[CallbackQueryHandler(self.homework_handler.cancel, pattern="^cancel$")],
            per_user=True,
            per_chat=True,
        )
        
        # Диалог для изменения времени напоминаний
        reminder_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.settings_handler.edit_reminder_time_start, pattern="^edit_reminder_time$")],
            states={
                SettingsHandler.EDITING_REMINDER_TIME: [
                    CallbackQueryHandler(self.settings_handler.edit_reminder_time_set, pattern="^select_offset:"),
                ],
            },
            fallbacks=[CallbackQueryHandler(self.settings_handler.cancel_conversation, pattern="^cancel$")],
            per_user=True,
            per_chat=True,
        )

        # Обработчики команд
        self.application.add_handler(TGCommandHandler("start", self.command_handler.start))
        self.application.add_handler(TGCommandHandler("help", self.command_handler.help))

        # Обработчик админ-статистики (секретная команда)
        self.application.add_handler(MessageHandler(filters.TEXT & filters.Regex(f'^{re.escape(ADMIN_COMMAND)}$'), self.command_handler.admin_stats))

        # Обработчики для навигации и управления ДЗ (через ConversationHandler)
        # Регистрируем диалоги с более конкретными entry_points первыми
        
        # ВАЖНО: homework_action_conv регистрируется ПЕРЕД homework_conv_handler,
        # чтобы его MessageHandler (для редактирования текста) имел приоритет
        # над "жадным" MessageHandler'ом добавления ДЗ.
        
        self.application.add_handler(subjects_conv_handler)
        self.application.add_handler(reminder_conv_handler)
        
        homework_action_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.homework_handler.prompt_for_homework_action, pattern="^start:(mark_done|edit_hw|delete_hw):")],
            states={
                HomeworkHandler.SELECTING_HOMEWORK_FOR_ACTION: [
                    CallbackQueryHandler(self.homework_handler.handle_homework_action, pattern="^hw_action:"),
                ],
                HomeworkHandler.EDITING_HOMEWORK_TEXT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.homework_handler.receive_new_homework_text)
                ]
            },
            fallbacks=[CallbackQueryHandler(self.command_handler.handle_navigation, pattern="^navigate_week:")],
             per_user=True,
            per_chat=True,
        )
        self.application.add_handler(homework_action_conv)
        
        # Этот диалог должен идти ПОСЛЕ homework_action_conv, так как у него "жадный" MessageHandler entry_point
        self.application.add_handler(homework_conv_handler)
        
        # Основные CallbackQueryHandlers
        self.application.add_handler(CallbackQueryHandler(self.command_handler.handle_navigation, pattern="^navigate_week:"))
        self.application.add_handler(CallbackQueryHandler(self.settings_handler.show_settings, pattern="^show_settings$"))
        self.application.add_handler(CallbackQueryHandler(self.command_handler.back_to_main_menu, pattern="^back_to_main_menu$"))
        self.application.add_handler(CallbackQueryHandler(self.settings_handler.toggle_setting, pattern="^toggle_setting:"))
        self.application.add_handler(CallbackQueryHandler(self.settings_handler.show_subjects_management, pattern="^manage_subjects$"))
        self.application.add_handler(CallbackQueryHandler(self.settings_handler.delete_subject, pattern="^delete_subject:"))
        logger.info("All handlers have been registered.")

    def run(self):
        """Запускает бота."""
        self.register_handlers()
        self.job_scheduler.setup_jobs()
        logger.info("Starting bot polling...")
        self.application.run_polling()
