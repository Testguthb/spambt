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
    import asyncio
    
    data: str = event.data.decode()
    user_id = int(data.split("_")[3])
    cursor = conn.cursor()
    cursor.execute("SELECT session_string FROM sessions WHERE user_id = ?", (user_id, ))
    accounts = cursor.fetchall()
    if not accounts:
        await event.respond("❌ Нет добавленных аккаунтов.")
        return
    
    # Отправляем сообщение о начале обработки
    progress_msg = await event.respond("🔄 **Обновление информации о группах...**\n\n⏳ Подключение к аккаунту...")
    
    session = StringSession(accounts[0][0])
    client = TelegramClient(session, API_ID, API_HASH)
    
    try:
        # Устанавливаем таймаут для подключения
        await asyncio.wait_for(client.connect(), timeout=15.0)
        
        # Обновляем прогресс
        await progress_msg.edit("🔄 **Обновление информации о группах...**\n\n📋 Получение списка диалогов...")
        
        # Очищаем старые группы
        cursor.execute("DELETE FROM groups WHERE user_id = ?", (user_id,))
        conn.commit()
        
        # Створюємо множини для відстеження унікальних груп
        added_group_ids = set()
        added_group_names = set()
        
        # Получаем все диалоги с таймаутом
        try:
            all_dialogs = await asyncio.wait_for(client.get_dialogs(), timeout=30.0)
        except asyncio.TimeoutError:
            await progress_msg.edit("⚠️ **Таймаут при получении диалогов**\n\nПопробуйте позже или обратитесь к администратору.")
            return
        
        # Фильтруем только группы и каналы
        valid_groups = []
        for dialog in all_dialogs:
            ent = dialog.entity
            if isinstance(ent, (Channel, Chat)):
                # Пропускаем боты
                if hasattr(ent, 'bot') and ent.bot:
                    continue
                # Пропускаем каналы-витрины (не мегагруппы)
                if isinstance(ent, Channel) and ent.broadcast and not ent.megagroup:
                    continue
                valid_groups.append(dialog)
        
        total_groups = len(valid_groups)
        
        # Обновляем прогресс
        await progress_msg.edit(f"🔄 **Обновление информации о группах...**\n\n📊 Найдено групп: {total_groups}\n⚙️ Обработка...")
        
        # Сортируем группы
        sorted_dialogs = sorted(valid_groups, key=lambda d: (
            not isinstance(d.entity, Channel),
            not (isinstance(d.entity, Channel) and d.entity.username),
            d.name
        ))
        
        # Обрабатываем группы батчами для лучшей производительности
        batch_size = 50  # Обрабатываем по 50 групп за раз
        processed_count = 0
        groups_to_insert = []  # Для батчинга INSERT операций
        
        for i, group in enumerate(sorted_dialogs):
            ent = group.entity
            
            # Пропускаем дубликаты
            if ent.id in added_group_ids or group.name in added_group_names:
                continue
                
            added_group_ids.add(ent.id)
            added_group_names.add(group.name)
            
            # Подготавливаем данные для вставки
            if isinstance(ent, Channel) and ent.username:
                group_username = f"@{ent.username}"
            else:
                group_username = str(ent.id)
            
            groups_to_insert.append((ent.id, group_username, user_id))
            processed_count += 1
            
            # Обновляем прогресс каждые 25 групп или в конце
            if (i + 1) % 25 == 0 or i == len(sorted_dialogs) - 1:
                progress_percent = int((i + 1) / len(sorted_dialogs) * 100)
                await progress_msg.edit(
                    f"🔄 **Обновление информации о группах...**\n\n"
                    f"📊 Найдено групп: {total_groups}\n"
                    f"⚙️ Обработано: {i + 1}/{len(sorted_dialogs)} ({progress_percent}%)\n"
                    f"✅ Добавлено уникальных: {processed_count}"
                )
            
            # Выполняем батч INSERT каждые 50 групп или в конце
            if len(groups_to_insert) >= batch_size or i == len(sorted_dialogs) - 1:
                if groups_to_insert:
                    cursor.executemany(
                        "INSERT INTO groups (group_id, group_username, user_id) VALUES (?, ?, ?)",
                        groups_to_insert
                    )
                    conn.commit()
                    groups_to_insert = []
        
        # Финальное обновление
        await progress_msg.edit(
            f"✅ **Обновление завершено!**\n\n"
            f"📊 **Статистика:**\n"
            f"• Всего диалогов проверено: {len(all_dialogs)}\n"
            f"• Найдено групп/каналов: {total_groups}\n"
            f"• Добавлено уникальных: {processed_count}\n\n"
            f"💡 *Группы успешно обновлены в базе данных*"
        )
        
    except asyncio.TimeoutError:
        await progress_msg.edit("⚠️ **Таймаут операции**\n\nОбновление прервано из-за превышения времени ожидания.")
    except Exception as e:
        logging.error(f"Ошибка при обновлении групп: {e}")
        await progress_msg.edit(f"❌ **Ошибка при обновлении групп**\n\n`{str(e)}`")
    finally:
        cursor.close()
        if client.is_connected():
            await client.disconnect()


@bot.on(Query(data=lambda d: d.decode().startswith("groups_")))
async def groups_list(event: callback_query) -> None:
    """Отображает список групп пользователя."""
    import asyncio
    
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
    
    # Показываем прогресс для больших списков
    progress_msg = None
    
    try:
        # Получаем список групп из БД
        cursor.execute("SELECT group_id, group_username FROM groups WHERE user_id = ?", (user_id,))
        groups = cursor.fetchall()
        
        if not groups:
            await event.respond("📋 У вас нет добавленных групп. Добавьте группы через главное меню.")
            cursor.close()
            return
        
        # Если групп много, показываем прогресс
        if len(groups) > 50:
            progress_msg = await event.respond(f"📋 **Загрузка списка групп...**\n\n⏳ Обработка {len(groups)} групп...")
        
        await asyncio.wait_for(client.connect(), timeout=15.0)
        
        # Формируем список групп с информацией о статусе рассылки
        group_list = []
        processed = 0
        
        # Обрабатываем группы с периодическим обновлением прогресса
        for i, (group_id, group_username) in enumerate(groups):
            try:
                # Пытаемся получить entity группы с таймаутом
                ent = None
                try:
                    ent = await asyncio.wait_for(client.get_entity(group_username), timeout=5.0)
                except (asyncio.TimeoutError, Exception) as entity_error:
                    if "Cannot find any entity corresponding to" in str(entity_error) or isinstance(entity_error, asyncio.TimeoutError):
                        try:
                            # Преобразуем username в ID, если это возможно
                            try:
                                group_id_int = int(group_username)
                                ent = await asyncio.wait_for(get_entity_by_id(client, group_id_int), timeout=5.0)
                            except (ValueError, asyncio.TimeoutError):
                                # Если не удалось получить entity, используем базовую информацию
                                logging.warning(f"Не удалось получить entity для группы {group_username}, используем базовую информацию")
                                ent = None
                        except Exception as alt_error:
                            logging.error(f"Ошибка при альтернативном получении Entity: {alt_error}")
                            ent = None
                    else:
                        logging.error(f"Ошибка при получении entity для группы {group_username}: {entity_error}")
                        ent = None
                
                # Получаем статус рассылки
                status = broadcast_status_emoji(user_id, group_id)
                
                # Формируем название группы для отображения
                if ent:
                    group_name = getattr(ent, 'title', group_username)
                else:
                    # Если не удалось получить entity, используем username или ID
                    group_name = group_username if not group_username.isdigit() else f"Группа ID: {group_username}"
                
                # Используем gid_key для правильной обработки ID группы
                group_list.append((gid_key(group_id), group_name, status))
                processed += 1
                
                # Обновляем прогресс каждые 25 групп
                if progress_msg and (i + 1) % 25 == 0:
                    progress_percent = int((i + 1) / len(groups) * 100)
                    await progress_msg.edit(
                        f"📋 **Загрузка списка групп...**\n\n"
                        f"⚙️ Обработано: {i + 1}/{len(groups)} ({progress_percent}%)\n"
                        f"✅ Загружено: {processed} групп"
                    )
                    
            except Exception as e:
                logging.error(f"Ошибка при обработке группы {group_username}: {e}")
                continue
                
        # Формируем сообщение и кнопки
        if group_list:
            # Ограничиваем количество кнопок для лучшей производительности
            max_buttons = 100  # Максимум 100 кнопок за раз
            
            if len(group_list) > max_buttons:
                # Если групп слишком много, показываем первые N и добавляем пагинацию
                displayed_groups = group_list[:max_buttons]
                pagination_info = f"\n\n📄 *Показано первых {max_buttons} из {len(group_list)} групп*"
            else:
                displayed_groups = group_list
                pagination_info = ""
            
            # Создаем кнопки для каждой группы
            buttons = []
            for group_id, group_name, status in displayed_groups:
                # Ограничиваем длину названия группы для кнопки
                display_name = group_name[:50] + "..." if len(group_name) > 50 else group_name
                data = f"groupInfo_{user_id}_{group_id}".encode()
                buttons.append([Button.inline(f"{status} {display_name}", data)])
                
            # Добавляем кнопку "Назад"
            buttons.append([Button.inline("◀️ Назад", f"account_{user_id}".encode())])
            
            message = f"📋 **Список ваших групп:** ({len(group_list)} групп){pagination_info}\n\nВыберите группу для просмотра информации:"
            
            if progress_msg:
                await progress_msg.edit(message, buttons=buttons)
            else:
                await event.respond(message, buttons=buttons)
        else:
            error_msg = "⚠ Не удалось получить информацию о группах. Возможно, они были удалены или недоступны."
            if progress_msg:
                await progress_msg.edit(error_msg)
            else:
                await event.respond(error_msg)
            
    except asyncio.TimeoutError:
        error_msg = "⚠️ **Таймаут при загрузке групп**\n\nСписок групп слишком большой для быстрой загрузки. Попробуйте позже."
        if progress_msg:
            await progress_msg.edit(error_msg)
        else:
            await event.respond(error_msg)
    except Exception as e:
        logging.error(f"Ошибка при получении списка групп: {e}")
        error_msg = f"⚠ Ошибка при получении списка групп: {str(e)}"
        if progress_msg:
            await progress_msg.edit(error_msg)
        else:
            await event.respond(error_msg)
    finally:
        if client.is_connected():
            await client.disconnect()
        cursor.close()
