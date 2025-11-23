import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode

from app.handlers.base_handler import BaseHandler
from app.ui.keyboards import KeyboardFactory
import app.ui.text as text

# Инициализация логгера
logger = logging.getLogger(__name__)

class HomeworkHandler(BaseHandler):
    # Состояния диалога
    (
        SELECTING_SUBJECT, SELECTING_DATE, CREATING_SUBJECT,
        SELECTING_HOMEWORK_FOR_ACTION, EDITING_HOMEWORK_TEXT, SELECTING_TIME
    ) = range(6)

    # --- Точка входа в диалог ---
    async def start_add_homework(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Начинает диалог добавления нового ДЗ."""
        if update.message.text:
            context.user_data['homework_text'] = update.message.text
        
        user_id = str(update.effective_user.id)
        subjects = await self.subject_service.get_subjects(user_id)
        
        await update.message.reply_text(
            "Выберите предмет:",
            reply_markup=KeyboardFactory.get_subjects_keyboard(subjects)
        )
        return self.SELECTING_SUBJECT

    # --- Обработка выбора предмета ---
    async def handle_subject_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обрабатывает выбор предмета и запрашивает дату."""
        query = update.callback_query
        await query.answer()

        # Для создания нового предмета теперь будет использоваться вложенный диалог
        # Поэтому مستقیم обработка 'new_subject' здесь больше не нужна.
        context.user_data['subject_key'] = query.data.split(':')[1]
        
        await query.edit_message_text(
            "Выберите неделю:",
            reply_markup=KeyboardFactory.get_week_selection_keyboard()
        )
        return self.SELECTING_DATE

    # --- Создание нового предмета ---
    async def ask_new_subject_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Запрашивает у пользователя название нового предмета."""
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "Введите название нового предмета:",
            reply_markup=KeyboardFactory.get_cancel_keyboard() # Кнопка отмены
        )
        return self.CREATING_SUBJECT

    async def create_new_subject(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Создает новый предмет и завершает вложенный диалог."""
        new_subject_name = update.message.text.strip()
        user_id = str(update.effective_user.id)

        if not new_subject_name:
            await update.message.reply_text("Название не может быть пустым. Попробуйте снова.")
            return self.CREATING_SUBJECT

        await self.subject_service.add_subject(user_id, new_subject_name)
        await update.message.reply_text(f"Предмет '{new_subject_name}' добавлен!")

        # Показываем обновленный список предметов, не теряя исходный текст ДЗ
        subjects = await self.subject_service.get_subjects(user_id)
        await update.message.reply_text(
            "Выберите предмет:",
            reply_markup=KeyboardFactory.get_subjects_keyboard(subjects)
        )
        
        # Завершаем вложенный диалог, родительский останется в состоянии ожидания выбора предмета
        return ConversationHandler.END

    async def cancel_subject_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Отменяет создание предмета и возвращает к выбору."""
        query = update.callback_query
        await query.answer()
        user_id = str(update.effective_user.id)
        subjects = await self.subject_service.get_subjects(user_id)
        await query.edit_message_text(
            "Выберите предмет:",
            reply_markup=KeyboardFactory.get_subjects_keyboard(subjects)
        )
        return ConversationHandler.END # Завершаем вложенный диалог

    # --- Обработка выбора даты ---
    async def ask_for_day(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Запрашивает день недели после выбора недели."""
        query = update.callback_query
        await query.answer()
        week_start_date = query.data.split(':')[1]
        
        await query.edit_message_text(
            "Теперь выберите день:",
            reply_markup=KeyboardFactory.get_day_of_week_keyboard(week_start_date)
        )
        return self.SELECTING_DATE

    async def handle_date_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обрабатывает выбор даты и сохраняет ДЗ."""
        query = update.callback_query
        await query.answer()
        context.user_data['selected_date'] = query.data.split(':')[1]
        
        user_id = str(update.effective_user.id)
        settings = await self.user_service.get_user_settings(user_id)
        
        # Если пользователь хочет выбирать время для каждого ДЗ отдельно
        if settings.get("ask_for_notification_time"):
            await query.edit_message_text(
                "Выберите время для ежедневного напоминания:",
                reply_markup=KeyboardFactory.get_time_selection_keyboard(callback_prefix="select_hw_time", show_skip=True)
            )
            return self.SELECTING_TIME
        else:
            # Используем настройку по умолчанию из настроек пользователя
            context.user_data['notification_time'] = settings.get("default_notification_time", "09:00")
            return await self._save_homework_and_finish(update, context)

    async def handle_time_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обрабатывает выбор времени напоминания и сохраняет ДЗ."""
        query = update.callback_query
        await query.answer()
        time_str = query.data.split(':')[1]
        
        if time_str != 'skip':
            context.user_data['notification_time'] = time_str
        else:
            # Если пользователь пропустил выбор, используем настройку по умолчанию
            user_id = str(update.effective_user.id)
            settings = await self.user_service.get_user_settings(user_id)
            context.user_data['notification_time'] = settings.get("default_notification_time", "09:00")
            
        return await self._save_homework_and_finish(update, context)

    # --- Управление существующими ДЗ ---
    async def prompt_for_homework_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Запрашивает у пользователя номер ДЗ для выполнения действия."""
        query = update.callback_query
        await query.answer()

        _, action, week_offset_str = query.data.split(':')
        week_offset = int(week_offset_str)
        user_id = str(update.effective_user.id)
        
        all_homework = await self.homework_service.get_homework_for_week(user_id, week_offset)
        active_homework = [hw for hw in all_homework if hw.get('status') != 'done']

        if not active_homework:
            await query.answer("На этой неделе нет активных заданий.", show_alert=True)
            return ConversationHandler.END

        action_text_map = {"mark_done": "выполнить", "delete_hw": "удалить", "edit_hw": "изменить"}
        prompt_text = f"Какое задание вы хотите {action_text_map.get(action, 'обработать')}?"

        await query.edit_message_text(
            text=query.message.text + f"\n\n{prompt_text}",
            reply_markup=KeyboardFactory.get_homework_selection_keyboard(active_homework, action, week_offset),
            parse_mode=ParseMode.HTML
        )
        return self.SELECTING_HOMEWORK_FOR_ACTION

    async def handle_homework_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Выполняет действие над выбранным ДЗ."""
        query = update.callback_query
        await query.answer()
        _, action, week_offset_str, hw_id = query.data.split(':')
        week_offset = int(week_offset_str)
        user_id = str(update.effective_user.id)

        logger.info(f"ACTION: {action}, HW_ID: {hw_id}, WEEK: {week_offset}") # Временное логирование

        if action == 'mark_done':
            await self.homework_service.mark_homework_as_done(user_id, hw_id)
            await query.answer("Задание отмечено как выполненное.")
        elif action == 'delete_hw':
            await self.homework_service.delete_homework(user_id, hw_id)
            await query.answer("Задание удалено.")
        elif action == 'edit_hw':
            context.user_data['edit_hw_id'] = hw_id
            context.user_data['edit_hw_week_offset'] = week_offset
            await query.edit_message_text("Пожалуйста, отправьте новый текст для этого задания.")
            return self.EDITING_HOMEWORK_TEXT
        
        await self._redisplay_main_view(update, context, week_offset)
        return ConversationHandler.END

    async def receive_new_homework_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Получает новый текст для ДЗ и обновляет его."""
        new_text = update.message.text.strip()
        if not new_text:
            await update.message.reply_text("Текст не может быть пустым.")
            return self.EDITING_HOMEWORK_TEXT
            
        hw_id = context.user_data.pop('edit_hw_id')
        week_offset = context.user_data.pop('edit_hw_week_offset')
        user_id = str(update.effective_user.id)
        
        success = await self.homework_service.update_homework_text(user_id, hw_id, new_text)
        if success:
            await update.message.reply_text("✅ Задание успешно обновлено.")
        else:
            await update.message.reply_text("❌ Не удалось найти задание для обновления.")

        await self._redisplay_main_view(update, context, week_offset)
        return ConversationHandler.END

    # --- Вспомогательные методы и отмена ---
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Отменяет текущий диалог."""
        query = update.callback_query
        if query:
            await query.answer()
            await query.edit_message_text("Действие отменено.")
        context.user_data.clear()
        return ConversationHandler.END

    async def back_to_week_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Возвращает к выбору недели."""
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "Выберите неделю:",
            reply_markup=KeyboardFactory.get_week_selection_keyboard()
        )
        return self.SELECTING_DATE

    async def _save_homework_and_finish(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Приватный метод для сохранения ДЗ и завершения диалога."""
        user_id = str(update.effective_user.id)
        hw_data = {
            "subject_key": context.user_data['subject_key'],
            "deadline_date": context.user_data['selected_date'],
            "text": context.user_data.get('homework_text'),
            "notification_time": context.user_data.get('notification_time')
        }
        await self.homework_service.add_homework(user_id, hw_data)
        
        if update.callback_query:
            await update.callback_query.answer("✅ Домашнее задание сохранено!", show_alert=True)
        
        context.user_data.clear()
        await self._redisplay_main_view(update, context, week_offset=0)
        return ConversationHandler.END

    async def _redisplay_main_view(self, update: Update, context: ContextTypes.DEFAULT_TYPE, week_offset: int):
        """Обновляет основное представление списка ДЗ."""
        user_id = str(update.effective_user.id)
        subjects = await self.subject_service.get_subjects(user_id)
        weekly_homework = await self.homework_service.get_homework_for_week(user_id, week_offset)
        
        response_text = text.format_homework_list(weekly_homework, subjects)
        
        active_homework = [hw for hw in weekly_homework if hw.get('status') != 'done']
        keyboard = KeyboardFactory.get_homework_management_keyboard(active_homework, week_offset)

        message_content = {
            "text": response_text,
            "reply_markup": keyboard,
            "parse_mode": ParseMode.HTML
        }
        
        if update.callback_query:
            await update.callback_query.edit_message_text(**message_content)
        else: # Случай после редактирования текста
            await context.bot.send_message(chat_id=update.effective_chat.id, **message_content)
