import logging

class PayrollCalculator:
    """Калькулятор для расчета зарплаты и аванса"""
    
    def __init__(self, calendar):
        self.calendar = calendar
        self.NDFL_RATE = 0.13
        self.ADVANCE_PERCENT = 0.5
        
        logging.info("Калькулятор зарплаты инициализирован")

    def calculate_advance(self, employee_data, year, month, worked_days=None):
        """Расчет аванса за первую половину месяца"""
        salary = employee_data['salary']
        hire_date = employee_data['hire_date']
        fire_date = employee_data.get('fire_date')
        
        hire_day = int(hire_date.split('-')[2])
        start_day = hire_day if hire_date.startswith(f"{year}-{month:02d}") else 1
        
        if fire_date and fire_date.startswith(f"{year}-{month:02d}"):
            fire_day = int(fire_date.split('-')[2])
            end_day = min(fire_day, 15)
        else:
            end_day = 15
        
        if start_day > 15:
            return {
                'worked_days': 0,
                'total_workdays': 0,
                'amount_before_tax': 0,
                'ndfl': 0,
                'to_pay': 0,
                'note': 'Принят после 15 числа - аванс не положен'
            }
        
        total_workdays = self.calendar.get_workdays_in_month(year, month)
        
        # Если передан ручной ввод дней - используем его
        if worked_days is not None:
            max_advance_days = self.calendar.get_workdays_between(
                year, month, 1, min(15, self.calendar.get_days_in_month(year, month))
            )
            worked_until_15 = min(worked_days, max_advance_days)
        else:
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

    def calculate_salary(self, employee_data, year, month, worked_days=None):
        """Расчет полной зарплаты за месяц с раздельным НДФЛ"""
        salary = employee_data['salary']
        hire_date = employee_data['hire_date']
        fire_date = employee_data.get('fire_date')
        
        total_workdays = self.calendar.get_workdays_in_month(year, month)
        
        # Определяем фактически отработанные дни
        if worked_days is not None:
            actual_worked = worked_days
        else:
            hire_day = int(hire_date.split('-')[2])
            start_day = hire_day if hire_date.startswith(f"{year}-{month:02d}") else 1
            
            if fire_date and fire_date.startswith(f"{year}-{month:02d}"):
                fire_day = int(fire_date.split('-')[2])
                end_day = fire_day
            else:
                end_day = self.calendar.get_days_in_month(year, month)
            
            actual_worked = self.calendar.get_workdays_between(year, month, start_day, end_day)
        
        if total_workdays == 0:
            return {
                'worked_days': 0,
                'total_workdays': total_workdays,
                'full_salary': 0,
                'ndfl_full': 0,
                'ndfl_advance': 0,
                'ndfl_second_half': 0,
                'advance_paid': 0,
                'to_pay': 0,
                'note': 'Ошибка: нет рабочих дней в месяце'
            }
        
        # Расчет аванса (для вычета)
        advance_result = self.calculate_advance(employee_data, year, month, worked_days)
        advance_to_pay = advance_result['to_pay']
        advance_ndfl = advance_result['ndfl']
        
        # Полная зарплата
        full_salary = round(salary * actual_worked / total_workdays)
        ndfl_full = round(full_salary * self.NDFL_RATE)
        
        # НДФЛ со второй половины
        ndfl_second_half = ndfl_full - advance_ndfl
        if ndfl_second_half < 0:
            ndfl_second_half = 0
        
        # К выплате
        to_pay = full_salary - ndfl_full - advance_to_pay
        
        return {
            'worked_days': actual_worked,
            'total_workdays': total_workdays,
            'full_salary': full_salary,
            'ndfl_full': ndfl_full,
            'ndfl_advance': advance_ndfl,
            'ndfl_second_half': ndfl_second_half,
            'advance_paid': advance_to_pay,
            'to_pay': to_pay,
            'note': f'{full_salary:,} - {ndfl_full:,} (НДФЛ) - {advance_to_pay:,} (аванс) = {to_pay:,}'
        }

    def calculate_single(self, employee_data, year, month, worked_days=None, payment_type='salary'):
        """Расчет для одного сотрудника"""
        emp_data = {
            'id': employee_data[0],
            'full_name': employee_data[1],
            'salary': employee_data[2],
            'hire_date': employee_data[3],
            'fire_date': employee_data[4]
        }
        
        if payment_type == 'advance':
            return self.calculate_advance(emp_data, year, month, worked_days)
        else:
            return self.calculate_salary(emp_data, year, month, worked_days)

    def calculate_all(self, employees, year, month, payment_type='salary', worked_days_dict=None):
        """Расчет для всех сотрудников"""
        results = []
        total_to_pay = 0
        total_ndfl = 0
        total_ndfl_advance = 0
        total_ndfl_second_half = 0
        
        for emp in employees:
            emp_id, full_name, salary, hire_date, fire_date = emp
            
            emp_data = {
                'id': emp_id,
                'full_name': full_name,
                'salary': salary,
                'hire_date': hire_date,
                'fire_date': fire_date
            }
            
            worked_days = None
            if worked_days_dict and emp_id in worked_days_dict:
                worked_days = worked_days_dict[emp_id]
            
            if payment_type == 'advance':
                calc = self.calculate_advance(emp_data, year, month, worked_days)
                results.append({
                    'id': emp_id,
                    'name': full_name,
                    'calculation': calc,
                    'type': 'advance'
                })
                total_to_pay += calc['to_pay']
                total_ndfl += calc['ndfl']
            else:
                calc = self.calculate_salary(emp_data, year, month, worked_days)
                results.append({
                    'id': emp_id,
                    'name': full_name,
                    'calculation': calc,
                    'type': 'salary'
                })
                total_to_pay += calc['to_pay']
                total_ndfl += calc['ndfl_full']
                total_ndfl_advance += calc.get('ndfl_advance', 0)
                total_ndfl_second_half += calc.get('ndfl_second_half', 0)
        
        result = {
            'results': results,
            'total_to_pay': total_to_pay,
            'total_ndfl': total_ndfl
        }
        
        if payment_type == 'salary':
            result['total_ndfl_advance'] = total_ndfl_advance
            result['total_ndfl_second_half'] = total_ndfl_second_half
        
        return result
