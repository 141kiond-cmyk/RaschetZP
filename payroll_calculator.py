import logging

class PayrollCalculator:
    """Калькулятор для расчета зарплаты и аванса"""
    
    def __init__(self, calendar):
        self.calendar = calendar
        self.NDFL_RATE = 0.13  # Ставка НДФЛ (можно легко изменить)
        self.ADVANCE_PERCENT = 0.5  # Аванс - 50% от оклада (законодательно)
        
        logging.info("Калькулятор зарплаты инициализирован")

    def calculate_advance(self, employee_data, year, month):
        """
        Расчет аванса для сотрудника за первую половину месяца
        
        employee_data: словарь с данными сотрудника
        {
            'full_name': str,
            'salary': int,
            'hire_date': str (YYYY-MM-DD),
            'fire_date': str или None
        }
        """
        salary = employee_data['salary']
        hire_date = employee_data['hire_date']
        fire_date = employee_data.get('fire_date')
        
        # Определяем период работы
        hire_day = int(hire_date.split('-')[2])
        start_day = hire_day if hire_date.startswith(f"{year}-{month:02d}") else 1
        
        if fire_date and fire_date.startswith(f"{year}-{month:02d}"):
            fire_day = int(fire_date.split('-')[2])
            end_day = fire_day
        else:
            end_day = self.calendar.get_days_in_month(year, month)
        
        # Если сотрудник принят после 15 числа - аванс не положен
        if start_day > 15:
            return {
                'worked_days': 0,
                'total_workdays': 0,
                'amount_before_tax': 0,
                'ndfl': 0,
                'to_pay': 0,
                'note': 'Принят после 15 числа - аванс не положен'
            }
        
        # Рабочие дни в месяце
        total_workdays = self.calendar.get_workdays_in_month(year, month)
        
        # Сколько рабочих дней отработано до 15 числа
        worked_until_15 = self.calendar.get_workdays_between(
            year, month, start_day, min(15, end_day)
        )
        
        if total_workdays == 0 or worked_until_15 == 0:
            return {
                'worked_days': 0,
                'total_workdays': total_workdays,
                'amount_before_tax': 0,
                'ndfl': 0,
                'to_pay': 0,
                'note': 'Нет рабочих дней в периоде'
            }
        
        # Расчет суммы аванса
        amount_before_tax = round(salary * worked_until_15 / total_workdays)
        ndfl = round(amount_before_tax * self.NDFL_RATE)
        to_pay = amount_before_tax - ndfl
        
        return {
            'worked_days': worked_until_15,
            'total_workdays': total_workdays,
            'amount_before_tax': amount_before_tax,
            'ndfl': ndfl,
            'to_pay': to_pay,
            'note': f'Отработано {worked_until_15} из {total_workdays} рабочих дней'
        }

    def calculate_salary(self, employee_data, year, month):
        """
        Расчет полной зарплаты за месяц (за вычетом аванса)
        """
        # Сначала считаем аванс (для вычета)
        advance = self.calculate_advance(employee_data, year, month)
        
        salary = employee_data['salary']
        hire_date = employee_data['hire_date']
        fire_date = employee_data.get('fire_date')
        
        # Определяем период работы
        hire_day = int(hire_date.split('-')[2])
        start_day = hire_day if hire_date.startswith(f"{year}-{month:02d}") else 1
        
        if fire_date and fire_date.startswith(f"{year}-{month:02d}"):
            fire_day = int(fire_date.split('-')[2])
            end_day = fire_day
        else:
            end_day = self.calendar.get_days_in_month(year, month)
        
        total_workdays = self.calendar.get_workdays_in_month(year, month)
        worked_days = self.calendar.get_workdays_between(year, month, start_day, end_day)
        
        if total_workdays == 0:
            return {
                'worked_days': 0,
                'total_workdays': total_workdays,
                'full_salary': 0,
                'ndfl_full': 0,
                'advance_paid': 0,
                'to_pay': 0,
                'note': 'Ошибка: нет рабочих дней в месяце'
            }
        
        # Полная зарплата за месяц
        full_salary = round(salary * worked_days / total_workdays)
        ndfl_full = round(full_salary * self.NDFL_RATE)
        
        # Итоговая сумма к выплате (зарплата - НДФЛ - аванс)
        to_pay = full_salary - ndfl_full - advance['to_pay']
        
        return {
            'worked_days': worked_days,
            'total_workdays': total_workdays,
            'full_salary': full_salary,
            'ndfl_full': ndfl_full,
            'advance_paid': advance['to_pay'],
            'to_pay': to_pay,
            'note': f'{full_salary} - {ndfl_full} (НДФЛ) - {advance["to_pay"]} (аванс) = {to_pay}'
        }

    def calculate_all(self, employees, year, month, payment_type='salary'):
        """
        Расчет для всех сотрудников
        
        payment_type: 'advance' или 'salary'
        """
        results = []
        total_to_pay = 0
        total_ndfl = 0
        
        for emp in employees:
            emp_id, full_name, salary, hire_date, fire_date = emp
            
            emp_data = {
                'full_name': full_name,
                'salary': salary,
                'hire_date': hire_date,
                'fire_date': fire_date
            }
            
            if payment_type == 'advance':
                calc = self.calculate_advance(emp_data, year, month)
                results.append({
                    'name': full_name,
                    'calculation': calc,
                    'type': 'advance'
                })
                total_to_pay += calc['to_pay']
                total_ndfl += calc['ndfl']
            else:
                calc = self.calculate_salary(emp_data, year, month)
                results.append({
                    'name': full_name,
                    'calculation': calc,
                    'type': 'salary'
                })
                total_to_pay += calc['to_pay']
                total_ndfl += calc['ndfl_full']
        
        return {
            'results': results,
            'total_to_pay': total_to_pay,
            'total_ndfl': total_ndfl
        }