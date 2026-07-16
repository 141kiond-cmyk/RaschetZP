import tkinter as tk
from tkinter import ttk, messagebox
import logging

class ClientsTab:
    def __init__(self, parent, db, app):
        self.parent = parent
        self.db = db
        self.app = app  # Ссылка на главное приложение для обновления других вкладок
        self.current_client_id = None
        
        self.create_widgets()
        logging.info("Вкладка 'Клиенты' создана")

    def create_widgets(self):
        # Основной контейнер
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill='both', expand=True)
        
        # Левая панель с поиском и списком
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        
        # Строка поиска
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(search_frame, text="🔍 Поиск:").pack(side='left', padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.on_search())
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side='left', fill='x', expand=True, padx=5)
        
        # Кнопка очистки поиска
        ttk.Button(search_frame, text="✕", width=3, 
                  command=self.clear_search).pack(side='left')
        
        # Список клиентов
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill='both', expand=True)
        
        ttk.Label(list_frame, text="Список клиентов:").pack(anchor='w')
        
        # Добавляем scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.clients_listbox = tk.Listbox(list_frame, height=20, 
                                         yscrollcommand=scrollbar.set)
        self.clients_listbox.pack(fill='both', expand=True)
        scrollbar.config(command=self.clients_listbox.yview)
        
        self.clients_listbox.bind('<<ListboxSelect>>', self.on_client_select)
        # Двойной клик для редактирования
        self.clients_listbox.bind('<Double-Button-1>', lambda e: self.edit_client_dialog())
        
        # Правая панель с кнопками и информацией
        right_frame = ttk.Frame(main_frame, width=250)
        right_frame.pack(side='right', fill='y', padx=10, pady=5)
        right_frame.pack_propagate(False)
        
        # Кнопки действий
        btn_frame = ttk.LabelFrame(right_frame, text="Действия", padding=10)
        btn_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Button(btn_frame, text="➕ Добавить ИП", 
                  command=self.add_client_dialog).pack(fill='x', pady=2)
        ttk.Button(btn_frame, text="✏️ Редактировать", 
                  command=self.edit_client_dialog).pack(fill='x', pady=2)
        ttk.Button(btn_frame, text="🗑️ Удалить", 
                  command=self.delete_client).pack(fill='x', pady=2)
        
        # Информация о клиенте
        info_frame = ttk.LabelFrame(right_frame, text="Информация о клиенте", padding=10)
        info_frame.pack(fill='both', expand=True)
        
        self.client_info = tk.Text(info_frame, height=8, width=30, 
                                   state='disabled', wrap='word')
        self.client_info.pack(fill='both', expand=True)

    def refresh_list(self, clients=None):
        """Обновление списка клиентов"""
        if clients is None:
            clients = self.db.get_all_clients()
        
        self.clients_listbox.delete(0, tk.END)
        for client in clients:
            self.clients_listbox.insert(tk.END, f"{client[1]} (ИНН: {client[2]})")

    def on_search(self):
        """Поиск при вводе текста"""
        search_term = self.search_var.get().strip()
        if search_term:
            clients = self.db.search_clients(search_term)
        else:
            clients = self.db.get_all_clients()
        self.refresh_list(clients)

    def clear_search(self):
        """Очистка строки поиска"""
        self.search_var.set('')

    def on_client_select(self, event=None):
        """Обработка выбора клиента из списка"""
        selection = self.clients_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        clients = self.db.get_all_clients()
        
        if index < len(clients):
            client = clients[index]
            self.current_client_id = client[0]
            
            # Показываем информацию
            info = f"ФИО: {client[1]}\n"
            info += f"ИНН: {client[2]}\n"
            info += f"ОГРНИП: {client[3] or '—'}\n"
            
            # Считаем количество сотрудников
            employees = self.db.get_employees(client[0])
            active = sum(1 for emp in employees if emp[5] == 1)
            info += f"\nСотрудников: {len(employees)} (активных: {active})"
            
            self.client_info.config(state='normal')
            self.client_info.delete(1.0, tk.END)
            self.client_info.insert(1.0, info)
            self.client_info.config(state='disabled')

    def add_client_dialog(self):
        """Диалог добавления нового клиента"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("➕ Добавить нового ИП")
        dialog.geometry("400x250")
        dialog.resizable(False, False)
        
        # Центрируем окно
        dialog.transient(self.parent)
        dialog.grab_set()

        ttk.Label(dialog, text="ФИО:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        name_entry.focus()

        ttk.Label(dialog, text="ИНН (12 цифр):").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        # Проверка - только цифры и максимум 12 символов
        vcmd = (dialog.register(self.validate_inn_input), '%P')
        inn_entry = ttk.Entry(dialog, width=30, validate='key', validatecommand=vcmd)
        inn_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(dialog, text="ОГРНИП (необязательно):").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        ogrnip_entry = ttk.Entry(dialog, width=30)
        ogrnip_entry.grid(row=2, column=1, padx=5, pady=5)

        def save_client():
            name = name_entry.get().strip()
            inn = inn_entry.get().strip()
            ogrnip = ogrnip_entry.get().strip()
            
            if not name or not inn:
                messagebox.showerror("❌ Ошибка", "ФИО и ИНН обязательны для заполнения!")
                return
            
            success, message = self.db.add_client(name, inn, ogrnip)
            if success:
                dialog.destroy()
                self.refresh_list()
                self.app.refresh_all()  # Обновляем все вкладки
                messagebox.showinfo("✅ Успех", message)
            else:
                messagebox.showerror("❌ Ошибка", message)

        ttk.Button(dialog, text="✅ Сохранить", command=save_client).grid(row=3, column=1, pady=20)
        ttk.Button(dialog, text="❌ Отмена", command=dialog.destroy).grid(row=3, column=0, pady=20)

    def validate_inn_input(self, value):
        """Проверка ввода ИНН - только цифры, не больше 12"""
        if value == "":
            return True
        return value.isdigit() and len(value) <= 12

    def edit_client_dialog(self):
        """Диалог редактирования клиента"""
        if not self.current_client_id:
            messagebox.showwarning("⚠️ Внимание", "Выберите клиента в списке!")
            return
        
        # Находим клиента
        clients = self.db.get_all_clients()
        client = None
        for c in clients:
            if c[0] == self.current_client_id:
                client = c
                break
        
        if not client:
            return

        dialog = tk.Toplevel(self.parent)
        dialog.title("✏️ Редактировать клиента")
        dialog.geometry("400x250")
        dialog.transient(self.parent)
        dialog.grab_set()

        ttk.Label(dialog, text="ФИО:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.insert(0, client[1])
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        name_entry.focus()

        ttk.Label(dialog, text="ИНН:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        inn_entry = ttk.Entry(dialog, width=30)
        inn_entry.insert(0, client[2])
        inn_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(dialog, text="ОГРНИП:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        ogrnip_entry = ttk.Entry(dialog, width=30)
        ogrnip_entry.insert(0, client[3] or "")
        ogrnip_entry.grid(row=2, column=1, padx=5, pady=5)

        def update_client():
            success, message = self.db.update_client(
                self.current_client_id,
                name_entry.get().strip(),
                inn_entry.get().strip(),
                ogrnip_entry.get().strip()
            )
            if success:
                dialog.destroy()
                self.refresh_list()
                self.app.refresh_all()
                messagebox.showinfo("✅ Успех", message)
            else:
                messagebox.showerror("❌ Ошибка", message)

        ttk.Button(dialog, text="💾 Обновить", command=update_client).grid(row=3, column=1, pady=20)
        ttk.Button(dialog, text="❌ Отмена", command=dialog.destroy).grid(row=3, column=0, pady=20)

    def delete_client(self):
        """Удаление клиента"""
        if not self.current_client_id:
            messagebox.showwarning("⚠️ Внимание", "Выберите клиента в списке!")
            return
        
        if messagebox.askyesno("⚠️ Подтверждение", 
                              "Удалить клиента и всех его сотрудников?\nЭто действие нельзя отменить!"):
            success, message = self.db.delete_client(self.current_client_id)
            if success:
                self.current_client_id = None
                self.client_info.config(state='normal')
                self.client_info.delete(1.0, tk.END)
                self.client_info.config(state='disabled')
                self.refresh_list()
                self.app.refresh_all()
                messagebox.showinfo("✅ Успех", message)
            else:
                messagebox.showerror("❌ Ошибка", message)