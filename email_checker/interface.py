import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import json
import time
from datetime import datetime
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from mass_scanner import MassWebsiteEmailScanner
    SCANNER_AVAILABLE = True
    print("✅ Сканер подключен успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта сканера: {e}")
    SCANNER_AVAILABLE = False
    
    # Заглушка для тестирования GUI
    class MassWebsiteEmailScanner:
        def __init__(self, proxies=None, max_workers=20):
            self.stats = {
                'total_sites_checked': 0,
                'sites_with_emails': 0,
                'total_emails_found': 0,
                'start_time': datetime.now().isoformat(),
                'sites_processed': 0,
                'search_sites_found': 0
            }
            self.found_emails = set()
            self.stop_event = threading.Event()
            self.proxies = proxies
            self.max_workers = max_workers
            
        def run_mass_scan(self, total_sites=1000, search_query=None):
            # Имитация работы сканера для тестирования GUI
            self.log_message(f"🔧 ТЕСТОВЫЙ РЕЖИМ: Запуск сканирования {total_sites} сайтов")
            if search_query:
                self.log_message(f"🔧 Поисковый запрос: {search_query}")
            
            for i in range(total_sites):
                if self.stop_event.is_set():
                    self.log_message("⏹️ Сканирование остановлено")
                    break
                
                time.sleep(0.1)  # Имитация работы
                
                # Обновляем статистику
                self.stats['sites_processed'] = i + 1
                self.stats['total_sites_checked'] = i + 1
                
                # Имитация нахождения email
                if i % 15 == 0 and i > 0:
                    email = f"contact{i}@example.com"
                    self.found_emails.add(email)
                    self.stats['total_emails_found'] = len(self.found_emails)
                    self.stats['sites_with_emails'] += 1
                    self.log_message(f"🎯 Найден email: {email}")
                
                # Периодический лог прогресса
                if i % 50 == 0:
                    self.log_message(f"📊 Прогресс: {i+1}/{total_sites} сайтов")
            
            self.log_message("✅ Тестовое сканирование завершено")
        
        def log_message(self, message):
            # В реальном сканере это будет работать через logging
            print(f"[SCANNER] {message}")

class EmailScannerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎯 Mass Email Scanner Pro")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')
        
        # Инициализация сканера
        self.scanner = None
        self.scan_thread = None
        self.is_scanning = False
        
        # Создание интерфейса
        self.create_widgets()
        
        # Загрузка конфигурации
        self.load_config()
        
        # Статус подключения сканера
        if not SCANNER_AVAILABLE:
            self.log_message("⚠️ ВНИМАНИЕ: Режим тестирования. Основной сканер не подключен.", "WARNING")
            self.log_message("⚠️ Убедитесь, что файл mass_scanner.py находится в той же папке", "WARNING")
        
    def create_widgets(self):
        # Главный фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка весов для резинового интерфейса
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Заголовок
        title_label = ttk.Label(main_frame, 
                               text="🎯 Mass Email Scanner Pro", 
                               font=('Arial', 16, 'bold'),
                               foreground='#2c3e50')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Статус подключения
        status_text = "✅ Сканер подключен" if SCANNER_AVAILABLE else "⚠️ Тестовый режим"
        status_label = ttk.Label(main_frame, text=status_text, 
                                foreground='green' if SCANNER_AVAILABLE else 'orange')
        status_label.grid(row=0, column=2, sticky=tk.E, pady=(0, 20))
        
        # Фрейм настроек
        settings_frame = ttk.LabelFrame(main_frame, text="Настройки сканирования", padding="10")
        settings_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        settings_frame.columnconfigure(1, weight=1)
        
        # Поисковый запрос
        ttk.Label(settings_frame, text="Поисковый запрос:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(settings_frame, textvariable=self.search_var, width=40)
        self.search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        ttk.Label(settings_frame, text="(например: купить квартиру, услуги юриста)").grid(row=0, column=2, sticky=tk.W, pady=2, padx=(5, 0))
        
        # Количество сайтов
        ttk.Label(settings_frame, text="Количество сайтов:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.sites_var = tk.StringVar(value="100")
        self.sites_entry = ttk.Entry(settings_frame, textvariable=self.sites_var, width=10)
        self.sites_entry.grid(row=1, column=1, sticky=tk.W, pady=2, padx=(5, 0))
        
        # Количество потоков
        ttk.Label(settings_frame, text="Количество потоков:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.threads_var = tk.StringVar(value="10")
        self.threads_entry = ttk.Entry(settings_frame, textvariable=self.threads_var, width=10)
        self.threads_entry.grid(row=2, column=1, sticky=tk.W, pady=2, padx=(5, 0))
        
        # Режим прокси
        ttk.Label(settings_frame, text="Режим прокси:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.proxy_mode = tk.StringVar(value="with_proxy")
        ttk.Radiobutton(settings_frame, text="С прокси", variable=self.proxy_mode, value="with_proxy").grid(row=3, column=1, sticky=tk.W, pady=2)
        ttk.Radiobutton(settings_frame, text="Без прокси", variable=self.proxy_mode, value="without_proxy").grid(row=3, column=2, sticky=tk.W, pady=2)
        
        # Фрейм управления
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Кнопки управления
        self.start_button = ttk.Button(control_frame, text="🚀 Начать сканирование", command=self.start_scan)
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="⏹️ Остановить", command=self.stop_scan, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=(0, 10))
        
        self.export_button = ttk.Button(control_frame, text="💾 Экспорт email", command=self.export_emails)
        self.export_button.grid(row=0, column=2, padx=(0, 10))
        
        # Фрейм прогресса
        progress_frame = ttk.LabelFrame(main_frame, text="Прогресс сканирования", padding="10")
        progress_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        # Прогресс бар
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Статус сканирования
        self.status_var = tk.StringVar(value="Готов к работе")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        status_label.grid(row=1, column=0, sticky=tk.W)
        
        # Время работы
        self.time_var = tk.StringVar(value="Время: 00:00:00")
        time_label = ttk.Label(progress_frame, textvariable=self.time_var)
        time_label.grid(row=1, column=1, sticky=tk.E)
        
        # Фрейм статистики
        stats_frame = ttk.LabelFrame(main_frame, text="Статистика в реальном времени", padding="10")
        stats_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Сетка для статистики
        self.stats_vars = {}
        stats_data = [
            ("Проверено сайтов:", "sites_checked"),
            ("Сайтов с email:", "sites_with_emails"),
            ("Найдено email:", "emails_found"),
            ("Уникальных email:", "unique_emails"),
            ("Сайтов из поиска:", "search_sites")
        ]
        
        for i, (label, key) in enumerate(stats_data):
            ttk.Label(stats_frame, text=label, font=('Arial', 9)).grid(row=i//2, column=(i%2)*2, sticky=tk.W, pady=2)
            self.stats_vars[key] = tk.StringVar(value="0")
            ttk.Label(stats_frame, textvariable=self.stats_vars[key], font=('Arial', 9, 'bold')).grid(
                row=i//2, column=(i%2)*2+1, sticky=tk.W, pady=2, padx=(5, 20))
        
        # Фрейм логов
        log_frame = ttk.LabelFrame(main_frame, text="Лог выполнения", padding="10")
        log_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        # Текстовое поле для логов
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Кнопка очистки логов
        ttk.Button(log_frame, text="Очистить логи", command=self.clear_logs).grid(row=1, column=0, sticky=tk.E, pady=(5, 0))
        
        # Настройка времени начала
        self.start_time = None
        self.update_time_id = None
        
        # Счетчик сообщений для авто-сохранения
        self.log_counter = 0
        
    def log_message(self, message, level="INFO"):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Цветовое кодирование уровней
        if level == "ERROR":
            prefix = "❌"
            color = "red"
        elif level == "WARNING":
            prefix = "⚠️"
            color = "orange"
        elif level == "SUCCESS":
            prefix = "✅"
            color = "green"
        else:
            prefix = "ℹ️"
            color = "black"
        
        formatted_message = f"[{timestamp}] {prefix} {message}\n"
        
        # Вставляем сообщение с цветом
        self.log_text.insert(tk.END, formatted_message)
        
        # Применяем цвет к последней строке
        if level in ["ERROR", "WARNING", "SUCCESS"]:
            start_index = self.log_text.index("end-2l")
            end_index = self.log_text.index("end-1c")
            self.log_text.tag_add(level, start_index, end_index)
            self.log_text.tag_config(level, foreground=color)
        
        self.log_text.see(tk.END)
        
        # Авто-сохранение логов каждые 10 сообщений
        self.log_counter += 1
        if self.log_counter >= 10:
            self.save_logs()
            self.log_counter = 0
    
    def clear_logs(self):
        """Очистка логов"""
        self.log_text.delete(1.0, tk.END)
        self.log_counter = 0
    
    def save_logs(self):
        """Сохранение логов в файл"""
        try:
            with open('scan_log.txt', 'w', encoding='utf-8') as f:
                f.write(self.log_text.get(1.0, tk.END))
        except Exception as e:
            print(f"Ошибка сохранения логов: {e}")
    
    def load_config(self):
        """Загрузка конфигурации"""
        try:
            if os.path.exists('scanner_config.json'):
                with open('scanner_config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.search_var.set(config.get('search_query', ''))
                    self.sites_var.set(config.get('sites_count', '100'))
                    self.threads_var.set(config.get('threads_count', '10'))
                    self.proxy_mode.set(config.get('proxy_mode', 'with_proxy'))
        except Exception as e:
            self.log_message(f"Ошибка загрузки конфигурации: {e}", "ERROR")
    
    def save_config(self):
        """Сохранение конфигурации"""
        try:
            config = {
                'search_query': self.search_var.get(),
                'sites_count': self.sites_var.get(),
                'threads_count': self.threads_var.get(),
                'proxy_mode': self.proxy_mode.get()
            }
            with open('scanner_config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log_message(f"Ошибка сохранения конфигурации: {e}", "ERROR")
    
    def validate_inputs(self):
        """Проверка введенных данных"""
        try:
            sites = int(self.sites_var.get())
            threads = int(self.threads_var.get())
            
            if sites <= 0 or sites > 10000:
                messagebox.showerror("Ошибка", "Количество сайтов должно быть от 1 до 10000")
                return False
                
            if threads <= 0 or threads > 100:
                messagebox.showerror("Ошибка", "Количество потоков должно быть от 1 до 100")
                return False
                
            return True
            
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные числовые значения")
            return False
    
    def start_scan(self):
        """Запуск сканирования"""
        if not self.validate_inputs():
            return
            
        if self.is_scanning:
            messagebox.showwarning("Внимание", "Сканирование уже запущено!")
            return
        
        # Сохраняем конфигурацию
        self.save_config()
        
        # Подготовка параметров
        search_query = self.search_var.get().strip()
        if not search_query:
            search_query = None
            
        total_sites = int(self.sites_var.get())
        max_workers = int(self.threads_var.get())
        
        # Список прокси
        proxy_list = []
        if self.proxy_mode.get() == "with_proxy":
            proxy_list = [
                "191.102.154.117:9571:D2mBXc:SLokbJ",
                "191.102.172.175:9998:D2mBXc:SLokbJ",
            ]
        
        # Создание сканера
        try:
            self.scanner = MassWebsiteEmailScanner(proxies=proxy_list, max_workers=max_workers)
            self.log_message("✅ Сканер инициализирован успешно", "SUCCESS")
        except Exception as e:
            self.log_message(f"❌ Ошибка инициализации сканера: {e}", "ERROR")
            return
        
        # Сброс интерфейса
        self.is_scanning = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_var.set(0)
        self.start_time = datetime.now()
        self.log_counter = 0
        
        # Сброс статистики
        for var in self.stats_vars.values():
            var.set("0")
        
        # Логирование начала
        self.log_message("=" * 50)
        self.log_message("🚀 ЗАПУСК СКАНИРОВАНИЯ")
        self.log_message("=" * 50)
        if search_query:
            self.log_message(f"🔍 Поисковый запрос: {search_query}")
        self.log_message(f"📊 Целевое количество сайтов: {total_sites}")
        self.log_message(f"⚡ Количество потоков: {max_workers}")
        self.log_message(f"🔗 Режим прокси: {'Включен' if proxy_list else 'Выключен'}")
        if not SCANNER_AVAILABLE:
            self.log_message("🔧 РЕЖИМ ТЕСТИРОВАНИЯ: Используется заглушка сканера", "WARNING")
        
        # Запуск потока сканирования
        self.scan_thread = threading.Thread(
            target=self.run_scan,
            args=(total_sites, search_query),
            daemon=True
        )
        self.scan_thread.start()
        
        # Запуск мониторинга прогресса
        self.monitor_progress()
        
        # Запуск таймера
        self.update_time()
    
    def run_scan(self, total_sites, search_query):
        """Запуск сканирования в отдельном потоке"""
        try:
            self.scanner.run_mass_scan(total_sites=total_sites, search_query=search_query)
        except Exception as e:
            self.log_message(f"❌ Критическая ошибка при сканировании: {e}", "ERROR")
        finally:
            self.is_scanning = False
    
    def monitor_progress(self):
        """Мониторинг прогресса сканирования"""
        if not self.is_scanning and self.scanner:
            # Сканирование завершено
            self.scanning_finished()
            return
        
        if self.scanner:
            try:
                # Обновление статистики
                stats = self.scanner.stats
                self.stats_vars['sites_checked'].set(str(stats['sites_processed']))
                self.stats_vars['sites_with_emails'].set(str(stats['sites_with_emails']))
                self.stats_vars['emails_found'].set(str(stats['total_emails_found']))
                self.stats_vars['unique_emails'].set(str(len(self.scanner.found_emails)))
                self.stats_vars['search_sites'].set(str(stats.get('search_sites_found', 0)))
                
                # Обновление прогресса
                total_sites = int(self.sites_var.get())
                if total_sites > 0:
                    progress = (stats['sites_processed'] / total_sites) * 100
                    self.progress_var.set(min(progress, 100))
                
                # Обновление статуса
                self.status_var.set(f"Обработано: {stats['sites_processed']}/{total_sites} | Найдено email: {len(self.scanner.found_emails)}")
            except Exception as e:
                print(f"Ошибка обновления статистики: {e}")
        
        # Продолжаем мониторинг
        if self.is_scanning:
            self.root.after(1000, self.monitor_progress)
    
    def update_time(self):
        """Обновление времени работы"""
        if self.is_scanning and self.start_time:
            elapsed = datetime.now() - self.start_time
            hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.time_var.set(f"Время: {hours:02d}:{minutes:02d}:{seconds:02d}")
            self.update_time_id = self.root.after(1000, self.update_time)
        else:
            if self.update_time_id:
                self.root.after_cancel(self.update_time_id)
    
    def stop_scan(self):
        """Остановка сканирования"""
        if self.scanner and self.is_scanning:
            self.scanner.stop_event.set()
            self.is_scanning = False
            self.log_message("⏹️ Сканирование остановлено пользователем", "WARNING")
            self.status_var.set("Сканирование остановлено")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
    
    def scanning_finished(self):
        """Завершение сканирования"""
        self.is_scanning = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        if self.scanner:
            # Вывод финальной статистики
            self.log_message("=" * 50)
            self.log_message("📊 СКАНИРОВАНИЕ ЗАВЕРШЕНО", "SUCCESS")
            self.log_message("=" * 50)
            self.log_message(f"✅ Всего проверено сайтов: {self.scanner.stats['total_sites_checked']}")
            self.log_message(f"🎯 Сайтов с email: {self.scanner.stats['sites_with_emails']}")
            self.log_message(f"📧 Всего найдено email: {self.scanner.stats['total_emails_found']}")
            self.log_message(f"🔑 Уникальных email: {len(self.scanner.found_emails)}")
            
            # Показ найденных email
            if self.scanner.found_emails:
                self.log_message("\n📬 Найденные email адреса:", "SUCCESS")
                for email in sorted(self.scanner.found_emails):
                    self.log_message(f"  📧 {email}")
            else:
                self.log_message("❌ Email не найдены", "WARNING")
            
            self.status_var.set("Сканирование завершено")
            
            # Авто-экспорт email
            self.auto_export_emails()
        
        # Сохранение логов
        self.save_logs()
    
    def export_emails(self):
        """Экспорт email в файл"""
        if not self.scanner or not self.scanner.found_emails:
            messagebox.showinfo("Информация", "Нет email для экспорта")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Сохранить email"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    for email in sorted(self.scanner.found_emails):
                        f.write(f"{email}\n")
                self.log_message(f"✅ Email экспортированы в файл: {filename}", "SUCCESS")
                messagebox.showinfo("Успех", f"Email успешно экспортированы в файл:\n{filename}")
            except Exception as e:
                self.log_message(f"❌ Ошибка экспорта: {e}", "ERROR")
                messagebox.showerror("Ошибка", f"Не удалось экспортировать email: {e}")
    
    def auto_export_emails(self):
        """Автоматический экспорт email после завершения сканирования"""
        if self.scanner and self.scanner.found_emails:
            try:
                # Сохранение в файл по умолчанию
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"found_emails_{timestamp}.txt"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    for email in sorted(self.scanner.found_emails):
                        f.write(f"{email}\n")
                
                self.log_message(f"✅ Email автоматически сохранены в: {filename}", "SUCCESS")
                
            except Exception as e:
                self.log_message(f"❌ Ошибка авто-сохранения email: {e}", "ERROR")
    
    def on_closing(self):
        """Действия при закрытии приложения"""
        if self.is_scanning:
            if messagebox.askokcancel("Выход", "Сканирование еще выполняется. Вы уверены, что хотите выйти?"):
                self.stop_scan()
                # Даем время для корректного завершения
                self.root.after(1000, self.root.destroy)
        else:
            self.root.destroy()

def main():
    """Запуск приложения"""
    root = tk.Tk()
    app = EmailScannerGUI(root)
    
    # Обработка закрытия окна
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Центрирование окна
    root.update_idletasks()
    x = (root.winfo_screenwidth() - root.winfo_reqwidth()) // 2
    y = (root.winfo_screenheight() - root.winfo_reqheight()) // 2
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()