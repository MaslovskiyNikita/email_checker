# build.py (обновленная версия)
import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

def get_platform_config():
    """Конфигурация для разных платформ"""
    if platform.system() == "Windows":
        return {
            'exe_name': 'EmailFinder.exe',
            'separator': ';',
            'python_cmd': 'python'
        }
    else:
        return {
            'exe_name': 'EmailFinder',
            'separator': ':',
            'python_cmd': sys.executable
        }

def check_wine():
    """Проверка наличия Wine на Linux"""
    if platform.system() != "Windows":
        try:
            subprocess.run(['wine', '--version'], capture_output=True, check=True)
            return True
        except:
            return False
    return True

def build_exe():
    """Сборка EXE файла"""
    print("🚀 Начинаем сборку EXE файла...")
    
    config = get_platform_config()
    
    # Создаем временные папки
    build_dir = "build"
    dist_dir = "dist"
    
    # Очищаем предыдущие сборки
    for dir_name in [build_dir, dist_dir]:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"🧹 Очищена папка: {dir_name}")
    
    # Команда PyInstaller
    cmd = [
        config['python_cmd'], "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        f"--name=EmailFinder",
        f"--add-data=email_checker{config['separator']}email_checker",
        "--hidden-import=tkinter",
        "--hidden-import=requests",
        "--hidden-import=bs4",
        "--hidden-import=urllib3",
        "--hidden-import=concurrent.futures",
        "--hidden-import=queue",
        "--hidden-import=logging",
        "--hidden-import=json",
        "--hidden-import=re",
        "--hidden-import=time",
        "--hidden-import=datetime",
        "--hidden-import=random",
        "--hidden-import=socket",
        "--hidden-import=threading",
        "--hidden-import=os",
        "--hidden-import=sys",
        "--hidden-import=urllib.parse",
        "--clean",
        "main.py"
    ]
    
    # Если на Linux и есть Wine, добавляем wine в начало команды
    if platform.system() != "Windows" and check_wine():
        print("🔍 Обнаружен Wine, пытаемся собрать Windows EXE...")
        cmd = ['wine'] + cmd
        config['exe_name'] = 'EmailFinder.exe'
    
    try:
        print("🔨 Запуск PyInstaller...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Сборка завершена успешно!")
        
        # Проверяем наличие EXE файла
        exe_path = os.path.join(dist_dir, config['exe_name'])
        
        if os.path.exists(exe_path):
            print(f"🎉 EXE файл создан: {exe_path}")
            print(f"📏 Размер файла: {os.path.getsize(exe_path) / (1024*1024):.2f} MB")
            
            # Создаем папку для распространения
            release_dir = "release"
            if not os.path.exists(release_dir):
                os.makedirs(release_dir)
            
            # Копируем EXE файл
            shutil.copy2(exe_path, os.path.join(release_dir, config['exe_name']))
            
            # Создаем README для пользователя
            create_readme(release_dir)
            
            print(f"📦 Файлы для распространения в папке: {release_dir}")
            
        else:
            print("❌ EXE файл не найден!")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка сборки: {e}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()

def create_readme(release_dir):
    """Создание файла README"""
    readme_content = """# Email Finder - Инструкция

## Установка
1. Скачайте EmailFinder.exe
2. Запустите файл
3. Программа автоматически установит зависимости

## Использование
- Введите поисковый запрос
- Выберите количество сайтов
- Нажмите "Начать сканирование"

## Примечание
При первом запуске может потребоваться подключение к интернету.
"""
    
    with open(os.path.join(release_dir, "README.txt"), 'w', encoding='utf-8') as f:
        f.write(readme_content)

if __name__ == "__main__":
    build_exe()