import logging

from telethon import Button
from config import callback_message, ADMIN_ID_LIST, New_Message, bot
from func.func import save_setting 

@bot.on(New_Message(pattern="/start"))
async def start(event: callback_message) -> None:
    """
    Обрабатывает команду /start
    """
    logging.info(f"Нажата команда /start")
    if event.sender_id in ADMIN_ID_LIST:
        buttons = [
            [Button.inline("➕ Добавить аккаунт 👤", b"add_account"),
             Button.inline("➕ Добавить группу 👥", b"add_groups")],
            [Button.inline("👤 Мои аккаунты", b"my_accounts")],
            [Button.inline("📨 Рассылка во все аккаунты", b"broadcast_All_account")],
            [Button.inline("❌ Остановить рассылку во все аккаунты", b"Stop_Broadcast_All_account")],
            [Button.inline("🕗 История рассылки", b"show_history")]
        ]
        await event.respond("👋 Добро пожаловать, Админ!", buttons=buttons)
    else:
        await event.respond("⛔ Запрещено!")


@bot.on(New_Message(pattern="/setpause"))
async def set_pause_time(event: callback_message):
    """
    Устанаваливаем начало и конец ночной паузы.
    Использование: /setpause 22 8
    """
    if event.sender_id not in ADMIN_ID_LIST:
        return

    parts = event.text.split()
    if len(parts) != 3:
        await event.respond(
            "⚠️ **Неправильный формат.**\nВведите: `/setpause [час_начала] [час_окончания]`\n"
            "**Например:** `/setpause 22 8`"
        )
        return

    try:
        start_hour = int(parts[1])
        end_hour = int(parts[2])

        if not (0 <= start_hour <= 23 and 0 <= end_hour <= 23):
            raise ValueError("Часы должны быть в диапазоне с 0 до 23.")

        save_setting('pause_start_hour', start_hour)
        save_setting('pause_end_hour', end_hour)

        await event.respond(f"✅ **Настройки сохранены.**\nНочная пауза: с **{start_hour}:00** до **{end_hour}:00**.")
    except ValueError as e:
        await event.respond(f"❌ **Ошибка!**\n{e}\n\nВведите два целых числа от 0 до 23.")