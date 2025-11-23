from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from app.handlers.base_handler import BaseHandler
from app.ui.keyboards import KeyboardFactory
import app.ui.text as text
from app.config import ADMIN_COMMAND, ADMIN_ID

class CommandHandler(BaseHandler):
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles the /start command."""
        user_id = str(update.effective_user.id)
        await self.user_service.get_or_create_user(user_id)
        
        # This handler will now be responsible for showing the initial homework view.
        await self.show_homework_view(update, context, week_offset=0)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles the /help command."""
        await update.message.reply_text(text.HELP_MESSAGE, parse_mode=ParseMode.HTML)

    async def admin_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles admin statistics command."""
        user_id = str(update.effective_user.id)
        
        # Check if user is admin
        if ADMIN_ID and user_id != ADMIN_ID:
            await update.message.reply_text("❌ У вас нет прав доступа к этой команде.")
            return

        # Get statistics
        total_users = await self.user_service.get_total_users_count()
        total_homework = await self.homework_service.get_total_homework_count()

        # Format statistics message
        stats_message = (
            "📊 <b>Статистика бота</b>\n\n"
            f"👥 <b>Всего пользователей:</b> {total_users}\n"
            f"📚 <b>Всего домашних заданий:</b> {total_homework}\n\n"
            f"<i>Обновлено: {update.message.date.strftime('%d.%m.%Y %H:%M')}</i>"
        )

        await update.message.reply_text(stats_message, parse_mode=ParseMode.HTML)

    async def show_homework_view(self, update: Update, context: ContextTypes.DEFAULT_TYPE, week_offset: int):
        """Displays the homework for a given week."""
        query = update.callback_query
        user_id = str(update.effective_user.id)

        subjects = await self.subject_service.get_subjects(user_id)
        
        weekly_homework = await self.homework_service.get_homework_for_week(user_id, week_offset)
        
        response_text = text.format_homework_list(weekly_homework, subjects)
        
        keyboard = KeyboardFactory.get_homework_management_keyboard(weekly_homework, week_offset)

        message_content = {
            "text": response_text,
            "reply_markup": keyboard,
            "parse_mode": ParseMode.HTML
        }

        if query:
            await query.answer()
            await query.edit_message_text(**message_content)
        elif update.message:
            await update.message.reply_text(**message_content)

    async def handle_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles week navigation buttons."""
        query = update.callback_query
        _, offset_str = query.data.split(':')
        await self.show_homework_view(update, context, week_offset=int(offset_str))

    async def back_to_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Returns the user to the main homework view."""
        await self.show_homework_view(update, context, week_offset=0)
