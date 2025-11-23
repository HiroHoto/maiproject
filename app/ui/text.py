from datetime import datetime
from typing import List, Dict, Any

WELCOME_MESSAGE = "Добро пожаловать! Я помогу тебе управлять домашними заданиями."

HELP_MESSAGE = (
    "📚 <b>Бот для управления дз с напоминалкой.</b>\n\n"
    "🎯 <b>Как использовать:</b>\n"
    "• Чтобы добавить домашку - просто отправь мне текст задания\n"
    "• Я предложу выбрать предмет и срок выполнения\n\n"
    "⚙️ <b>Основные функции:</b>\n"
    "• Просмотр заданий по неделям\n"
    "• Отметка выполненных заданий\n"
    "• Редактирование и удаление заданий\n"
    "• Управление предметами в настройках\n"
    "• Настройка напоминаний\n\n"
    "🔧 <b>Команды:</b>\n"
    "/start - запустить бота\n"
    "/help - показать эту справку"
)

NO_HOMEWORK_MESSAGE = "На этой неделе заданий нет."

def format_russian_date(d: datetime.date) -> str:
    """Formats date into a Russian string with weekday."""
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    return f"{days[d.weekday()]}, {d.strftime('%d.%m')}"

def format_homework_list(weekly_homework: List[Dict[str, Any]], subjects: List[Dict[str, Any]]) -> str:
    if not weekly_homework:
        return NO_HOMEWORK_MESSAGE

    subjects_map = {s['id']: s for s in subjects}
    homework_by_day = {}
    for hw in weekly_homework:
        day = format_russian_date(datetime.fromisoformat(hw['deadline_date']).date())
        if day not in homework_by_day:
            homework_by_day[day] = []
        homework_by_day[day].append(hw)

    response_text = ""
    for day, hws in sorted(homework_by_day.items()):
        response_text += f"\n<b>{day.capitalize()}:</b>\n"
        
        active_hw_counter = 1
        for hw in sorted(hws, key=lambda x: x.get('subject_key', '')):
            subject = subjects_map.get(hw.get('subject_key'), {})
            subject_name = subject.get('name', "Неизвестно")
            text = hw['text']
            
            if hw.get('status') == 'done':
                status_icon = "✅"
                response_text += f"{status_icon} <s>{subject_name}: {text}</s>\n"
            else:
                status_icon = "📌"
                response_text += f"<b>{active_hw_counter}.</b> {status_icon} {subject_name}: {text}\n"
                active_hw_counter += 1
    
    return response_text.strip()
