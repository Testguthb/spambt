import logging
import os
from handlers import *
from config import (BOT_TOKEN, LOG_LEVEL, LOG_FORMAT, LOG_FILE, LOG_ENCODING, conn, bot, API_ID, API_HASH, user_clients, scheduler, BOT_NAME, DATABASE_NAME)
from func.db_func import create_table, delete_table
from func.func import is_night_time
from telethon import TelegramClient
from telethon.sessions import StringSession

# Налаштувати логування тільки для ERROR і вище
logging.basicConfig(level=logging.ERROR)
# або
logger = logging.getLogger()
logger.setLevel(logging.ERROR)

# Функция для загрузки сессий из базы данных при запуске бота
async def load_sessions():
    cursor = conn.cursor()
    try:
        # Получаем все сессии из базы данных
        sessions = cursor.execute("SELECT user_id, session_string FROM sessions").fetchall()
        logging.info(f"Загружаю {len(sessions)} сессий из базы данных для {BOT_NAME}")
        
        # Создаем директорию для хранения файлов сессий, если её нет (отдельную для каждого бота)
        sessions_dir = f".sessions_{BOT_NAME}"
        os.makedirs(sessions_dir, exist_ok=True)
        
        for user_id, session_string in sessions:
            try:
                # Создаем файл сессии для каждого пользователя в отдельной директории
                session_file = f"{sessions_dir}/user_{user_id}.session"
                
                # Инициализируем клиент с StringSession и сохраняем его в файл
                client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
                await client.connect()
                
                # Проверяем авторизацию
                if await client.is_user_authorized():
                    logging.info(f"[{BOT_NAME}] Сессия для пользователя {user_id} успешно загружена")
                else:
                    logging.warning(f"[{BOT_NAME}] Сессия для пользователя {user_id} не авторизована")
                
                # Отключаем клиент
                await client.disconnect()
            except Exception as e:
                logging.error(f"[{BOT_NAME}] Ошибка при загрузке сессии для пользователя {user_id}: {e}")
    except Exception as e:
        logging.error(f"[{BOT_NAME}] Ошибка при загрузке сессий: {e}")
    finally:
        cursor.close()

pause_state = {"is_paused": False} 

async def check_and_manage_pause():
    """
    Эта функция проверяет время и ставит на паузу или возобновляет
    все заданные рассылки.
    """
    now_is_night = is_night_time()

    if now_is_night and not pause_state["is_paused"]:
        logging.warning("Настала ночь. Ставлю на паузу все рассылки.")
        for job in scheduler.get_jobs():
            if job.id.startswith("broadcast"):
                scheduler.pause_job(job.id)
        pause_state["is_paused"] = True

    elif not now_is_night and pause_state["is_paused"]:
        logging.warning("Настало утро. Возобновляю все рассылки.")
        for job in scheduler.get_jobs():
            if job.id.startswith("broadcast"):
                scheduler.resume_job(job.id)
        pause_state["is_paused"] = False

if __name__ == "__main__":
    print(f"🚀 Запускаю {BOT_NAME}...")
    print(f"📊 Использую базу данных: {DATABASE_NAME}")
    
    create_table()
    delete_table()
    
    # Добавляем нашу задачу-контроллер в планировщик
    async def main():
        
        await bot.start(bot_token=BOT_TOKEN)
        
        scheduler.add_job(check_and_manage_pause, 'interval', minutes=1, id='pause_controller')

        if not scheduler.running:
            scheduler.start()
        
        await load_sessions()
        
        # Используем лишь один способ вывода сообщения о запуске
        logging.info(f"🚀 [{BOT_NAME}] Бот запущен...")
        
        await bot.run_until_disconnected()
    
    bot.loop.run_until_complete(main())
