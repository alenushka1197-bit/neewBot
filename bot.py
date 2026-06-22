import telebot
from telebot import types
import time
import os
import sys
import logging
import json
from datetime import datetime
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# ========================================
# ========== НАСТРОЙКА ЛОГГИРОВАНИЯ ==========
# ========================================

# Настройка ротации логов
handler = RotatingFileHandler(
    'bot.log',
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5
)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        handler,
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ========================================
# ========== ЗАГРУЗКА ТОКЕНОВ ==========
# ========================================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
YOUR_TELEGRAM_ID = int(os.getenv("YOUR_TELEGRAM_ID", "480145722"))
YOUR_USERNAME = os.getenv("YOUR_USERNAME", "Feisik")
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден! Проверь файл .env")

if not PROVIDER_TOKEN:
    print("⚠️ ВНИМАНИЕ: PROVIDER_TOKEN не найден! Оплата не будет работать.")

# ========================================
# ========== СОЗДАНИЕ БОТА ==========
# ========================================

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

# ========================================
# ========== СОСТОЯНИЯ ПОЛЬЗОВАТЕЛЕЙ ==========
# ========================================

user_states = {}

# ========================================
# ========== ТОВАРЫ (ЦЕНЫ В РУБЛЯХ) ==========
# ========================================

PRODUCTS = {
    # Программы тренировок
    "program_beginner": {
        "name": "Индивидуальная программа тренировок и питания",
        "price": 3500,  # 3 500 рублей
        "description": "Индивидуальная программа тренировок и питания под ваши цели.",
        "delivery_text": "🎉 Спасибо за покупку программы тренировок и питания! Напиши мне в ЛС: @{} и я отправлю программу в течение 24 часов."
    },
    "program_middle": {
        "name": "Программа для среднего уровня",
        "price": 14900,  # 14 900 рублей
        "description": "Программа для тренирующихся 3-12 месяцев. 6 недель, прогрессия нагрузок.",
        "delivery_text": "🎉 Спасибо за покупку программы для среднего уровня! Напиши мне в ЛС: @{} и я отправлю программу в течение 24 часов."
    },
    "program_advanced": {
        "name": "Программа для спортсменов",
        "price": 19900,  # 19 900 рублей
        "description": "Продвинутая программа с периодизацией. Для опытных спортсменов.",
        "delivery_text": "🎉 Спасибо за покупку программы для спортсменов! Напиши мне в ЛС: @{} и я свяжусь с тобой для индивидуальной настройки."
    },
    # Личное ведение
    "personal_1month": {
        "name": "Личное ведение — 1 месяц",
        "price": 12000,  # 12 000 рублей
        "description": "Индивидуальное сопровождение на месяц. Программа, питание, обратная связь.",
        "delivery_text": "🎉 Ты приобрел месяц личного ведения! Напиши мне в ЛС: @{} чтобы начать работу."
    },
    "personal_3month": {
        "name": "Личное ведение — 3 месяца",
        "price": 30000,  # 30 000 рублей
        "description": "Полное сопровождение на 3 месяца.",
        "delivery_text": "🎉 Ты выбрал 3 месяца личного ведения! Напиши мне в ЛС: @{} и мы начнём трансформацию!"
    },
    "personal_6month": {
        "name": "Личное ведение — 6 месяцев",
        "price": 54000,  # 54 000 рублей
        "description": "Полная трансформация за полгода.",
        "delivery_text": "🎉 Полгода личного ведения — это мощный шаг к новому себе! Напиши мне в ЛС: @{} и мы начнём!"
    },
    "personal_12month": {
        "name": "Личное ведение — 12 месяцев",
        "price": 108000,  # 108 000 рублей
        "description": "Максимальный тариф. Полная трансформация за год.",
        "delivery_text": "🎉 Год личного ведения — это мощный шаг к новому себе! Напиши мне в ЛС: @{} и мы начнём!"
    },
    # Онлайн консультация
    "consult_video": {
        "name": "Онлайн консультация",
        "price": 4000,  # 4 000 рублей
        "description": 'Онлайн консультация "Разбор под ключ"',
        "delivery_text": "🎉 Оплата за онлайн консультацию получена! Напиши мне в ЛС: @{} и мы начнём!"
    },
}

# ========================================
# ========== ТЕКСТЫ ==========
# ========================================

WELCOME_TEXT = """
🏋️‍♀️ <b>Привет! 👋
Меня зовут Константин, и я твой персональный гид в мире спорта и здорового тела.</b>

Этот бот создан, чтобы привести тебя к результату без крайностей и сложного пути.

<b>Что ты можешь сделать прямо здесь?</b>
✅ Получить готовую программу тренировок
✅ Перейти в личное ведение ко мне
✅ Заказать разовую онлайн-консультацию
✅ Написать мне лично

👇 <b>Выбери нужный раздел ниже:</b>
"""

PROGRAMS_TEXT = """
📋 <b>Программы тренировок и питания</b>

✅ Составим индивидуальную программу тренировок под твои цели, опыт и график.
✅ Подберем питание с учетом твоих вкусовых предпочтений для достижения желаемого результата

"""

PERSONAL_TEXT = """
🔥 <b>Онлайн-фитнес тренер</b>

Помогаю людям похудеть, набрать мышечную массу и привести тело в лучшую форму.

📌 <b>Что ты получаешь:</b>

1️⃣ Индивидуальную программу тренировок
2️⃣ Похудение или набор мышечной массы
3️⃣ Подбор питания
4️⃣ Корректировку рациона
5️⃣ Подбор БАДов
6️⃣ Постоянную связь и поддержку

💰 <b>Тарифы:</b>
🔥 1 месяц - 12 000₽
💪 3 месяца - 30 000₽
🏆 6 месяцев - 54 000₽
👑 12 месяцев - 108 000₽

👇 <b>Выбери тариф:</b>
"""

CONSULT_TEXT = """
🎧 <b>Онлайн-консультация «Разбор под ключ»</b>

Что ты получаешь:
✅ Ответы на все вопросы в течение 24 часов
✅ Разбор питания
✅ План действий в тренировочном процессе
✅ Корректировка техники

💰 <b>Стоимость:</b> 4 000₽

👇 <b>Нажми на кнопку ниже для оплаты:</b>
"""

CONTACT_TEXT = """
📩 <b>Связь со мной</b>

Ты можешь написать мне личное сообщение прямо сейчас!
Просто напиши свой вопрос в чат, и я отвечу в ближайшее время.

⏰ <b>Время ответа:</b> обычно 2-4 часа

👇 <b>Напиши своё сообщение:</b>
"""

# ========================================
# ========== КЛАВИАТУРЫ ==========
# ========================================

def main_menu():
    """Главное меню"""
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("📋 Программы тренировок")
    btn2 = types.KeyboardButton("👤 Личное ведение")
    btn3 = types.KeyboardButton("🎧 Онлайн консультация")
    btn4 = types.KeyboardButton("📩 Написать мне")
    keyboard.add(btn1, btn2, btn3, btn4)
    return keyboard

def programs_submenu():
    """Подменю Программы тренировок"""
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("🔹 Индивидуальная (3 500₽)")
    btn2 = types.KeyboardButton("🔹 Средний уровень (14 900₽)")
    btn3 = types.KeyboardButton("🔹 Спортсмен (19 900₽)")
    btn_back = types.KeyboardButton("🔙 Назад в главное меню")
    keyboard.add(btn1, btn2, btn3, btn_back)
    return keyboard

def personal_submenu():
    """Подменю Личное ведение"""
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("🔥 1 месяц (12 000₽)")
    btn2 = types.KeyboardButton("💪 3 месяца (30 000₽)")
    btn3 = types.KeyboardButton("🏆 6 месяцев (54 000₽)")
    btn4 = types.KeyboardButton("👑 12 месяцев (108 000₽)")
    btn_back = types.KeyboardButton("🔙 Назад в главное меню")
    keyboard.add(btn1, btn2, btn3, btn4, btn_back)
    return keyboard

def consult_submenu():
    """Подменю Онлайн консультация"""
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    btn1 = types.KeyboardButton("🎧 Оплатить консультацию (4 000₽)")
    btn_back = types.KeyboardButton("🔙 Назад в главное меню")
    keyboard.add(btn1, btn_back)
    return keyboard

def contact_submenu():
    """Подменю Связь со мной"""
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    btn_back = types.KeyboardButton("🔙 Назад в главное меню")
    keyboard.add(btn_back)
    return keyboard

# ========================================
# ========== ОТПРАВКА СООБЩЕНИЙ ==========
# ========================================

def safe_send_message(chat_id, text, parse_mode='HTML', reply_markup=None):
    """Безопасная отправка сообщения"""
    try:
        return bot.send_message(
            chat_id,
            text,
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке: {e}")
        return None

# ========================================
# ========== УВЕДОМЛЕНИЕ О НЕУДАЧНОЙ ОПЛАТЕ ==========
# ========================================

def notify_trainer_payment_failed(user_id, user_name, product_name, amount, error_message):
    """
    Отправляет уведомление тренеру о неудачной оплате
    
    Args:
        user_id: ID пользователя
        user_name: Имя пользователя
        product_name: Название товара
        amount: Сумма в рублях
        error_message: Текст ошибки
    """
    try:
        # Формируем сообщение для тренера
        failed_text = f"""
❌ **НЕУДАЧНАЯ ПОПЫТКА ОПЛАТЫ!**

👤 Пользователь: {user_name}
🆔 ID: `{user_id}`
📦 Товар: {product_name}
💰 Сумма: {amount} руб.
⚠️ Ошибка: {error_message}
🕐 Время: {time.strftime('%d.%m.%Y %H:%M')}

❗️ Проверь настройки платежей или свяжись с пользователем.
"""
        
        # Отправляем тренеру
        bot.send_message(
            YOUR_TELEGRAM_ID,
            failed_text,
            parse_mode='Markdown'
        )
        
        logger.info(f"Уведомление о неудачной оплате отправлено тренеру. Пользователь: {user_id}")
        
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления о неудачной оплате: {e}")

# ========================================
# ========== КОМАНДЫ ==========
# ========================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Обработчик команды /start"""
    try:
        logger.info(f"Пользователь {message.from_user.id} запустил бота")
        safe_send_message(
            message.chat.id,
            WELCOME_TEXT,
            parse_mode='HTML',
            reply_markup=main_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка в send_welcome: {e}")

@bot.message_handler(commands=['help'])
def send_help(message):
    """Обработчик команды /help"""
    help_text = """
📖 <b>Помощь по боту</b>

🤖 Фитнес-тренер в Telegram!

<b>📌 Команды:</b>
/start — Главное меню
/help — Помощь

<b>📋 Разделы:</b>
• Программы тренировок
• Личное ведение
• Онлайн консультация
• Написать мне

<b>💰 Оплата:</b>
• Через ЮKassa (СБП)
• После оплаты я свяжусь с тобой

👇 Используй кнопки меню
"""
    safe_send_message(
        message.chat.id,
        help_text,
        parse_mode='HTML',
        reply_markup=main_menu()
    )

@bot.message_handler(commands=['status'])
def check_status(message):
    """Проверка статуса бота (только для тренера)"""
    if message.from_user.id != YOUR_TELEGRAM_ID:
        safe_send_message(message.chat.id, "⛔ Доступ запрещен")
        return
    
    status_text = f"""
📊 **Статус бота**

✅ Бот активен
👤 ID тренера: {YOUR_TELEGRAM_ID}
💳 Провайдер: {'✅ Настроен' if PROVIDER_TOKEN else '❌ Не настроен'}
💳 Способ оплаты: СБП
📦 Товаров: {len(PRODUCTS)}
📝 Состояний пользователей: {len(user_states)}
🕐 Время: {time.strftime('%d.%m.%Y %H:%M:%S')}
"""
    safe_send_message(
        message.chat.id,
        status_text,
        parse_mode='Markdown'
    )

# ========================================
# ========== ОБРАБОТЧИК ТЕКСТА ==========
# ========================================

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """Обработчик всех сообщений"""
    try:
        text = message.text
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # Если пользователь в режиме "Написать мне" - пропускаем
        if user_id in user_states and user_states[user_id] == "waiting_for_message":
            return

        # ----- ГЛАВНОЕ МЕНЮ -----
        if text == "📋 Программы тренировок":
            safe_send_message(chat_id, PROGRAMS_TEXT, parse_mode='HTML', reply_markup=programs_submenu())
            return

        if text == "👤 Личное ведение":
            safe_send_message(chat_id, PERSONAL_TEXT, parse_mode='HTML', reply_markup=personal_submenu())
            return

        if text == "🎧 Онлайн консультация":
            safe_send_message(chat_id, CONSULT_TEXT, parse_mode='HTML', reply_markup=consult_submenu())
            return

        if text == "📩 Написать мне":
            user_states[user_id] = "waiting_for_message"
            safe_send_message(chat_id, CONTACT_TEXT, parse_mode='HTML', reply_markup=contact_submenu())
            bot.register_next_step_handler(message, forward_to_trainer)
            return

        # ----- КНОПКА НАЗАД -----
        if text == "🔙 Назад в главное меню":
            user_states.pop(user_id, None)
            safe_send_message(chat_id, "🔁 Главное меню:", reply_markup=main_menu())
            return

        # ----- ПРОГРАММЫ ТРЕНИРОВОК -----
        if text == "🔹 Индивидуальная (3 500₽)":
            create_invoice(chat_id, "program_beginner")
            return

        if text == "🔹 Средний уровень (14 900₽)":
            create_invoice(chat_id, "program_middle")
            return

        if text == "🔹 Спортсмен (19 900₽)":
            create_invoice(chat_id, "program_advanced")
            return

        # ----- ЛИЧНОЕ ВЕДЕНИЕ -----
        if text == "🔥 1 месяц (12 000₽)":
            create_invoice(chat_id, "personal_1month")
            return

        if text == "💪 3 месяца (30 000₽)":
            create_invoice(chat_id, "personal_3month")
            return

        if text == "🏆 6 месяцев (54 000₽)":
            create_invoice(chat_id, "personal_6month")
            return

        if text == "👑 12 месяцев (108 000₽)":
            create_invoice(chat_id, "personal_12month")
            return

        # ----- ОНЛАЙН КОНСУЛЬТАЦИЯ -----
        if text == "🎧 Оплатить консультацию (4 000₽)":
            create_invoice(chat_id, "consult_video")
            return

        # ----- НЕИЗВЕСТНАЯ КОМАНДА -----
        safe_send_message(
            chat_id,
            "❓ Я тебя не понял. Воспользуйся кнопками меню ⬇️\n\n"
            "💡 Чтобы написать мне лично — нажми '📩 Написать мне'",
            reply_markup=main_menu()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в handle_messages: {e}")

# ========================================
# ========== ПЕРЕСЫЛКА ТРЕНЕРУ ==========
# ========================================

def forward_to_trainer(message):
    """Пересылает сообщение тренеру"""
    user_id = message.from_user.id
    
    # Проверяем кнопку "Назад"
    if message.text == "🔙 Назад в главное меню":
        user_states.pop(user_id, None)
        safe_send_message(message.chat.id, "🔁 Главное меню:", reply_markup=main_menu())
        return
    
    user = message.from_user
    user_info = f"{user.first_name} (@{user.username})" if user.username else user.first_name
    
    # Проверяем текст
    if not message.text:
        safe_send_message(
            message.chat.id,
            "❓ Напиши текст сообщения.",
            reply_markup=main_menu()
        )
        user_states.pop(user_id, None)
        return
    
    # Отправляем тренеру
    safe_send_message(
        YOUR_TELEGRAM_ID,
        f"📩 **Сообщение от пользователя**\n\n"
        f"👤 {user_info}\n"
        f"🆔 ID: `{user.id}`\n"
        f"📝 **Текст:**\n{message.text}\n\n"
        f"🕐 {time.strftime('%d.%m.%Y %H:%M')}",
        parse_mode='Markdown'
    )
    
    # Подтверждение пользователю
    safe_send_message(
        message.chat.id,
        "✅ **Сообщение отправлено!**\n\n"
        "Я отвечу в ближайшее время (обычно 2-4 часа).",
        parse_mode='Markdown',
        reply_markup=main_menu()
    )
    
    user_states.pop(user_id, None)

# ========================================
# ========== МЕДИА-ФАЙЛЫ ==========
# ========================================

@bot.message_handler(content_types=['photo', 'video', 'document', 'voice', 'audio'])
def handle_media(message):
    """Обработка медиа-файлов"""
    user_id = message.from_user.id
    
    if user_id not in user_states or user_states[user_id] != "waiting_for_message":
        safe_send_message(
            message.chat.id,
            "❓ Сначала нажми '📩 Написать мне'",
            reply_markup=main_menu()
        )
        return
    
    user = message.from_user
    user_info = f"{user.first_name} (@{user.username})" if user.username else user.first_name
    
    # Определяем тип медиа
    if message.photo:
        media_type = "📷 Фото"
        file_id = message.photo[-1].file_id
        send_func = bot.send_photo
    elif message.video:
        media_type = "🎥 Видео"
        file_id = message.video.file_id
        send_func = bot.send_video
    elif message.document:
        media_type = "📄 Документ"
        file_id = message.document.file_id
        send_func = bot.send_document
    elif message.voice:
        media_type = "🎤 Голосовое"
        file_id = message.voice.file_id
        send_func = bot.send_voice
    elif message.audio:
        media_type = "🎵 Аудио"
        file_id = message.audio.file_id
        send_func = bot.send_audio
    else:
        return
    
    try:
        caption = f"📩 {media_type} от {user_info}\n🆔 ID: `{user.id}`"
        if message.caption:
            caption += f"\n\n📝 Текст: {message.caption}"
        
        send_func(YOUR_TELEGRAM_ID, file_id, caption=caption, parse_mode='Markdown')
        
        safe_send_message(
            message.chat.id,
            f"✅ {media_type} отправлено!",
            reply_markup=main_menu()
        )
        user_states.pop(user_id, None)
        
    except Exception as e:
        logger.error(f"Ошибка при пересылке медиа: {e}")
        safe_send_message(
            message.chat.id,
            "❌ Не удалось отправить файл.",
            reply_markup=main_menu()
        )
        user_states.pop(user_id, None)

# ========================================
# ========== ОПЛАТА ==========
# ========================================

def create_invoice(chat_id, product_key):
    """Создает счет на оплату с поддержкой СБП"""
    product = PRODUCTS.get(product_key)
    if not product:
        safe_send_message(chat_id, "❌ Товар не найден.")
        return
    
    if not PROVIDER_TOKEN:
        safe_send_message(
            chat_id,
            f"❌ Оплата временно недоступна. Напишите @{YOUR_USERNAME}",
            reply_markup=main_menu()
        )
        return
    
    try:
        # Цена в рублях, переводим в копейки для API
        price_rub = int(product["price"])
        price_kop = price_rub * 100
        
        prices = [types.LabeledPrice(label=product["name"], amount=price_kop)]
        
        # Подготовка данных для СБП с чеком
        provider_data = {
            "receipt": {
                "items": [{
                    "description": product["name"][:64],  # Максимум 64 символа
                    "quantity": "1.00",
                    "amount": {
                        "value": str(price_rub),
                        "currency": "RUB"
                    },
                    "vat_code": 1,  # НДС 20%
                    "payment_mode": "full_payment",
                    "payment_subject": "service"  # Услуга
                }]
            }
        }
        
        # Отправляем инвойс с поддержкой СБП
        bot.send_invoice(
            chat_id,
            title=product["name"][:64],  # Ограничение Telegram
            description=product["description"][:255],  # Ограничение Telegram
            invoice_payload=f"product_{product_key}",
            provider_token=PROVIDER_TOKEN,
            currency="RUB",
            prices=prices,
            start_parameter="payment",
            need_name=False,
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            provider_data=json.dumps(provider_data)  # Поддержка СБП
        )
        
        logger.info(f"Счет создан для {chat_id}: {product_key}, сумма: {price_rub} руб. (СБП)")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Ошибка при создании счета: {error_msg}")
        
        # Отправляем сообщение пользователю
        safe_send_message(
            chat_id,
            f"❌ Ошибка при создании счета. Попробуйте позже.\n"
            f"Если ошибка повторяется, напишите @{YOUR_USERNAME}",
            reply_markup=main_menu()
        )
        
        # Уведомляем тренера о неудаче
        try:
            user_info = bot.get_chat(chat_id)
            user_name = user_info.first_name or "Пользователь"
            if user_info.username:
                user_name = f"{user_name} (@{user_info.username})"
            
            notify_trainer_payment_failed(
                user_id=chat_id,
                user_name=user_name,
                product_name=product["name"],
                amount=product["price"],
                error_message=error_msg[:200]
            )
        except Exception as notify_error:
            logger.error(f"Не удалось отправить уведомление тренеру: {notify_error}")

@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout(pre_checkout_query):
    """Предварительная проверка оплаты"""
    try:
        # Проверяем, что товар существует
        payload = pre_checkout_query.invoice_payload
        if not payload or not payload.startswith("product_"):
            bot.answer_pre_checkout_query(
                pre_checkout_query.id,
                ok=False,
                error_message="Неверный товар"
            )
            logger.warning(f"Pre-checkout отклонен: неверный payload {payload}")
            return
        
        product_key = payload.replace("product_", "")
        if product_key not in PRODUCTS:
            bot.answer_pre_checkout_query(
                pre_checkout_query.id,
                ok=False,
                error_message="Товар не найден"
            )
            logger.warning(f"Pre-checkout отклонен: товар {product_key} не найден")
            return
        
        # Все хорошо
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
        logger.info(f"Pre-checkout одобрен для {pre_checkout_query.from_user.id}, товар: {product_key}")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Ошибка в pre_checkout: {error_msg}")
        
        bot.answer_pre_checkout_query(
            pre_checkout_query.id,
            ok=False,
            error_message="Ошибка обработки платежа. Попробуйте позже."
        )
        
        # Уведомляем тренера о неудаче
        try:
            user = pre_checkout_query.from_user
            user_name = f"{user.first_name} (@{user.username})" if user.username else user.first_name
            
            payload = pre_checkout_query.invoice_payload
            product_key = payload.replace("product_", "") if payload and payload.startswith("product_") else "unknown"
            product = PRODUCTS.get(product_key, {})
            product_name = product.get("name", "Неизвестный товар")
            
            total_amount = 0
            if hasattr(pre_checkout_query, 'invoice'):
                total_amount = pre_checkout_query.invoice.total_amount // 100
            
            notify_trainer_payment_failed(
                user_id=user.id,
                user_name=user_name,
                product_name=product_name,
                amount=int(total_amount),
                error_message=f"Pre-checkout ошибка: {error_msg[:200]}"
            )
        except Exception as notify_error:
            logger.error(f"Не удалось отправить уведомление тренеру: {notify_error}")

@bot.message_handler(content_types=['successful_payment'])
def process_successful_payment(message):
    """Обработка успешной оплаты"""
    try:
        payment_info = message.successful_payment
        payload = payment_info.invoice_payload
        amount = payment_info.total_amount // 100  # Переводим из копеек в рубли
        
        # Получаем товар
        product_key = payload.replace("product_", "")
        product = PRODUCTS.get(product_key, {})
        
        if not product:
            logger.error(f"Товар не найден: {product_key}")
            safe_send_message(
                message.chat.id,
                "❌ Товар не найден. Свяжитесь с поддержкой.",
                reply_markup=main_menu()
            )
            return
        
        # Текст для пользователя
        delivery_text = product.get(
            "delivery_text",
            "🎉 Спасибо за оплату!"
        ).format(YOUR_USERNAME)
        
        # Уведомление пользователю
        safe_send_message(
            message.chat.id,
            f"✅ **Оплата прошла успешно!**\n\n"
            f"📦 {product.get('name', 'Услуга')}\n"
            f"💰 {amount} руб.\n"
            f"💳 Способ оплаты: СБП\n\n"
            f"{delivery_text}",
            parse_mode='Markdown',
            reply_markup=main_menu()
        )
        
        # Уведомление тренеру
        user = message.from_user
        user_info = f"{user.first_name} (@{user.username})" if user.username else user.first_name
        
        safe_send_message(
            YOUR_TELEGRAM_ID,
            f"💰 **НОВАЯ ОПЛАТА (СБП)!**\n\n"
            f"👤 {user_info}\n"
            f"🆔 ID: {user.id}\n"
            f"📦 {product.get('name', 'Неизвестно')}\n"
            f"💰 {amount} руб.\n"
            f"💳 Способ: СБП\n"
            f"🕐 {time.strftime('%d.%m.%Y %H:%M')}",
            parse_mode='Markdown'
        )
        
        logger.info(f"Оплата получена: {user.id} - {product_key} - {amount} руб. (СБП)")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Ошибка в обработке платежа: {error_msg}")
        
        safe_send_message(
            message.chat.id,
            f"❌ Ошибка обработки платежа. Напишите @{YOUR_USERNAME}",
            reply_markup=main_menu()
        )
        
        # Уведомляем тренера о неудаче
        try:
            user = message.from_user
            user_name = f"{user.first_name} (@{user.username})" if user.username else user.first_name
            
            if hasattr(message, 'successful_payment'):
                payload = message.successful_payment.invoice_payload
                product_key = payload.replace("product_", "") if payload and payload.startswith("product_") else "unknown"
                product = PRODUCTS.get(product_key, {})
                product_name = product.get("name", "Неизвестный товар")
                amount = message.successful_payment.total_amount // 100 if hasattr(message.successful_payment, 'total_amount') else 0
            else:
                product_name = "Неизвестный товар"
                amount = 0
            
            notify_trainer_payment_failed(
                user_id=user.id,
                user_name=user_name,
                product_name=product_name,
                amount=amount,
                error_message=f"Ошибка обработки: {error_msg[:200]}"
            )
        except Exception as notify_error:
            logger.error(f"Не удалось отправить уведомление тренеру: {notify_error}")

@bot.message_handler(content_types=['failed_payment'])
def process_failed_payment(message):
    """Обработка неудачной оплаты"""
    try:
        user = message.from_user
        user_name = f"{user.first_name} (@{user.username})" if user.username else user.first_name
        
        safe_send_message(
            YOUR_TELEGRAM_ID,
            f"❌ **НЕУДАЧНАЯ ОПЛАТА**\n\n"
            f"👤 {user_name}\n"
            f"🆔 ID: {user.id}\n"
            f"🕐 {time.strftime('%d.%m.%Y %H:%M')}",
            parse_mode='Markdown'
        )
        
        safe_send_message(
            message.chat.id,
            "❌ Оплата не прошла. Попробуйте еще раз или выберите другой способ оплаты.",
            reply_markup=main_menu()
        )
        logger.info(f"Неудачная оплата от пользователя {user.id}")
        
    except Exception as e:
        logger.error(f"Ошибка в process_failed_payment: {e}")

# ========================================
# ========== ЗАПУСК ==========
# ========================================

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🤖 ФИТНЕС-БОТ ЗАПУЩЕН!")
        print("=" * 50)
        print(f"👤 Тренер: @{YOUR_USERNAME}")
        print(f"💳 Провайдер: {'✅ Боевой' if PROVIDER_TOKEN and not PROVIDER_TOKEN.startswith('test_') else '🧪 Тестовый'}")
        print("💳 Способ оплаты: ТОЛЬКО СБП")
        print("=" * 50)
        print("📌 Команды:")
        print("  /start  - Главное меню")
        print("  /help   - Помощь")
        print("  /status - Статус бота (только для тренера)")
        print("=" * 50)
        print("🔄 Бот работает...")
        print("=" * 50)
        
        # Удаляем вебхук перед запуском
        try:
            bot.delete_webhook()
            logger.info("✅ Webhook удален")
        except Exception as e:
            logger.warning(f"Не удалось удалить webhook: {e}")
        
        # Запускаем бота
        bot.infinity_polling(
            timeout=60,
            long_polling_timeout=30,
            interval=0,
            skip_pending=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        print(f"❌ Ошибка: {e}")
        sys.exit(1)