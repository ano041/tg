# -*- coding: utf-8 -*-
import logging
import time
import re
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# ------------------------------------------------------------
# ЛОГИРОВАНИЕ
# ------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# API – основной и резервный
# ------------------------------------------------------------
PRIMARY_API = "https://api.exchangerate.host/latest"
BACKUP_API = "https://open.er-api.com/v6/latest/"

# ------------------------------------------------------------
# КЭШ (10 секунд) и rate-limit
# ------------------------------------------------------------
cache = {}  # (base,target) -> {"value": ..., "ts": ...}
CACHE_TTL = 10

rate_limit = {}  # user_id -> timestamp
RATE_LIMIT_TIME = 1.5  # сек

# ------------------------------------------------------------
# ФУНКЦИЯ ОГРАНИЧЕНИЯ ЗАПРОСОВ
# ------------------------------------------------------------
def can_use(user_id):
    now = time.time()
    if user_id not in rate_limit:
        rate_limit[user_id] = now
        return True
    if now - rate_limit[user_id] >= RATE_LIMIT_TIME:
        rate_limit[user_id] = now
        return True
    return False

# ------------------------------------------------------------
# АВТООЧИСТКА КЭША
# ------------------------------------------------------------
def cleanup_cache():
    """Удаляет старые записи из кэша."""
    now = time.time()
    expired = [key for key, data in cache.items() if now - data["ts"] > CACHE_TTL]
    for key in expired:
        del cache[key]

# ------------------------------------------------------------
# ПОЛУЧЕНИЕ КУРСА ИЗ ОБОИХ API
# ------------------------------------------------------------
def fetch_rate_from_primary(base: str, target: str):
    params = {"base": base, "symbols": target}
    r = requests.get(PRIMARY_API, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    rates = data.get("rates", {})
    if target not in rates:
        return None
    return rates[target]

def fetch_rate_from_backup(base: str, target: str):
    r = requests.get(f"{BACKUP_API}{base}", timeout=10)
    r.raise_for_status()
    data = r.json()
    if data.get("result") != "success":
        return None
    rates = data.get("rates", {})
    if target not in rates:
        return None
    return rates[target]

# ------------------------------------------------------------
# ОСНОВНАЯ ФУНКЦИЯ КУРСА С КЭШЕМ И РЕЗЕРВОМ
# ------------------------------------------------------------
def get_rate(base: str, target: str):
    base = base.upper()
    target = target.upper()
    key = (base, target)

    cleanup_cache()  # 🧹 чистим кэш

    # Проверка кэша
    if key in cache and time.time() - cache[key]["ts"] < CACHE_TTL:
        return cache[key]["value"], None

    # Основной API
    try:
        value = fetch_rate_from_primary(base, target)
        if value is not None:
            cache[key] = {"value": value, "ts": time.time()}
            return value, None
    except Exception as e:
        logger.warning(f"Primary API failed: {e}")

    # Резервный API
    try:
        value = fetch_rate_from_backup(base, target)
        if value is not None:
            cache[key] = {"value": value, "ts": time.time()}
            return value, None
    except Exception as e:
        logger.error(f"Backup API failed: {e}")

    return None, "Не удалось получить курс валют. Попробуйте позже."

# ------------------------------------------------------------
# MARKDOWNV2: безопасное экранирование
# ------------------------------------------------------------
def escape_md(text: str) -> str:
    """Экранирует спецсимволы для MarkdownV2."""
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)

# ------------------------------------------------------------
# ФОРМАТ ОТВЕТА
# ------------------------------------------------------------
def format_rate(base, target, rate):
    base, target = escape_md(base), escape_md(target)
    return (
        f"💱 *Курс валют*\n"
        f"——————————————\n"
        f"*1 {base}* = *{rate:.4f} {target}*\n"
        f"📅 Данные обновлены прямо сейчас\n"
        f"Источник: exchangerate\\.host / open\\.er\\-api\\.com"
    )

# ------------------------------------------------------------
# КНОПКИ ДЛЯ ПОВТОРНОГО ЗАПРОСА
# ------------------------------------------------------------
def rate_keyboard(base, target):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Обновить", callback_data=f"UPDATE_{base}_{target}")]
    ])

# ------------------------------------------------------------
# СТАРТ
# ------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("USD → RUB", callback_data="USD_RUB"),
            InlineKeyboardButton("EUR → RUB", callback_data="EUR_RUB"),
        ],
        [
            InlineKeyboardButton("USD → EUR", callback_data="USD_EUR"),
            InlineKeyboardButton("EUR → USD", callback_data="EUR_USD"),
        ],
        [
            InlineKeyboardButton("BTC → USD", callback_data="BTC_USD"),
            InlineKeyboardButton("BTC → RUB", callback_data="BTC_RUB"),
        ],
        [InlineKeyboardButton("Помощь", callback_data="help")]
    ]

    await update.message.reply_text(
        "💰 *Бот курсов валют*\n\n"
        "Можешь нажать кнопку или написать:\n"
        "`USD RUB`\n"
        "`100 USD RUB` (конвертация суммы)\n"
        "`/rate USD RUB`",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="MarkdownV2"
    )

# ------------------------------------------------------------
# ОБРАБОТКА КОМАНДЫ /rate
# ------------------------------------------------------------
async def rate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Используйте: `/rate USD RUB` или `100 USD RUB`",
            parse_mode="MarkdownV2"
        )
        return

    try:
        if len(context.args) == 2:
            base, target = context.args
            await send_rate(update, base, target)
            return

        if len(context.args) == 3:
            amount = float(context.args[0])
            base, target = context.args[1], context.args[2]
            await send_rate(update, base, target, amount)
            return
    except ValueError:
        pass

    await update.message.reply_text("Неверный формат.")

# ------------------------------------------------------------
# ОБРАБОТКА ТЕКСТА
# ------------------------------------------------------------
async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().upper().split()

    if len(text) == 2:
        await send_rate(update, text[0], text[1])
        return

    if len(text) == 3:
        try:
            amount = float(text[0])
            await send_rate(update, text[1], text[2], amount)
            return
        except ValueError:
            pass

    await update.message.reply_text(
        "Формат:\n`USD RUB`\n`100 USD RUB`",
        parse_mode="MarkdownV2"
    )

# ------------------------------------------------------------
# ОСНОВНАЯ ФУНКЦИЯ ОТПРАВКИ КУРСА
# ------------------------------------------------------------
async def send_rate(update, base, target, amount=None):
    user_id = update.message.from_user.id

    if not can_use(user_id):
        await update.message.reply_text("⏳ Слишком много запросов. Подожди секунду.")
        return

    rate, error = get_rate(base, target)

    if error:
        await update.message.reply_text(f"❌ {error}")
        return

    base, target = base.upper(), target.upper()

    if amount is not None:
        result = rate * amount
        text = (
            f"💱 *Конвертация валют*\n"
            f"——————————————\n"
            f"*{escape_md(str(amount))} {escape_md(base)}* = *{result:.4f} {escape_md(target)}*\n"
            f"1 {escape_md(base)} = {rate:.4f} {escape_md(target)}"
        )
        await update.message.reply_text(
            text,
            reply_markup=rate_keyboard(base, target),
            parse_mode="MarkdownV2"
        )
        return

    await update.message.reply_text(
        format_rate(base, target, rate),
        reply_markup=rate_keyboard(base, target),
        parse_mode="MarkdownV2"
    )

# ------------------------------------------------------------
# INLINE-КНОПКИ
# ------------------------------------------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "help":
        await query.edit_message_text(
            "ℹ️ *Помощь*\n\n"
            "Примеры:\n"
            "`USD RUB`\n"
            "`100 USD RUB`\n"
            "`/rate USD RUB`",
            parse_mode="MarkdownV2"
        )
        return

    if query.data.startswith("UPDATE_"):
        _, base, target = query.data.split("_")
        rate, error = get_rate(base, target)

        if error:
            await query.edit_message_text(f"❌ {error}")
            return

        new_text = format_rate(base, target, rate)
        if query.message.text != new_text:
            await query.edit_message_text(
                new_text,
                reply_markup=rate_keyboard(base, target),
                parse_mode="MarkdownV2"
            )
        return

    base, target = query.data.split("_")
    rate, error = get_rate(base, target)

    if error:
        await query.edit_message_text(f"❌ {error}")
        return

    await query.edit_message_text(
        format_rate(base, target, rate),
        reply_markup=rate_keyboard(base, target),
        parse_mode="MarkdownV2"
    )

# ------------------------------------------------------------
# ОШИБКИ
# ------------------------------------------------------------
async def error_handler(update, context):
    logger.error(f"Ошибка: {context.error}")

# ------------------------------------------------------------
# ЗАПУСК БОТА
# ------------------------------------------------------------
def main():
    TOKEN = "ВАШ_ТОКЕН_ТУТ"  # 👉 замени на свой токен или используй переменные окружения

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("rate", rate_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))
    app.add_error_handler(error_handler)

    print("🤖 Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
