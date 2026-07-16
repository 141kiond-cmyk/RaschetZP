import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from payroll_calculator import PayrollCalculator
import logging

class CalculationsTab:
    def __init__(self, parent, db, calendar, app):
        self.parent = parent
        self.db = db
        self.calendar = calendar
        self.app = app
        self.clients = []
        self.calculator = PayrollCalculator(calendar)
        
        self.create_widgets()
        logging.info("Вкладка 'Расчеты' создана")

    def create_widgets(self):
        # Верхняя панель выбора
        top_frame = ttk.LabelFrame(self.parent, text="Параметры расчета", padding=10)
        top_frame.pack(fill='x', padx=5, pady=5)
        
        # Первая строка
        row1 = ttk.Frame(top_frame)
        row1.pack(fill='x', pady=2)
        
        ttk.Label(row1, text="🏢 Клиент:").pack(side='left', padx=5)
        self.calc_client_cb = ttk.Combobox(row1, state='readonly', width=30)
        self.calc_client_cb.pack(side='left', padx=5)
        
        ttk.Label(row1, text="📅 Месяц:").pack(side='left', padx=5)
        self.month_var = tk.StringVar()
        months = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                 "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
        self.month_cb = ttk.Combobox(row1, textvariable=self.month_var, 
                                     state='readonly', width=15, values=months)
        self.month_cb.current(datetime.now().month - 1)
        self.month_cb.pack(side='left', padx=5)
        
        ttk.Label(row1, text="📆 Год:").pack(side='left', padx=5)
        self.year_var = tk.StringVar()
        years = [str(y) for y in range(2024, 2031)]
        self.year_cb = ttk.Combobox(row1, textvariable=self.year_var, 
                                   state='readonly', width=8, values=years)
        self.year_cb.current(years.index(str(datetime.now().year)))
        self.year_cb.pack(side='left', padx=5)
        
        # Вторая строка - тип выплаты и кнопка
        row2 = ttk.Frame(top_frame)
        row2.pack(fill='x', pady=5)
        
        self.payment_type = tk.StringVar(value="salary")
        ttk.Radiobutton(row2, text="💵 Аванс (до 15 числа)", 
                       variable=self.payment_type, 
                       value="advance").pack(side='left', padx=10)
        ttk.Radiobutton(row2, text="💰 Зарплата (за месяц)", 
                       variable=self.payment_type, 
                       value="salary").pack(side='left', padx=10)
        
        ttk.Button(row2, text="🧮 Рассчитать", 
                  command=self.calculate_payroll).pack(side='right', padx=20)
        
        # Информация о месяце
        self.month_info_label = ttk.Label(top_frame, text="", foreground='blue')
        self.month_info_label.pack(pady=5)
        
        # Обновляем информацию при изменении месяца/года
        self.month_cb.bind('<<ComboboxSelected>>', self.update_month_info)
        self.year_cb.bind('<<ComboboxSelected>>', self.update_month_info)
        
        # Результаты расчета
        result_frame = ttk.LabelFrame(self.parent, text="Результаты расчета", padding=10)
        result_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, height=15, 
                                                     font=("Consolas", 10))
        self.result_text.pack(fill='both', expand=True)
        
        # Кнопки действий с результатами
        btn_frame = ttk.Frame(self.parent)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(btn_frame, text="📋 Копировать в буфер", 
                  command=self.copy_to_clipboard).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="📝 Отправить в сообщения", 
                  command=self.send_to_messages).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="📊 Экспорт в Excel", 
                  command=self.export_to_excel).pack(side='left', padx=5)

    def refresh_clients_list(self, clients):
        """Обновление списка клиентов"""
        self.clients = clients
        client_names = [f"{c[1]} (ИНН: {c[2]})" for c in clients]
        self.calc_client_cb['values'] = client_names
        if client_names:
            self.calc_client_cb.current(0)
            self.update_month_info()

    def update_month_info(self, event=None):
        """Обновление информации о выбранном месяце"""
        try:
            month_name = self.month_var.get()
            year = int(self.year_var.get())
            months = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                     "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
            
            if month_name in months:
                month = months.index(month_name) + 1
                info = self.calendar.get_month_info(year, month)
                self.month_info_label.config(
                    text=f"📊 {info['name']} {year}: {info['workdays']} рабочих дней, "
                         f"{info['weekends']} выходных, {info['total_days']} всего"
                )
        except:
            pass

    def calculate_payroll(self):
        """Расчет зарплаты"""
        if not self.calc_client_cb.get():
            messagebox.showwarning("⚠️ Внимание", "Выберите клиента!")
            return
        
        # Находим ID клиента
        selected = self.calc_client_cb.get()
        client_id = None
        for c in self.clients:
            if f"{c[1]} (ИНН: {c[2]})" == selected:
                client_id = c[0]
                break
        
        if not client_id:
            messagebox.showerror("❌ Ошибка", "Клиент не найден!")
            return
        
        # Получаем месяц и год
        months = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                 "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
        
        month_name = self.month_var.get()
        if month_name in months:
            month = months.index(month_name) + 1
        else:
            messagebox.showerror("❌ Ошибка", "Выберите месяц!")
            return
        
        try:
            year = int(self.year_var.get())
        except ValueError:
            messagebox.showerror("❌ Ошибка", "Выберите год!")
            return
        
        # Получаем сотрудников
        employees = self.db.get_active_employees_for_month(client_id, year, month)
        
        if not employees:
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, "Нет сотрудников для расчета за этот месяц.")
            return
        
        # Выполняем расчет
        payment_type = self.payment_type.get()
        result = self.calculator.calculate_all(employees, year, month, payment_type)
        
        # Форматируем вывод
        output = []
        month_info = self.calendar.get_month_info(year, month)
        
        if payment_type == "advance":
            output.append(f"{'='*60}")
            output.append(f"АВАНС за {month_name} {year}")
            output.append(f"Рабочих дней в месяце: {month_info['workdays']}")
            output.append(f"{'='*60}")
            output.append("")
            
            for emp_result in result['results']:
                calc = emp_result['calculation']
                output.append(f"👤 {emp_result['name']}:")
                output.append(f"   Отработано дней до 15 числа: {calc['worked_days']}")
                output.append(f"   Начислено: {calc['amount_before_tax']:,} руб.")
                output.append(f"   НДФЛ: {calc['ndfl']:,} руб.")
                output.append(f"   К выплате: {calc['to_pay']:,} руб.")
                if calc.get('note'):
                    output.append(f"   ℹ️ {calc['note']}")
                output.append("")
        else:
            output.append(f"{'='*60}")
            output.append(f"ЗАРПЛАТА за {month_name} {year} (за вычетом аванса)")
            output.append(f"Рабочих дней в месяце: {month_info['workdays']}")
            output.append(f"{'='*60}")
            output.append("")
            
            for emp_result in result['results']:
                calc = emp_result['calculation']
                output.append(f"👤 {emp_result['name']}:")
                output.append(f"   Отработано дней: {calc['worked_days']} из {calc['total_workdays']}")
                output.append(f"   Начислено за месяц: {calc['full_salary']:,} руб.")
                output.append(f"   НДФЛ за месяц: {calc['ndfl_full']:,} руб.")
                output.append(f"   Аванс (удержан): {calc['advance_paid']:,} руб.")
                output.append(f"   К выплате: {calc['to_pay']:,} руб.")
                if calc.get('note'):
                    output.append(f"   ℹ️ {calc['note']}")
                output.append("")
        
        output.append(f"{'='*60}")
        output.append(f"💰 ИТОГО к выплате: {result['total_to_pay']:,} руб.")
        output.append(f"💸 НДФЛ (удержан): {result['total_ndfl']:,} руб.")
        output.append(f"{'='*60}")
        
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(1.0, "\n".join(output))
        
        logging.info(f"Выполнен расчет {payment_type} для клиента ID={client_id} за {month}.{year}")

    def copy_to_clipboard(self):
        """Копирование результата в буфер обмена"""
        text = self.result_text.get(1.0, tk.END).strip()
        if text:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(text)
            messagebox.showinfo("✅ Успех", "Результат скопирован в буфер обмена!")
        else:
            messagebox.showwarning("⚠️ Внимание", "Нет данных для копирования!")

    def send_to_messages(self):
        """Отправка результата на вкладку Сообщения"""
        text = self.result_text.get(1.0, tk.END).strip()
        if text:
            self.app.messages_tab.add_message(text)
            self.app.notebook.select(3)  # Переключаемся на вкладку Сообщения
            messagebox.showinfo("✅ Успех", "Результат отправлен на вкладку Сообщения!")
        else:
            messagebox.showwarning("⚠️ Внимание", "Нет данных для отправки!")

    def export_to_excel(self):
        """Экспорт результатов в Excel"""
        try:
            import openpyxl
            from datetime import datetime
            
            text = self.result_text.get(1.0, tk.END).strip()
            if not text:
                messagebox.showwarning("⚠️ Внимание", "Нет данных для экспорта!")
                return
            
            # Создаем Excel файл
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Расчет зарплаты"
            
            # Записываем данные построчно
            for i, line in enumerate(text.split('\n'), 1):
                ws.cell(row=i, column=1, value=line)
            
            # Сохраняем файл
            filename = f"Расчет_зарплаты_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            wb.save(filename)
            
            messagebox.showinfo("✅ Успех", f"Данные экспортированы в файл:\n{filename}")
            logging.info(f"Данные экспортированы в {filename}")
            
        except ImportError:
            messagebox.showerror("❌ Ошибка", 
                               "Для экспорта в Excel необходимо установить библиотеку openpyxl\n"
                               "Выполните команду: pip install openpyxl")