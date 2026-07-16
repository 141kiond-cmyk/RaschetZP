import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import logging

class MessagesTab:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        
        self.create_widgets()
        logging.info("Вкладка 'Сообщения' создана")

    def create_widgets(self):
        # Заголовок
        header_frame = ttk.Frame(self.parent)
        header_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(header_frame, text="📝 Сообщения для отправки предпринимателям",
                 font=('Arial', 10, 'bold')).pack(side='left')
        
        # Счетчик сообщений
        self.msg_count_label = ttk.Label(header_frame, text="", foreground='gray')
        self.msg_count_label.pack(side='right')
        
        # Текстовое поле для сообщений
        self.message_text = scrolledtext.ScrolledText(self.parent, height=20, 
                                                      font=("Consolas", 10))
        self.message_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Кнопки действий
        btn_frame = ttk.Frame(self.parent)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(btn_frame, text="📋 Копировать всё", 
                  command=self.copy_all).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="📝 Копировать выделенное", 
                  command=self.copy_selected).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🗑️ Очистить", 
                  command=self.clear_messages).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="💾 Сохранить в файл", 
                  command=self.save_to_file).pack(side='left', padx=5)
        
        # Горячие клавиши
        self.parent.master.bind('<Control-a>', lambda e: self.select_all())
        self.parent.master.bind('<Control-c>', lambda e: self.copy_selected())

    def add_message(self, text):
        """Добавление сообщения"""
        current_text = self.message_text.get(1.0, tk.END).strip()
        
        if current_text:
            # Если уже есть текст, добавляем разделитель
            self.message_text.insert(tk.END, "\n\n" + "="*50 + "\n\n")
        
        self.message_text.insert(tk.END, text)
        self.update_count()

    def copy_all(self):
        """Копирование всего текста"""
        text = self.message_text.get(1.0, tk.END).strip()
        if text:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(text)
            messagebox.showinfo("✅ Успех", "Сообщение скопировано в буфер обмена!")
            logging.info("Сообщение скопировано в буфер обмена")
        else:
            messagebox.showwarning("⚠️ Внимание", "Нет сообщений для копирования!")

    def copy_selected(self):
        """Копирование выделенного текста"""
        try:
            text = self.message_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            if text:
                self.parent.clipboard_clear()
                self.parent.clipboard_append(text)
                messagebox.showinfo("✅ Успех", "Выделенный текст скопирован!")
        except tk.TclError:
            # Если текст не выделен
            messagebox.showinfo("ℹ️ Информация", "Сначала выделите текст для копирования")

    def select_all(self):
        """Выделение всего текста"""
        self.message_text.tag_add(tk.SEL, "1.0", tk.END)
        self.message_text.mark_set(tk.INSERT, "1.0")
        self.message_text.see(tk.INSERT)
        return 'break'

    def clear_messages(self):
        """Очистка всех сообщений"""
        if messagebox.askyesno("⚠️ Подтверждение", "Удалить все сообщения?"):
            self.message_text.delete(1.0, tk.END)
            self.update_count()
            logging.info("Сообщения очищены")

    def save_to_file(self):
        """Сохранение сообщений в текстовый файл"""
        text = self.message_text.get(1.0, tk.END).strip()
        if not text:
            messagebox.showwarning("⚠️ Внимание", "Нет сообщений для сохранения!")
            return
        
        from datetime import datetime
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")],
            initialfile=f"Сообщение_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(text)
            messagebox.showinfo("✅ Успех", f"Сообщение сохранено в файл:\n{filename}")
            logging.info(f"Сообщение сохранено в {filename}")

    def update_count(self):
        """Обновление счетчика сообщений"""
        text = self.message_text.get(1.0, tk.END).strip()
        if text:
            lines = len(text.split('\n'))
            self.msg_count_label.config(text=f"Строк: {lines}")
        else:
            self.msg_count_label.config(text="")