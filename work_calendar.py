import json
import os
from datetime import datetime, timedelta

class WorkCalendar:
    def __init__(self, calendar_file="holidays.json"):
        self.calendar_file = calendar_file
        self.holidays = {}
        self.load_holidays()

    def load_holidays(self):
        """Загрузка праздников из файла. Если файла нет - создаем с базовыми данными"""
        if os.path.exists(self.calendar_file):
            with open(self.calendar_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Преобразуем списки в множества для быстрого поиска
                self.holidays = {
                    int(year): set(tuple(d) for d in dates)
                    for year, dates in data.items()
                }
        else:
            # Создаем файл с базовыми праздниками
            self.create_default_holidays()
            self.load_holidays()

    def create_default_holidays(self):
        """Создание файла с праздниками по умолчанию (2024-2027)"""
        default_holidays = {
            "2024": [
                [2024, 1, 1], [2024, 1, 2], [2024, 1, 3], [2024, 1, 4],
                [2024, 1, 5], [2024, 1, 6], [2024, 1, 7], [2024, 1, 8],
                [2024, 2, 23], [2024, 2, 24], [2024, 2, 25],
                [2024, 3, 8], [2024, 3, 9], [2024, 3, 10],
                [2024, 5, 1], [2024, 5, 9], [2024, 5, 10], [2024, 5, 11],
                [2024, 6, 12],
                [2024, 11, 4],
                [2024, 12, 29], [2024, 12, 30], [2024, 12, 31]
            ],
            "2025": [
                [2025, 1, 1], [2025, 1, 2], [2025, 1, 3], [2025, 1, 4],
                [2025, 1, 5], [2025, 1, 6], [2025, 1, 7], [2025, 1, 8],
                [2025, 2, 23], [2025, 2, 24],
                [2025, 3, 8], [2025, 3, 9], [2025, 3, 10],
                [2025, 5, 1], [2025, 5, 9], [2025, 5, 10], [2025, 5, 11],
                [2025, 6, 12], [2025, 6, 13], [2025, 6, 14],
                [2025, 11, 4],
                [2025, 12, 31]
            ],
            "2026": [
                [2026, 1, 1], [2026, 1, 2], [2026, 1, 3], [2026, 1, 4],
                [2026, 1, 5], [2026, 1, 6], [2026, 1, 7], [2026, 1, 8],
                [2026, 1, 9], [2026, 1, 10], [2026, 1, 11],
                [2026, 2, 23], [2026, 2, 24],
                [2026, 3, 8], [2026, 3, 9],
                [2026, 5, 1], [2026, 5, 9], [2026, 5, 10], [2026, 5, 11],
                [2026, 6, 12], [2026, 6, 13], [2026, 6, 14],
                [2026, 11, 4],
                [2026, 12, 31]
            ],
            "2027": [
                [2027, 1, 1], [2027, 1, 2], [2027, 1, 3], [2027, 1, 4],
                [2027, 1, 5], [2027, 1, 6], [2027, 1, 7], [2027, 1, 8],
                [2027, 1, 9], [2027, 1, 10],
                [2027, 2, 23],
                [2027, 3, 8],
                [2027, 5, 1], [2027, 5, 9], [2027, 5, 10],
                [2027, 6, 12], [2027, 6, 13], [2027, 6, 14],
                [2027, 11, 4],
                [2027, 12, 31]
            ]
        }
        
        with open(self.calendar_file, 'w', encoding='utf-8') as f:
            json.dump(default_holidays, f, ensure_ascii=False, indent=2)

    def add_holiday(self, year, month, day):
        """Добавление нового праздничного дня"""
        # Загружаем текущий файл
        with open(self.calendar_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        year_str = str(year)
        if year_str not in data:
            data[year_str] = []
        
        new_holiday = [year, month, day]
        if new_holiday not in data[year_str]:
            data[year_str].append(new_holiday)
            data[year_str].sort()
            
            with open(self.calendar_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Обновляем в памяти
            self.load_holidays()

    def is_weekend(self, year, month, day):
        """Проверка - выходной ли день (суббота или воскресенье)"""
        try:
            return datetime(year, month, day).weekday() >= 5
        except ValueError:
            return False

    def is_holiday(self, year, month, day):
        """Проверка - праздничный или выходной день"""
        holidays = self.holidays.get(year, set())
        return (year, month, day) in holidays or self.is_weekend(year, month, day)

    def get_days_in_month(self, year, month):
        """Количество календарных дней в месяце"""
        if month == 12:
            return 31
        next_month = datetime(year, month + 1, 1)
        return (next_month - timedelta(days=1)).day

    def get_workdays_in_month(self, year, month):
        """Количество рабочих дней в месяце"""
        days_in_month = self.get_days_in_month(year, month)
        workdays = 0
        for day in range(1, days_in_month + 1):
            if not self.is_holiday(year, month, day):
                workdays += 1
        return workdays

    def get_workdays_between(self, year, month, start_day, end_day):
        """Количество рабочих дней между двумя датами включительно"""
        workdays = 0
        for day in range(start_day, end_day + 1):
            if not self.is_holiday(year, month, day):
                workdays += 1
        return workdays

    def get_month_info(self, year, month):
        """Полная информация о месяце"""
        month_names = [
            "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
        ]
        
        return {
            'name': month_names[month - 1],
            'total_days': self.get_days_in_month(year, month),
            'workdays': self.get_workdays_in_month(year, month),
            'weekends': self.get_days_in_month(year, month) - self.get_workdays_in_month(year, month)
        }