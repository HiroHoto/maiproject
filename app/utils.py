from datetime import date, timedelta, datetime
import pytz

def get_week_dates(offset=0):
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    
    start_date = start_of_week + timedelta(weeks=offset)
    end_date = start_date + timedelta(days=6)
    
    return start_date, end_date

def format_russian_date(d: date) -> str:
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    return f"{days[d.weekday()]}, {d.strftime('%d.%m')}"

def get_moscow_time() -> datetime:

    return datetime.now(pytz.timezone('Europe/Moscow'))