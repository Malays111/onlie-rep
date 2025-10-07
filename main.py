import asyncio
import os
import json
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.enums import ContentType
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# Токен бота
TOKEN = "8219940488:AAEJBcxzzTLYNDK_99MLbB730mKxbSnEpIo"

# ID владельца группы (замените на свой Telegram ID)
OWNER_ID = 8237632695  # Пример, замените на реальный ID

# ID чата и сообщения для репутации
REPUTATION_CHAT_ID = -1003157897257
def save_data():
    data = {
        'reputation': reputation,
        'pending_reviews': pending_reviews,
        'reviews': reviews
    }
    with open('bot_data.json', 'w') as f:
        json.dump(data, f)

def load_data():
    global reputation, pending_reviews, reviews
    try:
        with open('bot_data.json', 'r') as f:
            data = json.load(f)
            reputation = data.get('reputation', {'good': 0, 'bad': 0, 'last_review': {'date': 'Нет', 'content': 'Нет'}})
            pending_reviews = data.get('pending_reviews', {})
            reviews = data.get('reviews', [])
    except FileNotFoundError:
        pass
REPUTATION_MESSAGE_ID = 207

# Webhook
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # Установить в Railway переменную окружения

async def update_reputation_message():
    total = reputation['good'] + reputation['bad']
    average = (reputation['good'] / total * 100) if total > 0 else 0
    average_10 = (reputation['good'] / total * 10) if total > 0 else 0
    text = f"""<b>Репутация: <a href="https://t.me/Roeev">Roeev | Work</a> | @Roeev</b>

✅ <b>Хороших отзывов:</b> {reputation['good']}
❌ <b>Плохих отзывов:</b> {reputation['bad']}
📊 <b>Средняя оценка:</b> {average:.1f}% (или {average_10:.1f}/10)
📈 <b>Общее количество отзывов:</b> {total}

🔹 <b>Последний отзыв:</b> {reputation['last_review']['date']} — "{reputation['last_review']['content']}"
🔹 <b>Тренд репутации:</b> ↔️ стабильно
🔹 <i>Рекомендуют:</i> {average:.1f}% пользователей"""
    try:
        await bot.edit_message_caption(
            chat_id=REPUTATION_CHAT_ID,
            message_id=REPUTATION_MESSAGE_ID,
            caption=text,
            parse_mode='HTML'
        )
        print("Репутация обновлена")
    except Exception as e:
        print(f"Ошибка обновления репутации: {e}")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Словарь для хранения данных отзывов: reply_message_id -> {'original_user_id': id, 'text': text, 'username': username, 'type': 'good' or 'bad'}
pending_reviews = {}

# Статистика репутации
reputation = {'good': 0, 'bad': 0, 'last_review': {'date': 'Нет', 'content': 'Нет'}}
reviews = []
load_data()

@dp.message()
async def handle_messages(message: Message):
    global reputation, reviews
    print(f"Получено сообщение: content_type={message.content_type}, text={message.text}, from_user={message.from_user}")
    # Проверяем тип сообщения: вступление или выход из группы
    if message.content_type in [ContentType.NEW_CHAT_MEMBERS, ContentType.LEFT_CHAT_MEMBER]:
        try:
            await message.delete()
            print("Сообщение удалено")
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")
    # Проверяем на отзыв
    if message.text and not message.text.startswith('/'):
        text_lower = message.text.lower()
        good_words = ['ахуенный', 'топ', 'круто', 'отлично', 'хорошо', 'спасибо', 'рекомендую', '+rep', '+ rep', '+реп', '+ реп']
        bad_words = ['хуйня', 'наебал', 'плохо', 'отстой', 'развод', 'мошенник', '-rep', '- rep', '-реп', '- реп']
        is_good = any(word in text_lower for word in good_words)
        is_bad = any(word in text_lower for word in bad_words)
        if message.from_user.id == OWNER_ID and (is_good or is_bad):
            # Админ пытается оставить отзыв
            try:
                await message.reply("Админы не могут оставлять и накручивать себе репутацию")
                await message.delete()
                print("Админ попытался оставить отзыв")
            except Exception as e:
                print(f"Ошибка при ответе админу: {e}")
        elif is_bad:
            # Плохой отзыв, на модерацию
            try:
                reply_msg = await message.reply("Ваш отзыв временно удален,так как он в обработке,сейчас прийдет модератор и проверит его")
                pending_reviews[reply_msg.message_id] = {
                    'original_user_id': message.from_user.id,
                    'text': message.text,
                    'username': message.from_user.username or message.from_user.first_name,
                    'type': 'bad'
                }
                save_data()
                await message.delete()  # Удаляем оригинальное сообщение
                print("Плохой отзыв на модерацию")
            except Exception as e:
                print(f"Ошибка при отправке ответа: {e}")
        elif is_good:
            # Хороший отзыв, сразу одобряем
            try:
                username = message.from_user.username or message.from_user.first_name
                text_lower = message.text.lower()
                if any(rep in text_lower for rep in ['+rep', '+ rep', '+реп', '+ реп']) and '@roeev' not in text_lower:
                    if '+rep ' in message.text:
                        modified_text = message.text.replace('+rep ', '+rep @Roeev ', 1)
                    elif '+ rep ' in message.text:
                        modified_text = message.text.replace('+ rep ', '+ rep @Roeev ', 1)
                    elif '+реп ' in message.text:
                        modified_text = message.text.replace('+реп ', '+реп @Roeev ', 1)
                    elif '+ реп ' in message.text:
                        modified_text = message.text.replace('+ реп ', '+ реп @Roeev ', 1)
                    elif text_lower.strip() in ['+rep', '+реп']:
                        modified_text = message.text.strip() + ' @Roeev'
                    elif text_lower.strip() in ['+ rep', '+ реп']:
                        modified_text = message.text.strip() + ' @Roeev'
                    else:
                        modified_text = message.text
                else:
                    modified_text = message.text
                clean_text = modified_text
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=f"👍 <i><b>Новый отзыв от</b></i> <b>@{username}</b>\nОтзыв: <blockquote>{clean_text}</blockquote>\n(<b>+ еще 1 хорошая репутация у @Roeev</b>)\n<i>*Текущая хорошая репутация:</i> {reputation['good'] + 1} 👍",
                    parse_mode='HTML'
                )
                reputation['good'] += 1
                reviews.append({'username': username, 'text': clean_text, 'type': 'good', 'date': datetime.now().strftime("%d.%m.%Y")})
                reputation['last_review'] = {
                    'date': datetime.now().strftime("%d.%m.%Y"),
                    'content': f"@{username} (+rep): {clean_text}"
                }
                save_data()
                await update_reputation_message()
                await message.delete()
                print("Хороший отзыв одобрен")
            except Exception as e:
                print(f"Ошибка при одобрении хорошего отзыва: {e}")
    # Проверяем команду /confirm от владельца в reply на сообщение бота
    if message.text == "/confirm" and message.from_user.id == OWNER_ID and message.reply_to_message and message.reply_to_message.from_user.id == bot.id and message.reply_to_message.message_id in pending_reviews:
        try:
            data = pending_reviews[message.reply_to_message.message_id]
            await bot.delete_message(chat_id=message.chat.id, message_id=message.reply_to_message.message_id)
            clean_text = data['text'].replace('@Roeev', '').strip()
            await bot.send_message(
                chat_id=message.chat.id,
                text=f"👎 <i>Новый отзыв от</i> <b>@{data['username']}</b>\nОтзыв: <blockquote>{clean_text}</blockquote>\n(<b>- еще 1 плохая репутация у @Roeev</b>)\n<i>*Текущая плохая репутация:</i> {reputation['bad'] + 1} 👎",
                parse_mode='HTML'
            )
            if data['type'] == 'bad':
                reputation['bad'] += 1
                reviews.append({'username': data['username'], 'text': clean_text, 'type': 'bad', 'date': datetime.now().strftime("%d.%m.%Y")})
            reputation['last_review'] = {
                'date': datetime.now().strftime("%d.%m.%Y"),
                'content': f"@{data['username']} (-rep): {clean_text}"
            }
            save_data()
            await update_reputation_message()
            del pending_reviews[message.reply_to_message.message_id]
            await message.delete()  # Удаляем команду
            print("Отзыв одобрен")
        except Exception as e:
            print(f"Ошибка при одобрении: {e}")
    # Проверяем команду /del от владельца в reply на сообщение бота
    if message.text == "/del" and message.from_user.id == OWNER_ID and message.reply_to_message and message.reply_to_message.from_user.id == bot.id and message.reply_to_message.message_id in pending_reviews:
        try:
            data = pending_reviews[message.reply_to_message.message_id]
            # Отправляем сообщение в приват чат отправителя
            await bot.send_message(
                chat_id=data['original_user_id'],
                text="ваш отзыв был отклонен,так как он не настоящий"
            )
            await bot.delete_message(chat_id=message.chat.id, message_id=message.reply_to_message.message_id)
            del pending_reviews[message.reply_to_message.message_id]
            save_data()
            await message.delete()  # Удаляем команду
            print("Отклонение отправлено, ответ удален")
        except Exception as e:
            print(f"Ошибка при отправке отклонения: {e}")
    # Команда /init_rep для инициализации сообщения репутации
    if message.text == "/init_rep" and message.from_user.id == OWNER_ID:
        try:
            photo_url = "https://dl.dropboxusercontent.com/scl/fi/78qa1gk8x4j1jyv30lvre/photo_2025-10-06_17-45-34-1.jpg?rlkey=l31pkl2i2fpvc3aivwvmhkk8d&st=eatp97wj"
            msg = await bot.send_photo(
                chat_id=REPUTATION_CHAT_ID,
                photo=photo_url,
                caption="Инициализация репутации..."
            )
            await message.reply(f"Сообщение отправлено, ID: {msg.message_id}. Обновите REPUTATION_MESSAGE_ID в коде на {msg.message_id}.")
            print(f"Инициализировано сообщение репутации с ID {msg.message_id}")
        except Exception as e:
            print(f"Ошибка инициализации: {e}")
    # Команда /rep_roeev для добавления положительного отзыва
    if message.text == "/rep_roeev" and message.from_user.id == OWNER_ID:
        try:
            clean_text = "обменял баксы очень быстро, отличный сервис, всегда на связи, рекомендую всем для безопасных обменов!"
            await bot.send_message(
                chat_id=message.chat.id,
                text=f"👍 <i>Новый отзыв от</i><b>@Roeev</b>\nОтзыв: <blockquote>{clean_text}</blockquote>\n(<b>+ еще 1 хорошая репутация у @Roeev</b>)\nТекущая хорошая репутация: {reputation['good'] + 1} 👍",
                parse_mode='HTML'
            )
            reputation['good'] += 1
            reviews.append({'username': 'Roeev', 'text': clean_text, 'type': 'good', 'date': datetime.now().strftime("%d.%m.%Y")})
            reputation['last_review'] = {
                'date': datetime.now().strftime("%d.%m.%Y"),
                'content': f"@Roeev (+rep): {clean_text}"
            }
            save_data()
            await update_reputation_message()
            await message.delete()
            print("Отзыв добавлен")
        except Exception as e:
            print(f"Ошибка добавления отзыва: {e}")
    # Команда /list для списка отзывов
    if message.text == "/list" and message.from_user.id == OWNER_ID:
        try:
            text = f"Общее хороших отзывов: {reputation['good']}\nОбщее плохих отзывов: {reputation['bad']}\n\nСписок отзывов с текстами:\n"
            if not reviews:
                text += "Нет отзывов с текстами."
            else:
                for i, rev in enumerate(reviews, 1):
                    sign = '+' if rev['type'] == 'good' else '-'
                    text += f"{i}. @{rev['username']} ({rev['date']}): {rev['text']} ({sign})\n"
            await message.reply(text)
        except Exception as e:
            print(f"Ошибка списка: {e}")
    # Команда /del для удаления отзыва
    if message.text.startswith("/del ") and message.from_user.id == OWNER_ID:
        try:
            parts = message.text.split()
            if len(parts) == 2:
                num = int(parts[1]) - 1
                if 0 <= num < len(reviews):
                    rev = reviews.pop(num)
                    if rev['type'] == 'good':
                        reputation['good'] -= 1
                    else:
                        reputation['bad'] -= 1
                    save_data()
                    await update_reputation_message()
                    await message.reply(f"Отзыв {num+1} удален.")
                else:
                    await message.reply("Неверный номер.")
            else:
                await message.reply("Используйте /del <номер>")
        except ValueError:
            await message.reply("Неверный формат номера.")
        except Exception as e:
            print(f"Ошибка удаления: {e}")
    # Команда /reset для сброса репутации
    if message.text == "/reset" and message.from_user.id == OWNER_ID:
        try:
            reputation = {'good': 0, 'bad': 0, 'last_review': {'date': 'Нет', 'content': 'Нет'}}
            reviews = []
            save_data()
            await update_reputation_message()
            await message.reply("Репутация сброшена.")
            await message.delete()
        except Exception as e:
            print(f"Ошибка сброса: {e}")

async def main():
    if WEBHOOK_URL:
        # Webhook mode
        await bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH)
        app = web.Application()
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
        )
        webhook_requests_handler.register(app, path=WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
        await site.start()
        print("Бот запущен в режиме webhook")
        # Keep the event loop running
        await asyncio.EventLoop().create_future()
    else:
        # Polling mode for local testing
        print("Бот запущен и начинает polling...")
        await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())