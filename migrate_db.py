import sqlite3
import logging

logging.basicConfig(level=logging.INFO)

def migrate_database(db_name="buh.db"):
    """Добавление таблицы для сохранения расчетов"""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Создаем таблицу для хранения расчетов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calculations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            payment_type TEXT NOT NULL CHECK(payment_type IN ('advance', 'salary')),
            worked_days INTEGER NOT NULL,
            total_workdays INTEGER NOT NULL,
            accrued REAL NOT NULL,
            ndfl REAL NOT NULL,
            ndfl_advance REAL DEFAULT 0,
            ndfl_second_half REAL DEFAULT 0,
            advance_paid REAL DEFAULT 0,
            to_pay REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
        )
    ''')
    
    # Индекс для быстрого поиска по клиенту и периоду
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_calculations_period 
        ON calculations(client_id, year, month)
    ''')
    
    conn.commit()
    conn.close()
    logging.info("Миграция базы данных выполнена успешно!")

if __name__ == "__main__":
    migrate_database()
    print("✅ База данных обновлена. Добавлена таблица calculations.")
