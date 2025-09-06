from config import user_sessions_deleting, callback_query, callback_message, Query, New_Message, bot, conn


@bot.on(Query(data=b"delete_group"))
async def handle_delete_group(event: callback_query) -> None:
    user_sessions_deleting[event.sender_id] = {"step": "awaiting_group_username"}
    await event.respond("📲 Введите @username группы, которую нужно удалить:")


@bot.on(New_Message(func=lambda event: (user_state := user_sessions_deleting.get(event.sender_id)) and user_state["step"] == "awaiting_group_username"))
async def handle_user_input(event: callback_message) -> None:
    group_username = event.text.strip()

    if group_username.startswith("@"):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM groups WHERE group_username = ?", (group_username,))
        group = cursor.fetchone()

        if group:
            cursor.execute("DELETE FROM groups WHERE group_username = ?", (group_username,))
            conn.commit()
            await event.respond(f"✅ Группа {group_username} успешно удалена из базы данных!")
        else:
            await event.respond("⚠ Группа с именем {group_username} не найдена в базе данных.")

        user_sessions_deleting.pop(event.sender_id, None)
        cursor.close()
    else:
        await event.respond("⚠ Пожалуйста, введите корректный @username группы, начиная с '@'.")
        return