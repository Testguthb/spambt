import logging
import sqlite3
import os
import sys
from typing import Dict, Tuple, List, Optional

import telethon.events
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from decouple import config
from telethon import TelegramClient

# Определяем какой бот запускается (по умолчанию bot1)
BOT_INSTANCE = os.getenv('BOT_INSTANCE', 'bot1')

# Загружаем конфигурацию из соответствующего файла
if BOT_INSTANCE == 'bot2':
    from decouple import Config, RepositoryEnv
    env_config = Config(RepositoryEnv('.env.bot2'))
elif BOT_INSTANCE == 'bot3':
    from decouple import Config, RepositoryEnv
    env_config = Config(RepositoryEnv('.env.bot3'))
elif BOT_INSTANCE == 'bot4':
    from decouple import Config, RepositoryEnv
    env_config = Config(RepositoryEnv('.env.bot4'))
elif BOT_INSTANCE == 'bot5':
    from decouple import Config, RepositoryEnv
    env_config = Config(RepositoryEnv('.env.bot5'))
elif BOT_INSTANCE == 'bot6':
    from decouple import Config, RepositoryEnv
    env_config = Config(RepositoryEnv('.env.bot6'))
elif BOT_INSTANCE == 'bot7':
    from decouple import Config, RepositoryEnv
    env_config = Config(RepositoryEnv('.env.bot7'))
elif BOT_INSTANCE == 'bot8':
    from decouple import Config, RepositoryEnv
    env_config = Config(RepositoryEnv('.env.bot8'))
elif BOT_INSTANCE == 'bot9':
    from decouple import Config, RepositoryEnv
    env_config = Config(RepositoryEnv('.env.bot9'))
elif BOT_INSTANCE == 'bot10':
    from decouple import Config, RepositoryEnv
    env_config = Config(RepositoryEnv('.env.bot10'))
elif BOT_INSTANCE == 'bot11':
    from decouple import Config, RepositoryEnv
    env_config = Config(RepositoryEnv('.env.bot11'))
elif BOT_INSTANCE == 'bot12':
    from decouple import Config, RepositoryEnv
    env_config = Config(RepositoryEnv('.env.bot12'))
elif BOT_INSTANCE == 'bot13':
    from decouple import Config, RepositoryEnv
    env_config = Config(RepositoryEnv('.env.bot13'))
elif BOT_INSTANCE == 'bot14':
    from decouple import Config, RepositoryEnv
    env_config = Config(RepositoryEnv('.env.bot14'))
elif BOT_INSTANCE == 'bot15':
    from decouple import Config, RepositoryEnv
    env_config = Config(RepositoryEnv('.env.bot15'))
else:
    from decouple import Config, RepositoryEnv
    env_config = Config(RepositoryEnv('.env.bot1'))

# Конфиг
API_ID: int = int(env_config("API_ID"))
API_HASH: str = env_config("API_HASH")
BOT_TOKEN: str = env_config("BOT_TOKEN")
ADMIN_ID_LIST: List[int] = list(map(int, map(str.strip, env_config("ADMIN_ID_LIST").split(","))))  # <-- Вставить ID разрешенных телеграмм аккаунтов через запятую
DATABASE_NAME: str = env_config("DATABASE_NAME", default="sessions.db")
BOT_NAME: str = env_config("BOT_NAME", default="bot")

# Создаем уникальное имя для бота включая номер экземпляра
bot: TelegramClient = TelegramClient(f"{BOT_NAME}_session", API_ID, API_HASH)
conn: sqlite3.Connection = sqlite3.connect(DATABASE_NAME, timeout=30.0, check_same_thread=False)

# Логирование
LOG_FORMAT: str = f"[{BOT_NAME}] %(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL: logging.INFO = logging.INFO
LOG_FILE: Optional[str] = f"{BOT_NAME}_log.log"  # Отдельный лог для каждого бота
LOG_ENCODING: str = "utf-8"

# Аннотирование
New_Message = telethon.events.NewMessage
Query = telethon.events.CallbackQuery
callback_query = Query.Event
callback_message = New_Message.Event
__Dict_int_str = Dict[int, str]
__Dict_all_str = Dict[str, str]
__Dict_int_dict = Dict[int, dict]


phone_waiting: Dict[int, bool] = {}  # Список пользователей ожидающие подтверждения телефона

code_waiting: __Dict_int_str = {}
broadcast_all_text: __Dict_int_str = {}
user_states: __Dict_int_str = {}

password_waiting: __Dict_int_dict = {}
broadcast_all_state: __Dict_int_dict = {}
broadcast_solo_state: __Dict_int_dict = {}
broadcast_all_state_account: __Dict_int_dict = {}
user_sessions: __Dict_int_dict = {}

user_sessions_deleting: Dict[int, __Dict_all_str] = {}
user_sessions_phone: Dict[Tuple[int, int], __Dict_all_str] = {}

user_clients: Dict[int, TelegramClient] = {}
scheduler: AsyncIOScheduler = AsyncIOScheduler()

# Словарь для отслеживания обработанных callback-запросов
processed_callbacks: Dict[str, bool] = {}

# Логируем информацию о запущенном экземпляре
print(f"🤖 Загружена конфигурация для {BOT_NAME}")
print(f"📁 База данных: {DATABASE_NAME}")
print(f"🔑 API_ID: {API_ID}")
