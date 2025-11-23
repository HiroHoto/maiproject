from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import date, timedelta
from typing import List, Dict, Any

class KeyboardFactory:
    @staticmethod
    def get_main_menu_keyboard(week_offset: int) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("◀️", callback_data=f"navigate_week:{week_offset-1}"),
                InlineKeyboardButton("🔄", callback_data=f"navigate_week:{week_offset}"),
                InlineKeyboardButton("▶️", callback_data=f"navigate_week:{week_offset+1}"),
            ],
            [InlineKeyboardButton("⚙️ Настройки", callback_data="show_settings")],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_subjects_keyboard(subjects: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(s['name'], callback_data=f"select_subject:{s['id']}")] for s in subjects
        ]
        keyboard.append([InlineKeyboardButton("➕ Новый предмет", callback_data="new_subject")])
        keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_week_selection_keyboard() -> InlineKeyboardMarkup:
        today = date.today()
        keyboard = []
        for i in range(-3, 4):
            start_day = today + timedelta(weeks=i)
            start_day -= timedelta(days=start_day.weekday())
            end_day = start_day + timedelta(days=6)
            week_label = f"{start_day.strftime('%d.%m')} - {end_day.strftime('%d.%m')}"
            callback_data = f"select_week:{start_day.isoformat()}"
            keyboard.append([InlineKeyboardButton(week_label, callback_data=callback_data)])
        keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_day_of_week_keyboard(week_start_date_str: str) -> InlineKeyboardMarkup:
        week_start_date = date.fromisoformat(week_start_date_str)
        days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        keyboard = []
        for i in range(7):
            current_date = week_start_date + timedelta(days=i)
            day_name = days[i]
            button_text = f"{day_name} ({current_date.day})"
            callback_data = f"select_date:{current_date.isoformat()}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_week_selection"), InlineKeyboardButton("❌ Отмена", callback_data="cancel")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_homework_management_keyboard(active_homework: List[Dict[str, Any]], week_offset: int) -> InlineKeyboardMarkup:
        keyboard = []
        if active_homework:
            action_row = [
                InlineKeyboardButton("✅ Выполнить", callback_data=f"start:mark_done:{week_offset}"),
                InlineKeyboardButton("✏️ Изменить", callback_data=f"start:edit_hw:{week_offset}"),
                InlineKeyboardButton("🗑️ Удалить", callback_data=f"start:delete_hw:{week_offset}")
            ]
            keyboard.append(action_row)
        
        nav_row = [
            InlineKeyboardButton("◀️", callback_data=f"navigate_week:{week_offset-1}"),
            InlineKeyboardButton("🔄", callback_data=f"navigate_week:{week_offset}"),
            InlineKeyboardButton("▶️", callback_data=f"navigate_week:{week_offset+1}"),
        ]
        keyboard.append(nav_row)
        keyboard.append([InlineKeyboardButton("⚙️ Настройки", callback_data="show_settings")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_settings_keyboard(user_settings: Dict[str, Any]) -> InlineKeyboardMarkup:
        reminders_status = "Вкл" if user_settings.get('reminders_enabled', False) else "Выкл"
        ask_time_status = "Вкл" if user_settings.get('ask_for_notification_time', False) else "Выкл"
        default_time = user_settings.get('default_notification_time', '09:00')
        keyboard = [
            [InlineKeyboardButton(f"Напоминания о ДЗ: {reminders_status}", callback_data="toggle_setting:reminders_enabled")],
            [InlineKeyboardButton(f"Время напоминаний: {default_time}", callback_data="edit_reminder_time")],
            [InlineKeyboardButton(f"Спрашивать время для ДЗ: {ask_time_status}", callback_data="toggle_setting:ask_for_notification_time")],
            [InlineKeyboardButton("Мои предметы", callback_data="manage_subjects")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_subjects_management_keyboard(subjects: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
        keyboard = []
        for subject in subjects:
            row = [
                InlineKeyboardButton(subject['name'], callback_data=f"subject_info:{subject['id']}"),
                InlineKeyboardButton("🗑️", callback_data=f"delete_subject:{subject['id']}")
            ]
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("➕ Добавить", callback_data="add_subject")])
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="show_settings")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_homework_selection_keyboard(active_homework: List[Dict[str, Any]], action: str, week_offset: int) -> InlineKeyboardMarkup:
        keyboard = []
        row = []
        for i, hw in enumerate(active_homework):
            hw_number = i + 1
            row.append(InlineKeyboardButton(str(hw_number), callback_data=f"hw_action:{action}:{week_offset}:{hw['id']}"))
            if len(row) == 5:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=f"navigate_week:{week_offset}")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_reminder_offset_keyboard(callback_prefix: str = "select_offset", show_skip: bool = False) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton("За день", callback_data=f"{callback_prefix}:1d"),
                InlineKeyboardButton("За час", callback_data=f"{callback_prefix}:1h")
            ],
            [InlineKeyboardButton("За 30 минут", callback_data=f"{callback_prefix}:30m")],
        ]
        if show_skip:
            keyboard.append([InlineKeyboardButton("Пропустить", callback_data=f"{callback_prefix}:skip")])
        keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_time_selection_keyboard(callback_prefix: str = "select_time", show_skip: bool = False) -> InlineKeyboardMarkup:
        """Создает клавиатуру для выбора времени дня с шагом 30 минут."""
        keyboard = []
        row = []
        
        # Создаем времена от 00:00 до 23:30 с шагом 30 минут
        for hour in range(24):
            for minute in [0, 30]:
                time_str = f"{hour:02d}:{minute:02d}"
                button = InlineKeyboardButton(time_str, callback_data=f"{callback_prefix}:{time_str}")
                row.append(button)
                
                # Размещаем по 4 кнопки в строке
                if len(row) == 4:
                    keyboard.append(row)
                    row = []
        
        # Добавляем оставшиеся кнопки
        if row:
            keyboard.append(row)
        
        if show_skip:
            keyboard.append([InlineKeyboardButton("Пропустить", callback_data=f"{callback_prefix}:skip")])
        
        keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_cancel_keyboard() -> InlineKeyboardMarkup:
        """Возвращает клавиатуру с единственной кнопкой 'Отмена'."""
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel")]]
        return InlineKeyboardMarkup(keyboard)
