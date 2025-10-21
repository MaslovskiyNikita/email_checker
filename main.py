# main.py
import os
import sys
import tkinter as tk
from tkinter import messagebox
import subprocess

import os
import sys
import psutil

# Оптимизация памяти
try:
    import psutil
    process = psutil.Process()
    if hasattr(process, 'nice'):
        process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
except:
    pass

# Увеличиваем лимит рекурсии если нужно
sys.setrecursionlimit(5000)

# Отключаем буферизацию вывода для лучшего управления памятью
os.environ['PYTHONUNBUFFERED'] = '1'
def resource_path(relative_path):
    """Получение абсолютного пути к ресурсу для PyInstaller"""
    try:
        # PyInstaller создает временную папку и хранит путь в _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def check_dependencies():
    """Проверка наличия необходимых библиотек"""
    required_packages = ['requests', 'beautifulsoup4', 'urllib3']
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'beautifulsoup4':
                __import__('bs4')
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def install_missing_packages(missing_packages):
    """Установка отсутствующих пакетов"""
    for package in missing_packages:
        try:
            if package == 'beautifulsoup4':
                subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
            else:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ Установлен пакет: {package}")
        except Exception as e:
            print(f"❌ Ошибка установки {package}: {e}")
            return False
    return True

def main():
    """Основная функция запуска"""
    try:
        # Проверяем зависимости
        missing = check_dependencies()
        
        if missing:
            print(f"Обнаружены отсутствующие пакеты: {missing}")
            if not install_missing_packages(missing):
                messagebox.showerror("Ошибка", f"Не удалось установить пакеты: {missing}")
                return
        
        # Добавляем путь к модулям в sys.path
        email_finder_path = resource_path('email_finder_bot')
        if email_finder_path not in sys.path:
            sys.path.insert(0, email_finder_path)
        
        # Запускаем основной интерфейс
        try:
            from email_checker.interface import main as gui_main
            gui_main()
        except ImportError as e:
            # Пробуем альтернативный путь
            try:
                # Если мы в распакованном PyInstaller
                from interface import main as gui_main
                gui_main()
            except ImportError:
                messagebox.showerror("Ошибка", f"Не удалось найти модули: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при запуске: {e}")
            
    except Exception as e:
        messagebox.showerror("Критическая ошибка", f"Не удалось запустить приложение: {e}")

if __name__ == "__main__":
    main()