import tkinter as tk
from tkinter import ttk, messagebox
import logging
import sys

from database import Database
from work_calendar import WorkCalendar
from gui_clients import ClientsTab
from gui_employees import EmployeesTab
from gui_calculations import CalculationsTab
from gui_messages import MessagesTab

# Настройка логирования - запись всех действий в файл
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('buh.log', encoding='utf-8'),  # Запись в файл
        logging.StreamHandler(sys.stdout)  # Вывод в консоль
    ]
)

class BuhApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🧮 Бухгалтерский помощник v4.0")
        self.root.geometry("1100x750")
        
        # Запуск программы
        logging.info("=== Запуск программы ===")
        
        # Создаем базу данных и календарь
        self.db = Database()
        self.calendar = WorkCalendar()
        
        # Создаем интерфейс
        self.create_menu()
        self.create_notebook()
        self.create_status_bar()
        
        # Настраиваем горячие клавиши
        self.bind_hotkeys()
        
        # Загружаем все данные
        self.refresh_all()
        
        # Запускаем автосохранение (каждые 5 минут)
        self.auto_save()
        
        logging.info("Программа готова к работе")

    def create_menu(self):
        """Создание главного меню (Файл, Правка, Вид, Помощь)"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Меню "Файл"
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="📁 Файл", menu=file_menu)
        file_menu.add_command(label="🔄 Обновить все данные", command=self.refresh_all)
        file_menu.add_separator()  # Разделительная линия
        file_menu.add_command(label="❌ Выход", command=self.on_exit)
        
        # Меню "Правка"
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="✏️ Правка", menu=edit_menu)
        edit_menu.add_command(label="➕ Добавить клиента", 
                            command=lambda: self.clients_tab.add_client_dialog())
        
        # Меню "Вид"
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="👁️ Вид", menu=view_menu)
        view_menu.add_command(label="📊 Перейти к Расчетам", 
                            command=lambda: self.notebook.select(2))
        view_menu.add_command(label="📝 Перейти к Сообщениям", 
                            command=lambda: self.notebook.select(3))
        
        # Меню "Помощь"
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="❓ Помощь", menu=help_menu)
        help_menu.add_command(label="ℹ️ О программе", command=self.show_about)

    def create_notebook(self):
        """Создание вкладок (Клиенты, Сотрудники, Расчеты, Сообщения)"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Создаем пустые рамки для каждой вкладки
        clients_frame = ttk.Frame(self.notebook)
        employees_frame = ttk.Frame(self.notebook)
        calculations_frame = ttk.Frame(self.notebook)
        messages_frame = ttk.Frame(self.notebook)
        
        # Добавляем вкладки в блокнот
        self.notebook.add(clients_frame, text="🏢 Клиенты")
        self.notebook.add(employees_frame, text="👥 Сотрудники")
        self.notebook.add(calculations_frame, text="🧮 Расчеты")
        self.notebook.add(messages_frame, text="📝 Сообщения")
        
        # Создаем содержимое каждой вкладки
        # Передаем self (приложение) чтобы вкладки могли обновлять друг друга
        self.clients_tab = ClientsTab(clients_frame, self.db, self)
        self.employees_tab = EmployeesTab(employees_frame, self.db, self)
        self.calculations_tab = CalculationsTab(calculations_frame, self.db, 
                                               self.calendar, self)
        self.messages_tab = MessagesTab(messages_frame, self)

    def create_status_bar(self):
        """Создание строки состояния внизу окна"""
        self.status_bar = ttk.Label(
            self.root, 
            text="✅ Готов к работе", 
            relief=tk.SUNKEN,  # "Утопленный" стиль
            anchor='w'  # Текст прижат к левому краю
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def bind_hotkeys(self):
        """Настройка горячих клавиш"""
        # Ctrl+N - добавить нового клиента
        self.root.bind('<Control-n>', lambda e: self.clients_tab.add_client_dialog())
        # Ctrl+F - перейти к поиску клиентов
        self.root.bind('<Control-f>', lambda e: self.focus_search())
        # F5 - обновить все данные
        self.root.bind('<F5>', lambda e: self.refresh_all())
        # Ctrl+Q - выход из программы
        self.root.bind('<Control-q>', lambda e: self.on_exit())

    def focus_search(self):
        """Переключение на вкладку Клиенты и фокус на поиск"""
        self.notebook.select(0)  # Переключаемся на первую вкладку (Клиенты)
        self.clients_tab.search_var.set('')  # Очищаем поиск
        # Пытаемся установить фокус на поле поиска
        try:
            self.clients_tab.focus_search()
        except:
            pass

    def refresh_all(self):
        """Обновление всех данных во всех вкладках"""
        try:
            # Получаем актуальный список клиентов из базы
            clients = self.db.get_all_clients()
            
            # Обновляем все вкладки
            self.clients_tab.refresh_list(clients)
            self.employees_tab.refresh_clients_list(clients)
            self.calculations_tab.refresh_clients_list(clients)
            
            # Показываем сообщение в статус-баре
            self.set_status(f"✅ Данные обновлены. Всего клиентов: {len(clients)}")
            logging.info(f"Данные обновлены. Клиентов: {len(clients)}")
            
        except Exception as e:
            # Если произошла ошибка - показываем в статус-баре
            self.set_status(f"❌ Ошибка обновления: {e}")
            logging.error(f"Ошибка при обновлении данных: {e}")

    def set_status(self, message):
        """Показать сообщение в строке состояния"""
        self.status_bar.config(text=message)
        self.root.update_idletasks()  # Мгновенное обновление интерфейса

    def auto_save(self):
        """Автоматическое сохранение данных каждые 5 минут"""
        # Здесь можно добавить сохранение резервной копии базы данных
        # Пока просто записываем в лог
        logging.debug("Автосохранение выполнено")
        
        # Запускаем следующее автосохранение через 5 минут (300000 миллисекунд)
        self.root.after(300000, self.auto_save)

    def show_about(self):
        """Окно 'О программе'"""
        messagebox.showinfo(
            "ℹ️ О программе",
            "Бухгалтерский помощник v4.0\n\n"
            "Программа для расчета заработной платы\n"
            "и ведения учета сотрудников ИП.\n\n"
            "Возможности:\n"
            "✓ Учет клиентов (ИП)\n"
            "✓ Учет сотрудников\n"
            "✓ Расчет аванса и зарплаты\n"
            "✓ Учет праздничных дней\n"
            "✓ Экспорт в Excel\n\n"
            "© 2024 Все права защищены"
        )

    def on_exit(self):
        """Корректное закрытие программы"""
        if messagebox.askyesno("❌ Подтверждение", "Закрыть программу?"):
            logging.info("Программа закрыта пользователем")
            self.db.close()  # Закрываем соединение с базой данных
            self.root.destroy()  # Закрываем окно

# Точка входа в программу
if __name__ == "__main__":
    try:
        # Создаем главное окно
        root = tk.Tk()
        app = BuhApp(root)
        
        # При закрытии окна (на крестик) вызываем правильное завершение
        root.protocol("WM_DELETE_WINDOW", app.on_exit)
        
        # Запускаем главный цикл программы
        root.mainloop()
        
    except Exception as e:
        # Если произошла критическая ошибка при запуске
        logging.critical(f"Критическая ошибка при запуске: {e}", exc_info=True)
        messagebox.showerror(
            "❌ Критическая ошибка", 
            f"Не удалось запустить программу:\n\n{e}\n\n"
            f"Проверьте, что все файлы программы находятся в одной папке."
        )