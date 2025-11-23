from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from app.handlers.base_handler import BaseHandler
from app.ui.keyboards import KeyboardFactory

class SettingsHandler(BaseHandler):
    # Состояния для диалога управления предметами и временем
    CREATING_SUBJECT, EDITING_REMINDER_TIME = range(2)

    # --- Главное меню настроек ---
    async def show_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отображает меню настроек."""
        query = update.callback_query
        await query.answer()
        
        user_id = str(update.effective_user.id)
        settings = await self.user_service.get_user_settings(user_id)
        
        await query.edit_message_text(
            text="⚙️ Настройки",
            reply_markup=KeyboardFactory.get_settings_keyboard(settings)
        )

    async def toggle_setting(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Переключает булевы настройки."""
        query = update.callback_query
        await query.answer()
        
        _, setting_name = query.data.split(':')
        user_id = str(update.effective_user.id)
        
        await self.user_service.toggle_user_setting(user_id, setting_name)
        
        # Обновляем меню
        settings = await self.user_service.get_user_settings(user_id)
        await query.edit_message_text(
            text="⚙️ Настройки",
            reply_markup=KeyboardFactory.get_settings_keyboard(settings)
        )

    # --- Управление предметами ---
    async def show_subjects_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отображает меню управления предметами."""
        query = update.callback_query
        await query.answer()
        
        user_id = str(update.effective_user.id)
        subjects = await self.subject_service.get_subjects(user_id)
        
        await query.edit_message_text(
            text="Мои предметы:",
            reply_markup=KeyboardFactory.get_subjects_management_keyboard(subjects)
        )

    async def add_subject_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Начинает диалог добавления нового предмета."""
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("Введите название нового предмета:")
        return self.CREATING_SUBJECT

    async def add_subject_receive_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обрабатывает введенное название предмета и сохраняет его."""
        user_id = str(update.effective_user.id)
        subject_name = update.message.text.strip()
        
        if not subject_name:
            await update.message.reply_text("Название не может быть пустым. Попробуйте снова.")
            return self.CREATING_SUBJECT
            
        await self.subject_service.add_subject(user_id, subject_name)
        
        # Показываем обновленный список
        subjects = await self.subject_service.get_subjects(user_id)
        await update.message.reply_text(
            text=f"Предмет '{subject_name}' добавлен!\n\nМои предметы:",
            reply_markup=KeyboardFactory.get_subjects_management_keyboard(subjects)
        )
        return ConversationHandler.END

    async def delete_subject(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Удаляет предмет."""
        query = update.callback_query
        await query.answer()
        
        subject_key = query.data.split(':')[1]
        user_id = str(update.effective_user.id)
        
        await self.subject_service.delete_subject(user_id, subject_key)
        
        # Показываем обновленный список
        subjects = await self.subject_service.get_subjects(user_id)
        await query.edit_message_text(
            text="Предмет удален.\n\nМои предметы:",
            reply_markup=KeyboardFactory.get_subjects_management_keyboard(subjects)
        )

    # --- Редактирование времени напоминания ---
    async def edit_reminder_time_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Начинает диалог изменения времени напоминания по умолчанию."""
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "Выберите время для ежедневных напоминаний по умолчанию:",
            reply_markup=KeyboardFactory.get_time_selection_keyboard(callback_prefix="set_default_time")
        )
        return self.EDITING_REMINDER_TIME

    async def edit_reminder_time_set(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Сохраняет выбранное время напоминания по умолчанию."""
        query = update.callback_query
        await query.answer()
        
        time_str = query.data.split(':')[1]
        user_id = str(update.effective_user.id)
        
        await self.user_service.update_user_setting(user_id, "default_notification_time", time_str)
        
        # Возвращаемся в меню настроек
        settings = await self.user_service.get_user_settings(user_id)
        await query.edit_message_text(
            text=f"Время напоминаний по умолчанию установлено на {time_str}.",
            reply_markup=KeyboardFactory.get_settings_keyboard(settings)
        )
        return ConversationHandler.END

    async def cancel_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Отменяет любой диалог в настройках."""
        query = update.callback_query
        await query.answer()
        
        user_id = str(update.effective_user.id)
        settings = await self.user_service.get_user_settings(user_id)
        
        await query.edit_message_text(
            text="Действие отменено.",
            reply_markup=KeyboardFactory.get_settings_keyboard(settings)
        )
        return ConversationHandler.END
