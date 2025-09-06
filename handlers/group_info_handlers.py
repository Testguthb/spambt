import logging
import sqlite3
import os
import asyncio
import time
from typing import Dict, Optional

from telethon import Button, TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import Channel, Chat
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import GetFullChatRequest

from config import callback_query, API_ID, API_HASH, broadcast_all_text, scheduler, Query, bot, conn
from func.func import gid_key, broadcast_status_emoji, get_entity_by_id

# Кеш для названий групп (группа_id: {название, время_обновления})
groups_cache: Dict[str, Dict] = {}
CACHE_EXPIRE_TIME = 300  # 5 минут


def get_cached_group_title(group_username: str, group_id: int) -> Optional[str]:
    """Получает название группы из кеша, если оно не устарело"""
    cache_key = f"{group_username}_{group_id}"
    if cache_key in groups_cache:
        cached_data = groups_cache[cache_key]
        if time.time() - cached_data['timestamp'] < CACHE_EXPIRE_TIME:
            return cached_data['title']
    return None

def cache_group_title(group_username: str, group_id: int, title: str):
    """Сохраняет название группы в кеш"""
    cache_key = f"{group_username}_{group_id}"
    groups_cache[cache_key] = {
        'title': title,
        'timestamp': time.time()
    }

def cleanup_cache():
    """Очищает устаревшие записи из кеша"""
    current_time = time.time()
    expired_keys = []
    
    for cache_key, cached_data in groups_cache.items():
        if current_time - cached_data['timestamp'] > CACHE_EXPIRE_TIME:
            expired_keys.append(cache_key)
    
    for key in expired_keys:
        del groups_cache[key]
    
    logging.info(f"Очищено {len(expired_keys)} устаревших записей из кеша групп")

@bot.on(Query(data=lambda data: data.decode().startswith("listOfgroups_")))
async def handle_groups_list(event: callback_query) -> None:
    # Очищаем устаревший кеш перед обработкой
    cleanup_cache()
    
    # Проверяем, есть ли параметр страницы
    data_parts = event.data.decode().split("_")
    user_id = int(data_parts[1])
    page = int(data_parts[2]) if len(data_parts) > 2 else 0
    
    cursor = conn.cursor()
    row = cursor.execute("SELECT session_string FROM sessions WHERE user_id = ?", (user_id,)).fetchone()
    if not row:
        cursor.close()
        await event.respond("⚠ Не удалось найти аккаунт.")
        return

    session_string = row[0]
    
    # Получаем общее количество групп
    total_groups = cursor.execute("SELECT COUNT(*) FROM groups WHERE user_id = ?", (user_id,)).fetchone()[0]
    
    if total_groups == 0:
        cursor.close()
        await event.respond("У аккаунта нет групп.")
        return
    
    # Пагинация - показываем по 10 групп на страницу
    PAGE_SIZE = 10
    offset = page * PAGE_SIZE
    
    # Получаем группы для текущей страницы
    dialogs = cursor.execute(
        "SELECT group_id, group_username FROM groups WHERE user_id = ? LIMIT ? OFFSET ?", 
        (user_id, PAGE_SIZE, offset)
    ).fetchall()
    
    cursor.close()
    
    buttons = []
    groups_with_api_calls = []  # Группы, которым нужны API вызовы
    
    # Сначала проверяем кеш для всех групп
    for group_id, group_username in dialogs:
        cached_title = get_cached_group_title(group_username, group_id)
        if cached_title:
            # Используем кешированное название
            buttons.append(
                [Button.inline(f"{broadcast_status_emoji(user_id, int(group_id))} {cached_title}",
                            f"groupInfo_{user_id}_{gid_key(group_id)}".encode())]
            )
        else:
            # Добавляем в список для API вызовов
            groups_with_api_calls.append((group_id, group_username))
            # Временно добавляем кнопку с username/ID
            buttons.append(
                [Button.inline(f"{broadcast_status_emoji(user_id, int(group_id))} {group_username}",
                            f"groupInfo_{user_id}_{gid_key(group_id)}".encode())]
            )
    
    # Если есть группы без кеша, делаем API вызовы (но ограниченно)
    if groups_with_api_calls and len(groups_with_api_calls) <= 5:  # Ограничиваем API вызовы
        client = None
        try:
            client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
            await client.connect()
            
            # Обновляем кнопки для групп с API вызовами
            for i, (group_id, group_username) in enumerate(groups_with_api_calls):
                try:
                    # Получаем entity с таймаутом
                    entity = None
                    try:
                        if group_username.startswith('@'):
                            entity = await asyncio.wait_for(client.get_entity(group_username), timeout=5.0)
                        else:
                            try:
                                group_id_int = int(group_username)
                                entity = await asyncio.wait_for(get_entity_by_id(client, group_id_int), timeout=5.0)
                            except ValueError:
                                entity = await asyncio.wait_for(client.get_entity(group_username), timeout=5.0)
                    except asyncio.TimeoutError:
                        logging.warning(f"Таймаут при получении entity для группы {group_username}")
                        continue
                    except Exception as e:
                        logging.error(f"Ошибка при получении entity для группы {group_username}: {e}")
                        continue
                    
                    if entity:
                        group_title = getattr(entity, 'title', group_username)
                        # Кешируем название
                        cache_group_title(group_username, group_id, group_title)
                        
                        # Находим индекс кнопки для обновления
                        button_index = None
                        for idx, button_row in enumerate(buttons):
                            if button_row[0].data.decode().endswith(f"_{gid_key(group_id)}"):
                                button_index = idx
                                break
                        
                        if button_index is not None:
                            buttons[button_index] = [Button.inline(
                                f"{broadcast_status_emoji(user_id, int(group_id))} {group_title}",
                                f"groupInfo_{user_id}_{gid_key(group_id)}".encode()
                            )]
                    
                except Exception as e:
                    logging.error(f"Ошибка при обработке группы {group_id}: {e}")
                    continue
                    
        except Exception as e:
            logging.error(f"Ошибка при подключении к Telegram: {e}")
        finally:
            if client:
                try:
                    await client.disconnect()
                except:
                    pass
    
    # Добавляем кнопки навигации если нужно
    navigation_buttons = []
    total_pages = (total_groups + PAGE_SIZE - 1) // PAGE_SIZE
    
    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(Button.inline("⬅️ Назад", f"listOfgroups_{user_id}_{page-1}"))
        
        nav_row.append(Button.inline(f"📄 {page+1}/{total_pages}", "noop"))
        
        if page < total_pages - 1:
            nav_row.append(Button.inline("➡️ Вперед", f"listOfgroups_{user_id}_{page+1}"))
        
        navigation_buttons.append(nav_row)
    
    # Добавляем кнопку "Назад к аккаунту"
    navigation_buttons.append([Button.inline("◀️ Назад к аккаунту", f"account_info_{user_id}")])
    
    buttons.extend(navigation_buttons)
    
    message_text = f"📋 **Список групп** (стр. {page+1}/{total_pages}):\n"
    if groups_with_api_calls and len(groups_with_api_calls) > 5:
        message_text += "\n💡 *Некоторые названия групп загружаются в фоновом режиме*"
    
    await event.respond(message_text, buttons=buttons)


# Обробник для кнопки-заглушки (показ номера страницы)
@bot.on(Query(data=b"noop"))
async def handle_noop(event: callback_query) -> None:
    await event.answer()


# ---------- меню конкретной группы ----------
@bot.on(Query(data=lambda d: d.decode().startswith("groupInfo_")))
async def group_info(event: callback_query) -> None:
    data = event.data.decode()
    user_id, group_id = map(int, data.split("_")[1:])
    cursor = conn.cursor()
    
    # Проверяем наличие сессии
    session_row = cursor.execute("SELECT session_string FROM sessions WHERE user_id = ?", (user_id,)).fetchone()
    if not session_row:
        await event.respond("⚠ Ошибка: не найдена сессия для этого аккаунта.")
        cursor.close()
        return
        
    session_string = session_row[0]
    session = StringSession(session_string)
    client = TelegramClient(session, API_ID, API_HASH)
    
    # Проверяем наличие группы
    group_row = cursor.execute("SELECT group_username FROM groups WHERE user_id = ? AND group_id = ?", 
                             (user_id, group_id)).fetchone()
    if not group_row:
        await event.respond("⚠ Ошибка: не найдена группа.")
        cursor.close()
        return
        
    group_username = group_row[0]
    
    try:
        await client.connect()
        
        try:
            ent = await client.get_entity(group_row[0])
        except Exception as entity_error:
            if "Cannot find any entity corresponding to" in str(entity_error):
                try:
                    # Преобразуем username в ID, если это возможно
                    try:
                        group_id_int = int(group_row[0])
                        ent = await get_entity_by_id(client, group_id_int)
                        if not ent:
                            await event.respond(f"⚠ Ошибка: не удалось получить информацию о группе {group_username}.")
                            await client.disconnect()
                            cursor.close()
                            return
                    except ValueError:
                        # Если username не является числом, сообщаем об ошибке
                        await event.respond(f"⚠ Ошибка: не удалось получить информацию о группе {group_username}.")
                        await client.disconnect()
                        cursor.close()
                        return
                except Exception as alt_error:
                    logging.error(f"Ошибка при альтернативном получении Entity: {alt_error}")
                    await event.respond(f"⚠ Ошибка: не удалось получить информацию о группе {group_username}.")
                    await client.disconnect()
                    cursor.close()
                    return
            else:
                await event.respond(f"⚠ Ошибка: не удалось получить информацию о группе {group_username}.")
                await client.disconnect()
                cursor.close()
                return
        
        # Получаем информацию о рассылке
        broadcast_row = cursor.execute("""
            SELECT broadcast_text, interval_minutes, is_active, photo_url 
            FROM broadcasts 
            WHERE user_id = ? AND group_id = ?
        """, (user_id, gid_key(group_id))).fetchone()
        
        broadcast_text = broadcast_row[0] if broadcast_row and broadcast_row[0] else "Не установлен"
        interval = f"{broadcast_row[1]} мин." if broadcast_row and broadcast_row[1] else "Не установлен"
        status = broadcast_status_emoji(user_id, group_id)
        
        # Получаем информацию о фото
        photo_url = broadcast_row[3] if broadcast_row and len(broadcast_row) > 3 and broadcast_row[3] else None
        photo_info = f"Фото: {os.path.basename(photo_url)}" if photo_url else "Фото отсутствует"
        
        # Формируем информацию о группе
        group_title = getattr(ent, 'title', group_username)
        group_username_display = f"@{ent.username}" if hasattr(ent, 'username') and ent.username else "Нет юзернейма"
        
        # Получаем количество участников с обработкой None
        members_count = getattr(ent, 'participants_count', None)
        if members_count is None:
            try:
                # Для супергрупп и каналов пытаемся получить количество участников через полную информацию
                if isinstance(ent, Channel):
                    full_channel = await client(GetFullChannelRequest(ent))
                    members_count = getattr(full_channel.full_chat, 'participants_count', "Неизвестно")
                elif isinstance(ent, Chat):
                    full_chat = await client(GetFullChatRequest(ent.id))
                    members_count = getattr(full_chat.full_chat, 'participants_count', "Неизвестно")
                else:
                    members_count = "Неизвестно"
            except Exception as e:
                logging.error(f"Не удалось получить количество участников: {e}")
                members_count = "Неизвестно"
        
        if isinstance(ent, Channel):
            group_type = "Канал" if ent.broadcast else "Супергруппа"
        elif isinstance(ent, Chat):
            group_type = "Группа"
        else:
            group_type = "Неизвестный тип"
        
        info_text = f"""
📊 **Информация о группе**

👥 **Название**: {group_title}
🔖 **Юзернейм**: {group_username_display}
👤 **Участников**: {members_count}
📝 **Тип**: {group_type}
🆔 **ID**: {group_id}

📬 **Статус рассылки**: {status}
⏱ **Интервал**: {interval}
📝 **Текст рассылки**: 
{broadcast_text[:100] + '...' if len(broadcast_text) > 100 else broadcast_text}
🖼 **{photo_info}**
"""
        
        # Кнопки для управления рассылкой
        buttons = [
            [Button.inline(f"📝 Текст и Интервал рассылки", f"BroadcastTextInterval_{user_id}_{group_id}".encode())],
            [Button.inline(f"▶️ Начать/возобновить рассылку", f"StartResumeBroadcast_{user_id}_{group_id}".encode())],
            [Button.inline(f"⏹ Остановить рассылку", f"StopAccountBroadcast_{user_id}_{group_id}".encode())],
            [Button.inline(f"❌ Удалить группу", f"DeleteGroup_{user_id}_{group_id}".encode())],
            [Button.inline(f"◀️ Назад к списку групп", f"groups_{user_id}".encode())]
        ]
        
        await event.respond(info_text, buttons=buttons)
        
    except Exception as e:
        logging.error(f"Ошибка при получении информации о группе: {e}")
        await event.respond(f"⚠ Ошибка при получении информации о группе: {str(e)}")
    finally:
        await client.disconnect()
        cursor.close()
