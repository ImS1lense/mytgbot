import random
import time
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler

DATA_FILE = 'user_data.json'

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

BONUS_NAME = "Бонус iq"  
GROW_COOLDOWN = 5 * 60 
BONUS_COOLDOWN = 3 * 60 * 60  
CREATOR_ID = 7058646786 

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

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4) 

user_data = load_data()

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
            'last_visit': time.time(),  
            'last_growth_time': 0,  
            'last_daily_time': 0, 
            'growth_attempts': []  
        }
        save_data(user_data)  

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

    await update.callback_query.message.delete()

    keyboard = [
        [InlineKeyboardButton(f"{emojis['home']} Главное меню", callback_data='home')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text(profile_text, reply_markup=reply_markup)

async def top(update: Update, context: CallbackContext) -> None:
    sorted_users = sorted(user_data.items(), key=lambda item: item[1]['growth'], reverse=True)
    
    top_text = f"{emojis['top']} Топ игроков:\n"
    for index, (user_id, data) in enumerate(sorted_users[:10]):  #топ 10 плееров
        top_text += f"{index + 1}. @{data['nickname']} — {data['growth']} iq {emojis['trophy']}\n"
    
    await update.callback_query.message.reply_text(top_text)

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

    user_data[user_id]['last_growth_time'] = current_time

    growth = random.randint(-5, 15)
    user_data[user_id]['growth'] += growth
    user_data[user_id]['experience'] += 10  

    if growth < 0:
        user_data[user_id]['failed_attempts'] += 1
        await update.callback_query.message.reply_text(f"{emojis['fail']} Удачи в следующий раз! Вы потеряли {abs(growth)} iq. Общее количество хромосом: {user_data[user_id]['growth']} iq.")
    else:
        await update.callback_query.message.reply_text(f"{emojis['success']} ВЫ получили {growth} iq! Ваш общий результат: {user_data[user_id]['growth']} iq.")

    save_data(user_data)

async def daily_bonus(update: Update, context: CallbackContext) -> None:
    user_id = update.callback_query.from_user.id
    if user_id not in user_data:
        await update.callback_query.message.reply_text(f"{emojis['warning']} Сначала используйте команду /start")
        return

    current_time = time.time()
    user = user_data[user_id]

    if current_time - user.get('last_daily_time', 0) < BONUS_COOLDOWN:
        wait_time = BONUS_COOLDOWN - (current_time - user['last_daily_time'])
        wait_time_formatted = time.strftime('%H:%M:%S', time.gmtime(wait_time))
        await update.callback_query.message.reply_text(f"{emojis['wait']} Ты уже получал бонус недавно. Подожди еще {wait_time_formatted}.")
        return

    bonus_growth = random.randint(5, 20)
    user_data[user_id]['growth'] += bonus_growth
    user_data[user_id]['experience'] += 5
    user_data[user_id]['last_daily_time'] = current_time

    save_data(user_data)

    await update.callback_query.message.reply_text(f"{emojis['gift']} Ваш {BONUS_NAME}: {bonus_growth} iq и {5} опыта! Общее количество хромосом: {user_data[user_id]['growth']} iq.")

async def stats(update: Update, context: CallbackContext) -> None:
    total_users = len(user_data)
    total_growth = sum(user['growth'] for user in user_data.values())

    stats_text = f"{emojis['stats']} Статистика бота:\n" \
                 f"Общее количество пользователей: {total_users}\n" \
                 f"Общее количество : {total_growth} iq"

    await update.callback_query.message.reply_text(stats_text)

async def reset(update: Update, context: CallbackContext) -> None:
    user_id = update.callback_query.from_user.id
    if user_id not in user_data:
        await update.callback_query.message.reply_text(f"{emojis['warning']} Сначала используйте команду /start")
        return

    user_data[user_id] = {
        'name': update.callback_query.from_user.first_name,
        'nickname': update.callback_query.from_user.username or "Никнейм не задан",
        'join_time': time.time(),
        'growth': 0,
        'experience': 0,
        'failed_attempts': 0,
        'last_growth': time.time(),
        'last_visit': time.time(),  
        'last_growth_time': 0, 
        'last_daily_time': 0,  
        'growth_attempts': [] 
    }
    save_data(user_data)

    await update.callback_query.message.reply_text(f"{emojis['reset']} Все данные были сброшены. Начнем заново!")

def main():
    app = Application.builder().token("7693103769:AAFpHCFeCUUUCE_-rMx1XpsljVePlrqqNds").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button_click))

    app.run_polling()

if __name__ == '__main__':
    main()
