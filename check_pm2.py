import os
import sys
import platform
import logging
import sqlite3
import json

# Настраиваем логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("pm2_check.log", mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger("PM2Checker")

def check_system():
    """Проверяет системную информацию"""
    logger.info("=" * 50)
    logger.info("СИСТЕМНАЯ ИНФОРМАЦИЯ")
    logger.info("=" * 50)
    
    logger.info(f"Операционная система: {platform.system()} {platform.release()}")
    logger.info(f"Версия Python: {sys.version}")
    logger.info(f"Текущая директория: {os.getcwd()}")
    logger.info(f"Переменные окружения PATH: {os.environ.get('PATH', 'Не найдено')}")
    
    # Проверяем наличие PM2
    try:
        import subprocess
        pm2_version = subprocess.check_output(["pm2", "--version"], text=True).strip()
        logger.info(f"Версия PM2: {pm2_version}")
    except Exception as e:
        logger.error(f"Ошибка при проверке версии PM2: {e}")
    
    logger.info("=" * 50)

def check_files():
    """Проверяет наличие необходимых файлов"""
    logger.info("=" * 50)
    logger.info("ПРОВЕРКА ФАЙЛОВ")
    logger.info("=" * 50)
    
    required_files = [
        "main.py",
        "config.py",
        "requirements.txt",
        ".env"
    ]
    
    for file in required_files:
        if os.path.exists(file):
            logger.info(f"✅ Файл {file} найден")
            
            # Проверяем права доступа
            try:
                with open(file, 'r') as f:
                    f.read(1)
                logger.info(f"   - Права на чтение: ОК")
            except Exception as e:
                logger.error(f"   - Ошибка при чтении файла {file}: {e}")
        else:
            logger.error(f"❌ Файл {file} не найден")
    
    # Проверяем директории
    directories = [
        "handlers",
        "func",
        ".sessions"
    ]
    
    for directory in directories:
        if os.path.isdir(directory):
            logger.info(f"✅ Директория {directory} найдена")
            
            # Проверяем содержимое
            try:
                files = os.listdir(directory)
                logger.info(f"   - Содержит {len(files)} файлов/директорий")
            except Exception as e:
                logger.error(f"   - Ошибка при чтении директории {directory}: {e}")
        else:
            logger.error(f"❌ Директория {directory} не найдена")
    
    logger.info("=" * 50)

def check_database():
    """Проверяет базу данных"""
    logger.info("=" * 50)
    logger.info("ПРОВЕРКА БАЗЫ ДАННЫХ")
    logger.info("=" * 50)
    
    db_file = "sessions.db"
    
    if not os.path.exists(db_file):
        logger.error(f"❌ База данных {db_file} не найдена")
        return
    
    logger.info(f"✅ База данных {db_file} найдена")
    
    try:
        conn = sqlite3.connect(db_file, timeout=30.0)
        cursor = conn.cursor()
        
        # Проверяем таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        logger.info(f"Найдено {len(tables)} таблиц:")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            logger.info(f"   - {table_name}: {count} записей")
        
        conn.close()
        logger.info("✅ База данных проверена успешно")
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке базы данных: {e}")
    
    logger.info("=" * 50)

def check_pm2_config():
    """Проверяет конфигурацию PM2"""
    logger.info("=" * 50)
    logger.info("ПРОВЕРКА КОНФИГУРАЦИИ PM2")
    logger.info("=" * 50)
    
    # Проверяем наличие файла ecosystem.config.js или ecosystem.config.json
    pm2_configs = [
        "ecosystem.config.js",
        "ecosystem.config.json",
        "pm2.config.js",
        "pm2.config.json",
        "pm2.json"
    ]
    
    found_config = False
    
    for config_file in pm2_configs:
        if os.path.exists(config_file):
            logger.info(f"✅ Найден файл конфигурации PM2: {config_file}")
            found_config = True
            
            # Пытаемся прочитать конфигурацию
            try:
                if config_file.endswith('.json'):
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    logger.info(f"Конфигурация PM2: {json.dumps(config, indent=2)}")
                else:
                    logger.info(f"Файл конфигурации в формате JS, не можем прочитать содержимое")
            except Exception as e:
                logger.error(f"Ошибка при чтении файла конфигурации: {e}")
    
    if not found_config:
        logger.warning("⚠️ Файл конфигурации PM2 не найден")
        
        # Предлагаем создать конфигурацию
        logger.info("Рекомендуется создать файл ecosystem.config.js с следующим содержимым:")
        
        example_config = {
            "apps": [
                {
                    "name": "bot",
                    "script": "main.py",
                    "interpreter": "python3",
                    "instances": 1,
                    "autorestart": True,
                    "watch": False,
                    "max_memory_restart": "200M",
                    "env": {
                        "NODE_ENV": "production"
                    }
                }
            ]
        }
        
        logger.info(json.dumps(example_config, indent=2))
    
    logger.info("=" * 50)

def check_environment():
    """Проверяет переменные окружения"""
    logger.info("=" * 50)
    logger.info("ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ")
    logger.info("=" * 50)
    
    # Проверяем наличие файла .env
    if os.path.exists(".env"):
        logger.info("✅ Файл .env найден")
        
        # Пытаемся прочитать содержимое
        try:
            with open(".env", 'r') as f:
                env_content = f.read()
            
            # Проверяем наличие необходимых переменных
            required_vars = ["API_ID", "API_HASH", "BOT_TOKEN", "ADMIN_ID_LIST"]
            
            for var in required_vars:
                if var in env_content:
                    logger.info(f"✅ Переменная {var} найдена в .env")
                else:
                    logger.error(f"❌ Переменная {var} не найдена в .env")
        except Exception as e:
            logger.error(f"Ошибка при чтении файла .env: {e}")
    else:
        logger.error("❌ Файл .env не найден")
    
    logger.info("=" * 50)

def check_dependencies():
    """Проверяет зависимости"""
    logger.info("=" * 50)
    logger.info("ПРОВЕРКА ЗАВИСИМОСТЕЙ")
    logger.info("=" * 50)
    
    try:
        import telethon
        logger.info(f"✅ Telethon установлен, версия: {telethon.__version__}")
    except ImportError:
        logger.error("❌ Telethon не установлен")
    
    try:
        import apscheduler
        logger.info(f"✅ APScheduler установлен, версия: {apscheduler.__version__}")
    except ImportError:
        logger.error("❌ APScheduler не установлен")
    
    try:
        from decouple import config
        logger.info("✅ python-decouple установлен")
    except ImportError:
        logger.error("❌ python-decouple не установлен")
    
    logger.info("=" * 50)

def main():
    """Запускает все проверки"""
    logger.info("=" * 50)
    logger.info("НАЧАЛО ПРОВЕРКИ PM2 И ОКРУЖЕНИЯ")
    logger.info("=" * 50)
    
    check_system()
    check_files()
    check_database()
    check_pm2_config()
    check_environment()
    check_dependencies()
    
    logger.info("=" * 50)
    logger.info("ПРОВЕРКА ЗАВЕРШЕНА")
    logger.info("=" * 50)
    
    logger.info("""
РЕКОМЕНДАЦИИ:
1. Убедитесь, что у вас установлен PM2: npm install pm2 -g
2. Создайте файл ecosystem.config.js с правильной конфигурацией
3. Запустите бота через PM2: pm2 start ecosystem.config.js
4. Проверьте логи: pm2 logs
5. Если бот падает, проверьте логи в файле pm2_debug.log
""")

if __name__ == "__main__":
    main() 