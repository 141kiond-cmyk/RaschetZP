import sqlite3
import logging
from datetime import datetime

# Настраиваю логирование - программа будет записывать все свои действия
logging.basicConfig(
    filename='buh.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

class Database:
    def __init__(self, db_name="buh.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.create_indexes()
        logging.info("База данных подключена и готова к работе")

    def create_tables(self):
        """Создание таблиц, если их ещё нет"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                inn TEXT UNIQUE NOT NULL,
                ogrnip TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                full_name TEXT NOT NULL,
                salary INTEGER NOT NULL CHECK(salary > 0),
                hire_date DATE NOT NULL,
                fire_date DATE,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
            )
        ''')
        self.conn.commit()
        logging.info("Таблицы созданы/проверены")

    def create_indexes(self):
        """Создание индексов для ускорения поиска"""
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_employees_client 
            ON employees(client_id)
        ''')
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_employees_dates 
            ON employees(hire_date, fire_date)
        ''')
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_employees_active 
            ON employees(is_active)
        ''')
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_clients_inn 
            ON clients(inn)
        ''')
        self.conn.commit()
        logging.info("Индексы созданы для ускорения поиска")

    def validate_inn(self, inn):
        """Проверка ИНН на корректность"""
        inn = inn.strip()
        if not inn.isdigit():
            raise ValueError("ИНН должен состоять только из цифр")
        if len(inn) != 12:
            raise ValueError("ИНН должен содержать ровно 12 цифр")
        return inn

    # ---------- КЛИЕНТЫ ----------
    def add_client(self, full_name, inn, ogrnip=""):
        """Добавление нового клиента с проверками"""
        try:
            inn = self.validate_inn(inn)
            full_name = full_name.strip()
            
            if not full_name:
                raise ValueError("ФИО не может быть пустым")
            
            self.cursor.execute(
                "INSERT INTO clients (full_name, inn, ogrnip) VALUES (?, ?, ?)",
                (full_name, inn, ogrnip.strip() if ogrnip else "")
            )
            self.conn.commit()
            logging.info(f"Добавлен клиент: {full_name}, ИНН: {inn}")
            return True, f"Клиент {full_name} успешно добавлен"
            
        except sqlite3.IntegrityError:
            error_msg = f"Клиент с ИНН {inn} уже существует в базе!"
            logging.warning(error_msg)
            return False, error_msg
        except ValueError as e:
            logging.warning(f"Ошибка валидации: {e}")
            return False, str(e)
        except Exception as e:
            error_msg = f"Неизвестная ошибка при добавлении клиента: {e}"
            logging.error(error_msg)
            return False, error_msg

    def get_all_clients(self):
        """Получение списка всех клиентов"""
        self.cursor.execute(
            "SELECT id, full_name, inn, ogrnip FROM clients ORDER BY full_name"
        )
        return self.cursor.fetchall()

    def search_clients(self, search_term):
        """Поиск клиентов по имени или ИНН"""
        search_term = f"%{search_term}%"
        self.cursor.execute(
            """SELECT id, full_name, inn, ogrnip 
               FROM clients 
               WHERE full_name LIKE ? OR inn LIKE ?
               ORDER BY full_name""",
            (search_term, search_term)
        )
        return self.cursor.fetchall()

    def update_client(self, client_id, full_name, inn, ogrnip):
        """Обновление данных клиента"""
        try:
            inn = self.validate_inn(inn)
            full_name = full_name.strip()
            
            if not full_name:
                raise ValueError("ФИО не может быть пустым")
            
            self.cursor.execute(
                "UPDATE clients SET full_name=?, inn=?, ogrnip=? WHERE id=?",
                (full_name, inn, ogrnip.strip() if ogrnip else "", client_id)
            )
            self.conn.commit()
            logging.info(f"Обновлен клиент ID={client_id}: {full_name}")
            return True, "Данные клиента обновлены"
            
        except sqlite3.IntegrityError:
            error_msg = f"Клиент с ИНН {inn} уже существует!"
            logging.warning(error_msg)
            return False, error_msg
        except ValueError as e:
            return False, str(e)

    def delete_client(self, client_id):
        """Удаление клиента и всех его сотрудников"""
        try:
            self.cursor.execute("SELECT full_name FROM clients WHERE id=?", (client_id,))
            client = self.cursor.fetchone()
            client_name = client[0] if client else "Неизвестный"
            
            self.cursor.execute("DELETE FROM employees WHERE client_id=?", (client_id,))
            self.cursor.execute("DELETE FROM clients WHERE id=?", (client_id,))
            self.conn.commit()
            
            logging.info(f"Удален клиент: {client_name} (ID={client_id})")
            return True, f"Клиент {client_name} и все его сотрудники удалены"
        except Exception as e:
            logging.error(f"Ошибка при удалении клиента: {e}")
            return False, f"Ошибка при удалении: {e}"

    # ---------- СОТРУДНИКИ ----------
    def add_employee(self, client_id, full_name, salary, hire_date, fire_date=None):
        """Добавление сотрудника с проверками"""
        try:
            full_name = full_name.strip()
            if not full_name:
                raise ValueError("ФИО сотрудника не может быть пустым")
            
            if salary <= 0:
                raise ValueError("Оклад должен быть положительным числом")
            
            if fire_date and fire_date <= hire_date:
                raise ValueError("Дата увольнения должна быть позже даты приема")
            
            is_active = 1 if fire_date is None else 0
            
            self.cursor.execute('''
                INSERT INTO employees (client_id, full_name, salary, hire_date, fire_date, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (client_id, full_name, salary, hire_date, fire_date, is_active))
            self.conn.commit()
            
            logging.info(f"Добавлен сотрудник: {full_name} с окладом {salary} руб.")
            return True, f"Сотрудник {full_name} добавлен"
            
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            logging.error(f"Ошибка при добавлении сотрудника: {e}")
            return False, f"Ошибка: {e}"

    def get_employees(self, client_id):
        """Получение списка сотрудников клиента"""
        self.cursor.execute('''
            SELECT id, full_name, salary, hire_date, fire_date, is_active
            FROM employees WHERE client_id=? ORDER BY full_name
        ''', (client_id,))
        return self.cursor.fetchall()

    def fire_employee(self, employee_id, fire_date):
        """Увольнение сотрудника"""
        try:
            self.cursor.execute('''
                UPDATE employees SET fire_date=?, is_active=0 WHERE id=?
            ''', (fire_date, employee_id))
            self.conn.commit()
            
            logging.info(f"Сотрудник ID={employee_id} уволен с {fire_date}")
            return True, "Сотрудник уволен"
        except Exception as e:
            return False, f"Ошибка при увольнении: {e}"

    def update_salary(self, employee_id, new_salary):
        """Изменение оклада сотрудника"""
        try:
            if new_salary <= 0:
                raise ValueError("Оклад должен быть положительным числом")
            
            self.cursor.execute('''
                UPDATE employees SET salary=? WHERE id=?
            ''', (new_salary, employee_id))
            self.conn.commit()
            
            logging.info(f"Изменен оклад сотрудника ID={employee_id} на {new_salary} руб.")
            return True, f"Оклад изменен на {new_salary} руб."
        except ValueError as e:
            return False, str(e)

    def get_employee(self, employee_id):
        """Получение данных одного сотрудника"""
        self.cursor.execute('''
            SELECT id, client_id, full_name, salary, hire_date, fire_date
            FROM employees WHERE id=?
        ''', (employee_id,))
        return self.cursor.fetchone()

    def delete_employee(self, employee_id):
        """Удаление сотрудника"""
        try:
            self.cursor.execute("DELETE FROM employees WHERE id=?", (employee_id,))
            self.conn.commit()
            logging.info(f"Сотрудник ID={employee_id} удален")
            return True, "Сотрудник удален"
        except Exception as e:
            logging.error(f"Ошибка удаления сотрудника: {e}")
            return False, f"Ошибка: {e}"

    # ---------- РАСЧЕТЫ ----------
    def get_active_employees_for_month(self, client_id, year, month):
        """Получение сотрудников, работавших в указанном месяце"""
        from datetime import timedelta
        
        month_start = f"{year}-{month:02d}-01"
        if month == 12:
            month_end = f"{year}-12-31"
        else:
            next_month = datetime(year, month + 1, 1)
            last_day = (next_month - timedelta(days=1)).day
            month_end = f"{year}-{month:02d}-{last_day:02d}"

        self.cursor.execute('''
            SELECT id, full_name, salary, hire_date, fire_date
            FROM employees
            WHERE client_id=?
            AND hire_date <= ?
            AND (fire_date IS NULL OR fire_date >= ?)
            AND is_active = 1
        ''', (client_id, month_end, month_start))
        return self.cursor.fetchall()

    def close(self):
        """Закрытие соединения с базой данных"""
        self.conn.close()
        logging.info("Соединение с базой данных закрыто")