import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import logging

class EmployeesTab:
    def __init__(self, parent, db, app):
        self.parent = parent
        self.db = db
        self.app = app
        self.current_client_id = None
        self.clients = []
        
        self.create_widgets()
        logging.info("Вкладка 'Сотрудники' создана")

    def create_widgets(self):
        # Верхняя панель выбора клиента
        top_frame = ttk.Frame(self.parent)
        top_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(top_frame, text="🏢 Клиент:").pack(side='left', padx=5)
        self.client_combobox = ttk.Combobox(top_frame, state='readonly', width=40)
        self.client_combobox.pack(side='left', padx=5)
        self.client_combobox.bind('<<ComboboxSelected>>', self.on_client_select)
        
        # Информация о клиенте
        self.client_info_label = ttk.Label(top_frame, text="", foreground='gray')
        self.client_info_label.pack(side='left', padx=20)
        
        # Список сотрудников
        list_frame = ttk.Frame(self.parent)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')
        
        columns = ('id', 'full_name', 'salary', 'hire_date', 'fire_date', 'status')
        self.emp_tree = ttk.Treeview(tree_frame, columns=columns, 
                                     show='headings', height=15,
                                     yscrollcommand=scrollbar.set)
        
        self.emp_tree.heading('id', text='№')
        self.emp_tree.heading('full_name', text='ФИО')
        self.emp_tree.heading('salary', text='Оклад (руб.)')
        self.emp_tree.heading('hire_date', text='Дата приема')
        self.emp_tree.heading('fire_date', text='Дата увольнения')
        self.emp_tree.heading('status', text='Статус')
        
        self.emp_tree.column('id', width=40, anchor='center')
        self.emp_tree.column('full_name', width=200)
        self.emp_tree.column('salary', width=100, anchor='e')
        self.emp_tree.column('hire_date', width=100, anchor='center')
        self.emp_tree.column('fire_date', width=100, anchor='center')
        self.emp_tree.column('status', width=80, anchor='center')
        
        self.emp_tree.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.emp_tree.yview)
        
        # Кнопки действий
        btn_frame = ttk.LabelFrame(self.parent, text="Действия с сотрудниками", padding=10)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(btn_frame, text="➕ Добавить", 
                  command=self.add_employee_dialog).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🚫 Уволить", 
                  command=self.fire_employee).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="💰 Изменить оклад", 
                  command=self.change_salary_dialog).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🗑️ Удалить", 
                  command=self.delete_employee).pack(side='left', padx=5)

    def refresh_clients_list(self, clients):
        """Обновление списка клиентов в выпадающем списке"""
        self.clients = clients
        client_names = [f"{c[1]} (ИНН: {c[2]})" for c in clients]
        self.client_combobox['values'] = client_names
        
        if client_names and not self.client_combobox.get():
            self.client_combobox.set(client_names[0])
            self.on_client_select()

    def on_client_select(self, event=None):
        """Обработка выбора клиента"""
        selected = self.client_combobox.get()
        if not selected:
            return
        
        for client in self.clients:
            if f"{client[1]} (ИНН: {client[2]})" == selected:
                self.current_client_id = client[0]
                self.client_info_label.config(
                    text=f"ИНН: {client[2]} | ОГРНИП: {client[3] or '—'}"
                )
                self.refresh_employees_list()
                break

    def refresh_employees_list(self):
        """Обновление списка сотрудников"""
        self.emp_tree.delete(*self.emp_tree.get_children())
        if not self.current_client_id:
            return
        
        employees = self.db.get_employees(self.current_client_id)
        for i, emp in enumerate(employees, 1):
            status = "✅ Работает" if emp[5] == 1 else "❌ Уволен"
            salary_formatted = f"{emp[2]:,}".replace(',', ' ')
            
            self.emp_tree.insert('', 'end', values=(
                i,
                emp[1],
                salary_formatted,
                emp[3],
                emp[4] if emp[4] else '—',
                status
            ))

    def add_employee_dialog(self):
        """Диалог добавления сотрудника"""
        if not self.current_client_id:
            messagebox.showwarning("⚠️ Внимание", "Сначала выберите клиента!")
            return

        dialog = tk.Toplevel(self.parent)
        dialog.title("➕ Добавить сотрудника")
        dialog.geometry("400x400")
        dialog.transient(self.parent)
        dialog.grab_set()

        ttk.Label(dialog, text="ФИО сотрудника:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        name_entry.focus()

        ttk.Label(dialog, text="Оклад (руб.):").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        vcmd = (dialog.register(lambda v: v == "" or v.isdigit()), '%P')
        salary_entry = ttk.Entry(dialog, width=30, validate='key', validatecommand=vcmd)
        salary_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(dialog, text="Дата приема:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        hire_date = DateEntry(dialog, width=28, background='darkblue', 
                            foreground='white', borderwidth=2,
                            date_pattern='yyyy-mm-dd')
        hire_date.grid(row=2, column=1, padx=5, pady=5)

        self.is_fired_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(dialog, text="Сотрудник уволен", 
                       variable=self.is_fired_var,
                       command=self.toggle_fire_date).grid(row=3, column=1, padx=5, pady=5, sticky='w')

        ttk.Label(dialog, text="Дата увольнения:").grid(row=4, column=0, padx=5, pady=5, sticky='e')
        self.fire_date_entry = DateEntry(dialog, width=28, background='darkblue',
                                       foreground='white', borderwidth=2,
                                       date_pattern='yyyy-mm-dd')
        self.fire_date_entry.grid(row=4, column=1, padx=5, pady=5)
        self.fire_date_entry.configure(state='disabled')

        def save_employee():
            name = name_entry.get().strip()
            salary_str = salary_entry.get().strip()
            
            if not name or not salary_str:
                messagebox.showerror("❌ Ошибка", "Заполните ФИО и оклад!")
                return
            
            try:
                salary = int(salary_str)
                if salary <= 0:
                    messagebox.showerror("❌ Ошибка", "Оклад должен быть больше нуля!")
                    return
            except ValueError:
                messagebox.showerror("❌ Ошибка", "Оклад должен быть числом!")
                return

            hire = hire_date.get()
            
            if self.is_fired_var.get():
                fire = self.fire_date_entry.get()
                if fire <= hire:
                    messagebox.showerror("❌ Ошибка", 
                                       "Дата увольнения должна быть позже даты приема!")
                    return
            else:
                fire = None

            success, message = self.db.add_employee(
                self.current_client_id, name, salary, hire, fire
            )
            
            if success:
                dialog.destroy()
                self.refresh_employees_list()
                messagebox.showinfo("✅ Успех", message)
            else:
                messagebox.showerror("❌ Ошибка", message)

        ttk.Button(dialog, text="✅ Сохранить", command=save_employee).grid(row=5, column=1, pady=20)
        ttk.Button(dialog, text="❌ Отмена", command=dialog.destroy).grid(row=5, column=0, pady=20)

    def toggle_fire_date(self):
        """Включение/выключение даты увольнения"""
        if self.is_fired_var.get():
            self.fire_date_entry.configure(state='normal')
        else:
            self.fire_date_entry.configure(state='disabled')

    def fire_employee(self):
        """Увольнение сотрудника"""
        selected = self.emp_tree.selection()
        if not selected:
            messagebox.showwarning("⚠️ Внимание", "Выберите сотрудника для увольнения!")
            return
        
        item = self.emp_tree.item(selected[0])
        emp_name = item['values'][1]
        emp_status = item['values'][5]
        
        if "Уволен" in emp_status:
            messagebox.showinfo("ℹ️ Информация", "Этот сотрудник уже уволен!")
            return
        
        employees = self.db.get_employees(self.current_client_id)
        emp_id = None
        for i, emp in enumerate(employees, 1):
            if i == int(item['values'][0]):
                emp_id = emp[0]
                break
        
        if not emp_id:
            messagebox.showerror("❌ Ошибка", "Сотрудник не найден в базе!")
            return

        dialog = tk.Toplevel(self.parent)
        dialog.title(f"🚫 Увольнение: {emp_name}")
        dialog.geometry("350x150")
        dialog.transient(self.parent)
        dialog.grab_set()

        ttk.Label(dialog, text=f"Дата увольнения для {emp_name}:", 
                 font=('Arial', 10, 'bold')).pack(pady=10)
        
        fire_date = DateEntry(dialog, width=30, background='darkblue', 
                            foreground='white', borderwidth=2,
                            date_pattern='yyyy-mm-dd')
        fire_date.pack(pady=10)

        def confirm_fire():
            success, message = self.db.fire_employee(emp_id, fire_date.get())
            if success:
                dialog.destroy()
                self.refresh_employees_list()
                messagebox.showinfo("✅ Успех", f"{emp_name} уволен с {fire_date.get()}")
            else:
                messagebox.showerror("❌ Ошибка", message)

        ttk.Button(dialog, text="✅ Подтвердить увольнение", 
                  command=confirm_fire).pack(pady=10)

    def change_salary_dialog(self):
        """Диалог изменения оклада"""
        selected = self.emp_tree.selection()
        if not selected:
            messagebox.showwarning("⚠️ Внимание", "Выберите сотрудника!")
            return
        
        item = self.emp_tree.item(selected[0])
        emp_name = item['values'][1]
        old_salary = item['values'][2].replace(' ', '')
        
        employees = self.db.get_employees(self.current_client_id)
        emp_id = None
        for i, emp in enumerate(employees, 1):
            if i == int(item['values'][0]):
                emp_id = emp[0]
                break

        dialog = tk.Toplevel(self.parent)
        dialog.title(f"💰 Изменить оклад: {emp_name}")
        dialog.geometry("300x200")
        dialog.transient(self.parent)
        dialog.grab_set()

        ttk.Label(dialog, text=f"Текущий оклад: {old_salary} руб.", 
                 font=('Arial', 10)).pack(pady=10)
        ttk.Label(dialog, text="Новый оклад (руб.):").pack(pady=5)
        
        vcmd = (dialog.register(lambda v: v == "" or v.isdigit()), '%P')
        salary_entry = ttk.Entry(dialog, width=20, validate='key', validatecommand=vcmd)
        salary_entry.pack(pady=5)
        salary_entry.focus()

        def update_salary():
            try:
                new_salary = int(salary_entry.get())
                if new_salary <= 0:
                    messagebox.showerror("❌ Ошибка", "Оклад должен быть положительным!")
                    return
                
                success, message = self.db.update_salary(emp_id, new_salary)
                if success:
                    dialog.destroy()
                    self.refresh_employees_list()
                    messagebox.showinfo("✅ Успех", message)
                else:
                    messagebox.showerror("❌ Ошибка", message)
            except ValueError:
                messagebox.showerror("❌ Ошибка", "Введите число!")

        ttk.Button(dialog, text="💾 Сохранить", command=update_salary).pack(pady=10)

    def delete_employee(self):
        """Удаление сотрудника"""
        selected = self.emp_tree.selection()
        if not selected:
            messagebox.showwarning("⚠️ Внимание", "Выберите сотрудника для удаления!")
            return
        
        # Получаем данные выбранного сотрудника из таблицы
        item = self.emp_tree.item(selected[0])
        emp_name = item['values'][1]
        emp_status = item['values'][5]
        
        # Получаем ВСЕХ сотрудников из базы
        employees = self.db.get_employees(self.current_client_id)
        
        # Находим нужного сотрудника по порядковому номеру в таблице
        emp_id = None
        for i, emp in enumerate(employees):
            if i + 1 == int(item['values'][0]):
                emp_id = emp[0]
                break
        
        if not emp_id:
            messagebox.showerror("❌ Ошибка", "Сотрудник не найден в базе!")
            return
        
        # Запрашиваем подтверждение
        result = messagebox.askyesno(
            "⚠️ Подтверждение удаления",
            f"Вы действительно хотите навсегда удалить сотрудника?\n\n"
            f"👤 ФИО: {emp_name}\n"
            f"📊 Статус: {emp_status}\n\n"
            f"❗ Это действие нельзя отменить!\n"
            f"Все данные этого сотрудника будут удалены."
        )
        
        if not result:
            return
        
        # Удаляем сотрудника
        success, message = self.db.delete_employee(emp_id)
        
        if success:
            self.refresh_employees_list()
            messagebox.showinfo("✅ Успех", message)
        else:
            messagebox.showerror("❌ Ошибка", message)