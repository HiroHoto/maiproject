from datetime import date, timedelta, datetime
import pytz

def get_week_dates(offset=0):
    """Returns the start and end dates of a week with a given offset from the current week."""
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    
    start_date = start_of_week + timedelta(weeks=offset)
    end_date = start_date + timedelta(days=6)
    
    return start_date, end_date

def format_russian_date(d: date) -> str:
    """Formats a date into a Russian string representation (e.g., 'Понедельник, 01.01')."""
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    return f"{days[d.weekday()]}, {d.strftime('%d.%m')}"

def get_moscow_time() -> datetime:
    """Returns the current time in the Moscow timezone."""
    return datetime.now(pytz.timezone('Europe/Moscow'))