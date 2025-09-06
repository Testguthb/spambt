import logging
from typing import List, Optional, Union

from telethon import Button, TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import Channel, Chat, DialogFilter

from config import callback_query, API_ID, API_HASH, Query, bot, conn, processed_callbacks
from func.func import broadcast_status_emoji, gid_key, get_entity_by_id


@bot.on(Query(data=lambda d: d.decode().startswith("account_")))
async def account_menu(event: callback_query) -> None:
    """Обрабатывает нажатие кнопки "Назад" в списке групп и возвращает к меню аккаунта."""
    # Получаем уникальный идентификатор для этого callback
    callback_id = f"{event.sender_id}:{event.query.msg_id}"
    
    # Проверяем, был ли уже обработан этот callback
    if callback_id in processed_callbacks:
        # Этот callback уже был обработан, отвечаем на событие без отправки нового сообщения
        await event.answer("Уже обработано")
        return
        
    # Отмечаем callback как обработанный
    processed_callbacks[callback_id] = True
    
    data = event.data.decode()
    parts = data.split("_")
    
    # Проверяем формат данных
    if len(parts) < 2:
        await event.respond("⚠ Ошибка: неверный формат данных")
        return
        
    # Проверяем, есть ли "info" в callback data
    if parts[1] == "info":
        # Формат account_info_user_id
        if len(parts) < 3:
            await event.respond("⚠ Ошибка: неверный формат данных")
            return
        try:
            user_id = int(parts[2])
        except ValueError:
            await event.respond("⚠ Ошибка: неверный ID пользователя")
            return
    else:
        # Формат account_user_id
        try:
            user_id = int(parts[1])
        except ValueError:
            await event.respond("⚠ Ошибка: неверный ID пользователя")
            return
    
    # Формируем кнопки для меню аккаунта
    buttons = [
        [Button.inline("📋 Список групп", f"groups_{user_id}".encode())],
        [Button.inline("📢 Запустить рассылку во все группы", f"broadcastAll_{user_id}".encode())],
        [Button.inline("❌ Остановить общую рассылку", f"StopBroadcastAll_{user_id}".encode())],
        [Button.inline("◀️ Назад", b"my_accounts")]
    ]
    
    # Отправляем меню аккаунта
    await event.respond(f"📱 **Меню аккаунта**\n\nВыберите действие:", buttons=buttons)


@bot.on(Query(data=b"my_groups"))
async def my_groups(event: callback_query) -> None:
    cursor = conn.cursor()
    cursor.execute("SELECT group_id, group_username FROM groups")
    groups = cursor.fetchall()
    cursor.close()
    message = "❌ У вас нет добавленных групп."
    buttons = []
    if groups:
        message = "📑 **Список добавленных групп:**\n"
        buttons[0].append(Button.inline("➕ Добавить все аккаунты в эти группы", b"add_all_accounts_to_groups"))
        buttons.append([Button.inline("❌ Удалить группу", b"delete_group")])
        for group in groups:
            message += f"{group[1]}\n"
    await event.respond(message, buttons=buttons)


@bot.on(Query(data=b"add_all_accounts_to_groups"))
async def add_all_accounts_to_groups(event: callback_query) -> None:
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, session_string FROM sessions")
    accounts = cursor.fetchall()

    cursor.execute("SELECT group_id, group_username FROM groups")
    groups = cursor.fetchall()
    if not accounts:
        await event.respond("❌ Нет добавленных аккаунтов.")
        return

    if not groups:
        await event.respond("❌ Нет добавленных групп.")
        return

    for account in accounts:
        session = StringSession(account[1])
        client = TelegramClient(session, API_ID, API_HASH)
        await client.connect()
        try:
            for group in groups:
                try:
                    await client(JoinChannelRequest(group[1]))
                except Exception as e:
                    logging.error(f"Ошибка {e}")
                cursor.execute("""INSERT OR IGNORE INTO groups 
                                        (user_id, group_id, group_username) 
                                        VALUES (?, ?, ?)""", (account[0], group[0], group[1]))
                logging.info(f"Добавляем в базу данных группу ({account[0], group[0], group[1]})")
        except Exception as e:
            await event.respond(f"⚠ Ошибка при добавлении аккаунта: {e}")
        finally:
            await client.disconnect()
    group_list = "\n".join([f"📌 {group[1]}" for group in groups])
    await event.respond(f"✅ Аккаунты успешно добавлены в следующие группы:\n{group_list}")
    conn.commit()
    cursor.close()


@bot.on(Query(data=lambda event: event.decode().startswith("add_all_groups_")))
async def add_all_accounts_to_groups(event: callback_query) -> None:
    data: str = event.data.decode()
    user_id = int(data.split("_")[3])
    cursor = conn.cursor()
    cursor.execute("SELECT session_string FROM sessions WHERE user_id = ?", (user_id, ))
    accounts = cursor.fetchall()
    if not accounts:
        await event.respond("❌ Нет добавленных аккаунтов.")
        return
    msg = ["✅ Добавленные группы:\n"]
    num = 1
    session = StringSession(accounts[0][0])
    client = TelegramClient(session, API_ID, API_HASH)
    await client.connect()
    cursor.execute("DELETE FROM groups WHERE user_id = ?", (user_id,))
    conn.commit()
    
    # Створюємо множини для відстеження унікальних груп
    added_group_ids = set()
    added_group_names = set()  # Додаємо відстеження за назвами
    
    # Спочатку збираємо всі діалоги
    all_dialogs = await client.get_dialogs()
    
    # Сортуємо їх: спочатку канали (з username), потім групи, потім приватні групи
    sorted_dialogs = sorted(all_dialogs, key=lambda d: (
        not isinstance(d.entity, Channel),  # Спочатку канали
        not (isinstance(d.entity, Channel) and d.entity.username),  # Потім з username
        d.name  # Потім за назвою
    ))
    
    for group in sorted_dialogs:
        ent = group.entity
        logging.info(f"Аналізуємо групу: {group.name}, тип: {type(ent)}")
        
        # Пропускаємо, якщо це не група або канал
        if not isinstance(ent, (Channel, Chat)):
            continue
            
        # Пропускаємо, якщо це приватний чат або бот
        if hasattr(ent, 'bot') and ent.bot:
            continue
            
        # Пропускаємо, якщо це канал-вітрина (не мегагрупа)
        if isinstance(ent, Channel) and ent.broadcast and not ent.megagroup:
            continue
            
        # Пропускаємо, якщо ця група вже була додана (за ID або назвою)
        if ent.id in added_group_ids or group.name in added_group_names:
            logging.info(f"Пропускаємо дублікат: {group.name}")
            continue
            
        # Додаємо ID та назву до множин відстеження
        added_group_ids.add(ent.id)
        added_group_names.add(group.name)
        
        # Визначаємо username або ID для збереження
        if isinstance(ent, Channel) and ent.username:
            group_username = f"@{ent.username}"
            cursor.execute(f"""INSERT INTO groups 
                            (group_id, group_username, user_id) 
                            VALUES (?, ?, ?)""", (ent.id, group_username, user_id))
            msg.append(f"№{num} **{group.name}** - {group_username}")
        else:
            # Для груп без username використовуємо ID
            # Зберігаємо ID як строку для приватних груп
            group_id_str = str(ent.id)
            cursor.execute(f"""INSERT INTO groups 
                            (group_id, group_username, user_id) 
                            VALUES (?, ?, ?)""", (ent.id, group_id_str, user_id))
            msg.append(f"№{num} **{group.name}** (приватна група, ID: {group_id_str})")
            
        conn.commit()
        num += 1
        
    conn.commit()
    cursor.close()
    await client.disconnect()
    await event.respond("\n".join(msg))


@bot.on(Query(data=lambda d: d.decode().startswith("groups_")))
async def groups_list(event: callback_query) -> None:
    """Отображает список групп пользователя."""
    data = event.data.decode()
    user_id = int(data.split("_")[1])
    
    cursor = conn.cursor()
    session_row = cursor.execute("SELECT session_string FROM sessions WHERE user_id = ?", (user_id,)).fetchone()
    
    if not session_row:
        await event.respond("⚠ Ошибка: не найдена сессия для этого аккаунта.")
        cursor.close()
        return
        
    session_string = session_row[0]
    client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
    
    try:
        await client.connect()
        
        # Получаем список групп из БД
        cursor.execute("SELECT group_id, group_username FROM groups WHERE user_id = ?", (user_id,))
        groups = cursor.fetchall()
        
        if not groups:
            await event.respond("📋 У вас нет добавленных групп. Добавьте группы через главное меню.")
            await client.disconnect()
            cursor.close()
            return
            
        # Формируем список групп с информацией о статусе рассылки
        group_list = []
        
        for group_id, group_username in groups:
            try:
                # Пытаемся получить entity группы
                try:
                    ent = await client.get_entity(group_username)
                except Exception as entity_error:
                    if "Cannot find any entity corresponding to" in str(entity_error):
                        try:
                            # Преобразуем username в ID, если это возможно
                            try:
                                group_id_int = int(group_username)
                                ent = await get_entity_by_id(client, group_id_int)
                                if not ent:
                                    logging.error(f"Не удалось получить entity для группы {group_username}")
                                    continue
                            except ValueError:
                                # Если username не является числом, пропускаем
                                logging.error(f"Не удалось получить entity для группы {group_username}")
                                continue
                        except Exception as alt_error:
                            logging.error(f"Ошибка при альтернативном получении Entity: {alt_error}")
                            continue
                    else:
                        logging.error(f"Ошибка при получении entity для группы {group_username}: {entity_error}")
                        continue
                
                # Получаем статус рассылки
                status = broadcast_status_emoji(user_id, group_id)
                
                # Формируем название группы для отображения
                group_name = getattr(ent, 'title', group_username)
                
                # Используем gid_key для правильной обработки ID группы
                group_list.append((gid_key(group_id), group_name, status))
            except Exception as e:
                logging.error(f"Ошибка при обработке группы {group_username}: {e}")
                continue
                
        # Формируем сообщение и кнопки
        if group_list:
            # Создаем кнопки для каждой группы
            buttons = []
            for group_id, group_name, status in group_list:
                # Используем правильный формат данных для кнопки
                data = f"groupInfo_{user_id}_{group_id}".encode()
                buttons.append([Button.inline(f"{status} {group_name}", data)])
                
            # Добавляем кнопку "Назад"
            buttons.append([Button.inline("◀️ Назад", f"account_{user_id}".encode())])
            
            await event.respond("📋 **Список ваших групп:**\n\nВыберите группу для просмотра информации:", buttons=buttons)
        else:
            await event.respond("⚠ Не удалось получить информацию о группах. Возможно, они были удалены или недоступны.")
            
    except Exception as e:
        logging.error(f"Ошибка при получении списка групп: {e}")
        await event.respond(f"⚠ Ошибка при получении списка групп: {str(e)}")
    finally:
        await client.disconnect()
        cursor.close()
