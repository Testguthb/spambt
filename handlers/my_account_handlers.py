import logging

from telethon import Button, TelegramClient
from telethon.sessions import StringSession

from config import callback_query, API_ID, API_HASH, Query, bot, conn, processed_callbacks
from func.func import get_active_broadcast_groups, broadcast_status_emoji, get_entity_by_id


@bot.on(Query(data=b"my_accounts"))
async def my_accounts(event: callback_query) -> None:
    """
    Выводит список аккаунтов
    """
    cursor = None
    try:
        cursor = conn.cursor()
        buttons = []
        accounts_found = False
        
        # Импортируем asyncio для таймаутов
        import asyncio

        for user_id, session_string in cursor.execute("SELECT user_id, session_string FROM sessions"):
            accounts_found = True
            client = None
            try:
                client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
                await client.connect()
                
                # Добавляем таймаут для получения информации об аккаунте
                me = await asyncio.wait_for(client.get_me(), timeout=10.0)
                username = me.first_name if me.first_name else "Без ника"
                buttons.append([Button.inline(f"👤 {username}", f"account_info_{user_id}")])
                
            except asyncio.TimeoutError:
                logging.warning(f"Таймаут при загрузке аккаунта {user_id}")
                buttons.append([Button.inline(f"⚠ Таймаут загрузки (ID: {user_id})", f"account_info_{user_id}")])
            except Exception as e:
                logging.error(f"Ошибка при загрузке аккаунта {user_id}: {e}")
                buttons.append([Button.inline(f"⚠ Ошибка загрузки (ID: {user_id})", f"account_info_{user_id}")])
            finally:
                if client:
                    try:
                        await client.disconnect()
                    except:
                        pass

        if not accounts_found:
            await event.respond("❌ У вас нет добавленных аккаунтов")
            return

        await event.respond("📱 **Список ваших аккаунтов:**", buttons=buttons)

    except Exception as e:
        logging.error(f"Error in my_accounts: {e}")
        await event.respond("⚠ Произошла ошибка при получении списка аккаунтов")
    finally:
        if cursor:
            cursor.close()


@bot.on(Query(data=lambda data: data.decode().startswith("account_info_")))
async def handle_account_button(event: callback_query) -> None:
    # Получаем уникальный идентификатор для этого callback
    callback_id = f"{event.sender_id}:{event.query.msg_id}"
    
    # Проверяем, был ли уже обработан этот callback
    if callback_id in processed_callbacks:
        # Этот callback уже был обработан, отвечаем на событие без отправки нового сообщения
        await event.answer("Уже обработано")
        return
        
    # Отмечаем callback как обработанный
    processed_callbacks[callback_id] = True
        
    user_id = int(event.data.decode().split("_")[2])
    cursor = conn.cursor()
    row = cursor.execute(
        "SELECT session_string FROM sessions WHERE user_id = ?", (user_id,)
    ).fetchone()
    if not row:
        cursor.close()
        await event.respond("⚠ Не удалось найти аккаунт.")
        return

    session_string = row[0]
    client = None
    try:
        client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
        await client.connect()
        
        # Устанавливаем таймаут для операций с клиентом
        import asyncio
        
        # Получаем основную информацию об аккаунте с таймаутом
        try:
            me = await asyncio.wait_for(client.get_me(), timeout=10.0)
            username = me.first_name or "Без имени"
            phone = me.phone or "Не указан"
        except asyncio.TimeoutError:
            await event.respond("⚠ Таймаут при получении информации об аккаунте. Попробуйте позже.")
            return
        except Exception as e:
            logging.error(f"Ошибка при получении информации об аккаунте: {e}")
            await event.respond("⚠ Ошибка при получении информации об аккаунте.")
            return
        
        # Получаем количество групп без загрузки их названий (быстро)
        groups_count = cursor.execute("SELECT COUNT(*) FROM groups WHERE user_id = ?", (user_id,)).fetchone()[0]
        
        # Получаем активные рассылки
        active_gids = get_active_broadcast_groups(user_id)
        mass_active = "🟢 ВКЛ" if active_gids else "🔴 ВЫКЛ"
        
        buttons = [
            [
                Button.inline("📋 Список групп", f"listOfgroups_{user_id}")
            ],
            [Button.inline("🚀 Начать рассылку во все чаты", f"broadcastAll_{user_id}"),
             Button.inline("❌ Остановить общую рассылку", f"StopBroadcastAll_{user_id}")],
            [Button.inline("✔ Обновить информацию о группах", f"add_all_groups_{user_id}")],
            [Button.inline("❌ Удалить этот аккаунт", f"delete_account_{user_id}")]
        ]

        # Показываем краткую информацию без загрузки названий групп
        await event.respond(
            f"📢 **Меню для аккаунта {username}:**\n"
            f"🚀 **Массовая рассылка:** {mass_active}\n\n"
            f"📌 **Имя:** {username}\n"
            f"📞 **Номер:** `+{phone}`\n\n"
            f"📊 **Количество групп:** {groups_count}\n"
            f"💡 *Нажмите \"📋 Список групп\" для просмотра подробной информации*",
            buttons=buttons
        )
        
    except Exception as e:
        logging.error(f"Ошибка в handle_account_button: {e}")
        await event.respond("⚠ Произошла ошибка при загрузке меню аккаунта.")
    finally:
        if client:
            try:
                await client.disconnect()
            except:
                pass
        cursor.close()
