import random
import time
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler

# Путь к файлу для хранения данных
DATA_FILE = 'user_data.json'

# Эмодзи для сообщений
emojis = {
    "start": "🌱",
    "grow": "🌿",
    "top": "🏆",
    "profile": "👤",
    "success": "🎉",
    "fail": "❌",
    "reload": "🔄",
    "creator": "👑",
    "menu": "🍔",
    "wait": "⏳",
    "happy": "😊",
    "warning": "⚠️",
    "trophy": "🏅",
    "home": "🏠",
    "level_up": "⬆️",
    "reset": "🔄",
    "stats": "📊",
    "gift": "🎁",
    "clock": "⏰",
    "leaf": "🍃"
}

# Название бонуса
BONUS_NAME = "Бонус iq"  # Можно изменить название бонуса

# Интервалы (в секундах)
GROW_COOLDOWN = 5 * 60  # 5 минут для выращивания
BONUS_COOLDOWN = 3 * 60 * 60  # 3 часа для бонуса

# ID создателя (ваш ID)
CREATOR_ID = 7058646786  # Ваш Telegram ID

# Функция для загрузки данных из файла
def load_data():
    if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Файл поврежден, создается новый.")
            return {}
    else:
        return {}

# Функция для сохранения данных в файл
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)  # Красивое форматирование

# Храним данные о пользователях
user_data = load_data()

# Функция для старта бота
async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {
            'name': update.message.from_user.first_name if update.message else update.callback_query.from_user.first_name,
            'nickname': update.message.from_user.username or "Никнейм не задан",
            'join_time': time.time(),
            'growth': 0,
            'experience': 0,
            'failed_attempts': 0,
            'last_growth': time.time(),
            'last_visit': time.time(),  # Время последнего посещения
            'last_growth_time': 0,  # Время последнего выращивания
            'last_daily_time': 0,  # Время последнего получения бонуса
            'growth_attempts': []  # Храним попытки выращивания
        }
        save_data(user_data)  # Сохраняем данные

    keyboard = [
        [InlineKeyboardButton(f"{emojis['profile']} Профиль", callback_data='profile')],
        [InlineKeyboardButton(f"{emojis['top']} Топ игроков", callback_data='top')],
        [InlineKeyboardButton(f"{emojis['grow']} Повысить iq", callback_data='grow')],
        [InlineKeyboardButton(f"{emojis['gift']} {BONUS_NAME}", callback_data='daily')],
        [InlineKeyboardButton(f"{emojis['stats']} Статы", callback_data='stats')],
        [InlineKeyboardButton(f"{emojis['reset']} Сбросить данные", callback_data='reset')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(f"{emojis['start']} Привет, {user_data[user_id]['name']}! Что хочешь сделать? {emojis['menu']}", reply_markup=reply_markup) if update.message else await update.callback_query.message.edit_text(f"{emojis['start']} Привет, {user_data[user_id]['name']}! Что хочешь сделать? {emojis['menu']}", reply_markup=reply_markup)

# Функция для обработки нажатий на кнопки
async def handle_button_click(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    if query.data == 'profile':
        await profile(update, context)
    elif query.data == 'top':
        await top(update, context)
    elif query.data == 'grow':
        await grow(update, context)
    elif query.data == 'daily':
        await daily_bonus(update, context)
    elif query.data == 'stats':
        await stats(update, context)
    elif query.data == 'reset':
        await reset(update, context)
    elif query.data == 'home':
        await start(update, context)

# Функция для отображения профиля
async def profile(update: Update, context: CallbackContext) -> None:
    user_id = update.callback_query.from_user.id
    if user_id not in user_data:
        await update.callback_query.message.reply_text(f"{emojis['warning']} Сначала используйте команду /start")
        return
    user = user_data[user_id]
    join_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(user['join_time']))
    profile_text = f"{emojis['profile']} Профиль:\n" \
                   f"{emojis['creator']} Ник: @{user['nickname']}\n" \
                   f"{emojis['clock']} Время регистрации: {join_time}\n" \
                   f"{emojis['grow']} У тебя: {user['growth']} iq\n" \
                   f"{emojis['level_up']} Опыт: {user['experience']} {emojis['level_up']}\n" \
                   f"{emojis['fail']} Неудачных попыток: {user['failed_attempts']}"

    # Удаляем старое сообщение
    await update.callback_query.message.delete()

    # Кнопка для возврата в главное меню
    keyboard = [
        [InlineKeyboardButton(f"{emojis['home']} Главное меню", callback_data='home')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text(profile_text, reply_markup=reply_markup)

# Функция для топа игроков
async def top(update: Update, context: CallbackContext) -> None:
    # Сортировка игроков по количеству выращенного роста
    sorted_users = sorted(user_data.items(), key=lambda item: item[1]['growth'], reverse=True)
    
    # Формируем текст для топа
    top_text = f"{emojis['top']} Топ игроков:\n"
    for index, (user_id, data) in enumerate(sorted_users[:10]):  # Показываем топ-10
        top_text += f"{index + 1}. @{data['nickname']} — {data['growth']} iq {emojis['trophy']}\n"
    
    # Отправляем топ
    await update.callback_query.message.reply_text(top_text)

# Функция для выращивания
async def grow(update: Update, context: CallbackContext) -> None:
    user_id = update.callback_query.from_user.id
    if user_id not in user_data:
        await update.callback_query.message.reply_text(f"{emojis['warning']} Сначала используйте команду /start")
        return

    user = user_data[user_id]
    current_time = time.time()

    # Проверяем, можно ли начать выращивание (раз в 5 минут)
    if current_time - user.get('last_growth_time', 0) < GROW_COOLDOWN:
        wait_time = GROW_COOLDOWN - (current_time - user['last_growth_time'])
        wait_time_formatted = time.strftime('%H:%M:%S', time.gmtime(wait_time))
        await update.callback_query.message.reply_text(f"{emojis['wait']} Ты слишком часто нажимаешь, подожди еще {wait_time_formatted}.")
        return

    # Обновляем время последнего выращивания
    user_data[user_id]['last_growth_time'] = current_time

    # Результат выращивания
    growth = random.randint(-5, 15)
    user_data[user_id]['growth'] += growth
    user_data[user_id]['experience'] += 10  # Добавление опыта за успешное выращивание

    # Если пользователь получил негативный результат, увеличиваем количество неудачных попыток
    if growth < 0:
        user_data[user_id]['failed_attempts'] += 1
        await update.callback_query.message.reply_text(f"{emojis['fail']} Удачи в следующий раз! Вы потеряли {abs(growth)} iq. Общее количество хромосом: {user_data[user_id]['growth']} iq.")
    else:
        await update.callback_query.message.reply_text(f"{emojis['success']} ВЫ получили {growth} iq! Ваш общий результат: {user_data[user_id]['growth']} iq.")

    save_data(user_data)  # Сохраняем данные

# Функция для получения ежедневного бонуса
async def daily_bonus(update: Update, context: CallbackContext) -> None:
    user_id = update.callback_query.from_user.id
    if user_id not in user_data:
        await update.callback_query.message.reply_text(f"{emojis['warning']} Сначала используйте команду /start")
        return

    current_time = time.time()
    user = user_data[user_id]

    # Проверяем, можно ли получить бонус (раз в 3 часа)
    if current_time - user.get('last_daily_time', 0) < BONUS_COOLDOWN:
        wait_time = BONUS_COOLDOWN - (current_time - user['last_daily_time'])
        wait_time_formatted = time.strftime('%H:%M:%S', time.gmtime(wait_time))
        await update.callback_query.message.reply_text(f"{emojis['wait']} Ты уже получал бонус недавно. Подожди еще {wait_time_formatted}.")
        return

    # Назначаем бонус (например, +10 см и опыт)
    bonus_growth = random.randint(5, 20)
    user_data[user_id]['growth'] += bonus_growth
    user_data[user_id]['experience'] += 5  # Бонусный опыт
    user_data[user_id]['last_daily_time'] = current_time

    save_data(user_data)  # Сохраняем данные

    await update.callback_query.message.reply_text(f"{emojis['gift']} Ваш {BONUS_NAME}: {bonus_growth} iq и {5} опыта! Общее количество хромосом: {user_data[user_id]['growth']} iq.")

# Функция для отображения статистики
async def stats(update: Update, context: CallbackContext) -> None:
    total_users = len(user_data)
    total_growth = sum(user['growth'] for user in user_data.values())

    stats_text = f"{emojis['stats']} Статистика бота:\n" \
                 f"Общее количество пользователей: {total_users}\n" \
                 f"Общее количество : {total_growth} iq"

    await update.callback_query.message.reply_text(stats_text)

# Функция для сброса данных
async def reset(update: Update, context: CallbackContext) -> None:
    user_id = update.callback_query.from_user.id
    if user_id not in user_data:
        await update.callback_query.message.reply_text(f"{emojis['warning']} Сначала используйте команду /start")
        return

    # Сброс данных пользователя
    user_data[user_id] = {
        'name': update.callback_query.from_user.first_name,
        'nickname': update.callback_query.from_user.username or "Никнейм не задан",
        'join_time': time.time(),
        'growth': 0,
        'experience': 0,
        'failed_attempts': 0,
        'last_growth': time.time(),
        'last_visit': time.time(),  # Время последнего посещения
        'last_growth_time': 0,  # Время последнего выращивания
        'last_daily_time': 0,  # Время последнего получения бонуса
        'growth_attempts': []  # Храним попытки выращивания
    }
    save_data(user_data)

    await update.callback_query.message.reply_text(f"{emojis['reset']} Все данные были сброшены. Начнем заново!")

# Запуск бота
def main():
    app = Application.builder().token("7421858821:AAEhtDjt4rNBFs4IXuaOPrJTmhIaMmkP0jU").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button_click))

    app.run_polling()

if __name__ == '__main__':
    main()
