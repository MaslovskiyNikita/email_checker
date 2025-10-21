import os
import sys
import gc

# Принудительная сборка мусора перед импортами
gc.collect()

# Оптимизация памяти
if hasattr(sys, 'setdlopenflags'):
    try:
        import ctypes
        sys.setdlopenflags(sys.getdlopenflags() | ctypes.RTLD_GLOBAL)
    except:
        pass

# Отключаем буферизацию
os.environ['PYTHONUNBUFFERED'] = '1'

# Добавляем путь к модулям
script_dir = os.path.dirname(os.path.abspath(__file__))
email_finder_path = os.path.join(script_dir, 'email_checker')
if email_finder_path not in sys.path:
    sys.path.insert(0, email_finder_path)

def check_dependencies():
    """Проверка наличия необходимых библиотек"""
    required_packages = ['requests', 'bs4', 'urllib3']
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'bs4':
                __import__('bs4')
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def main():
    """Основная функция запуска"""
    try:
        # Проверяем зависимости
        missing = check_dependencies()
        
        if missing:
            print(f"Отсутствующие пакеты: {missing}")
            # В собранной версии это не должно происходить
            return
        
        # Запускаем основной интерфейс
        try:
            from email_checker.interface import main as gui_main
            gui_main()
        except ImportError as e:
            # Пробуем альтернативный путь
            try:
                from interface import main as gui_main
                gui_main()
            except ImportError:
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror("Ошибка", f"Не удалось найти модули: {e}")
                
    except Exception as e:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Критическая ошибка", f"Не удалось запустить приложение: {e}")

if __name__ == "__main__":
    main()