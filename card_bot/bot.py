"""
Telegram бот для безопасного хранения данных банковских карт
"""
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from database import SecureCardDatabase
from ocr_parser import CardParser

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN', '8080110045:AAGK01_8PByIWA-F9o4wJnlGRdQtWu89Uyo')
ALLOWED_USER_ID = os.getenv('ALLOWED_USER_ID', None)  # ID пользователя, который может использовать бота

# Инициализация БД
db = SecureCardDatabase(
    db_path='card_bot/cards.db',
    key_path='card_bot/.encryption_key'
)
parser = CardParser()


def check_user_access(user_id: int) -> bool:
    """Проверяет, имеет ли пользователь доступ к боту"""
    if ALLOWED_USER_ID is None:
        return True
    return str(user_id) == ALLOWED_USER_ID


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_id = update.effective_user.id

    if not check_user_access(user_id):
        await update.message.reply_text("⛔ У вас нет доступа к этому боту.")
        return

    welcome_text = """
🔐 **Бот для безопасного хранения банковских карт**

**Доступные команды:**
/add - Добавить карту (отправьте скриншот)
/list - Показать список карт
/help - Помощь

**Как использовать:**
1. Отправьте скриншот банковской карты
2. Бот автоматически распознает и сохранит данные
3. Используйте /list для просмотра карт

⚠️ **Безопасность:**
- Все данные шифруются локально
- Доступ только у вас
- После отправки скриншота удалите его из чата
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📖 **Помощь**

**Команды:**
/start - Начало работы
/add - Добавить карту вручную
/list - Показать все карты
/delete - Удалить карту
/help - Эта справка

**Отправка скриншота:**
Просто отправьте фото карты боту. Он автоматически:
- Распознает номер карты (16 цифр)
- Найдет CVV код (3-4 цифры)
- Определит срок действия (MM/YY)

**Советы:**
- Делайте четкие фото при хорошем освещении
- Убедитесь, что все цифры видны
- После сохранения проверьте данные
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def list_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список всех сохраненных карт"""
    user_id = update.effective_user.id
    if not check_user_access(user_id):
        await update.message.reply_text("⛔ У вас нет доступа к этому боту.")
        return

    cards = db.get_all_cards()

    if not cards:
        await update.message.reply_text("📭 У вас пока нет сохраненных карт.")
        return

    # Создаем инлайн кнопки для каждой карты
    keyboard = []
    for card_id, card_name, created_at in cards:
        button_text = card_name if card_name else f"Карта #{card_id}"
        keyboard.append([
            InlineKeyboardButton(button_text, callback_data=f"view_{card_id}")
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "💳 **Ваши карты:**\nВыберите карту для просмотра:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает отправленное фото карты"""
    user_id = update.effective_user.id
    if not check_user_access(user_id):
        await update.message.reply_text("⛔ У вас нет доступа к этому боту.")
        return

    # Отправляем сообщение о начале обработки
    processing_msg = await update.message.reply_text("🔄 Обрабатываю изображение...")

    try:
        # Получаем фото (берем самое большое разрешение)
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)

        # Скачиваем фото
        image_bytes = await file.download_as_bytearray()

        # Парсим данные карты
        card_data = parser.parse_card_from_image(bytes(image_bytes))

        card_number = card_data.get('card_number')
        cvv = card_data.get('cvv')
        expiry = card_data.get('expiry')

        # Проверяем, что удалось распознать данные
        if not card_number:
            await processing_msg.edit_text(
                "❌ Не удалось распознать номер карты.\n\n"
                "💡 Попробуйте:\n"
                "- Сделать более четкое фото\n"
                "- Убедиться, что все цифры видны\n"
                "- Улучшить освещение"
            )
            return

        # Валидация номера карты по алгоритму Луна
        if not parser.validate_card_number(card_number):
            await processing_msg.edit_text(
                f"⚠️ Распознан номер карты: `{card_number}`\n"
                "Но он не прошел проверку по алгоритму Луна.\n\n"
                "Возможно, произошла ошибка распознавания. "
                "Проверьте данные перед использованием.",
                parse_mode='Markdown'
            )

        # Показываем распознанные данные
        result_text = "✅ **Данные распознаны:**\n\n"
        result_text += f"💳 Номер карты: `{card_number or 'Не найден'}`\n"
        result_text += f"🔐 CVV: `{cvv or 'Не найден'}`\n"
        result_text += f"📅 Срок: `{expiry or 'Не найден'}`\n\n"

        # Если не все данные распознаны
        if not cvv or not expiry:
            result_text += "⚠️ Не все данные распознаны.\n"
            result_text += "Вы можете добавить их вручную командой /add\n\n"

        result_text += "Сохранить эту карту?"

        # Кнопки для сохранения
        keyboard = [
            [
                InlineKeyboardButton("✅ Сохранить", callback_data=f"save_{card_number}_{cvv}_{expiry}"),
                InlineKeyboardButton("❌ Отмена", callback_data="cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await processing_msg.edit_text(
            result_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"Ошибка обработки фото: {e}")
        await processing_msg.edit_text(
            f"❌ Произошла ошибка при обработке изображения:\n`{str(e)}`",
            parse_mode='Markdown'
        )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия на инлайн кнопки"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if not check_user_access(user_id):
        await query.edit_message_text("⛔ У вас нет доступа к этому боту.")
        return

    data = query.data

    # Отмена
    if data == "cancel":
        await query.edit_message_text("❌ Операция отменена.")
        return

    # Сохранение карты
    if data.startswith("save_"):
        parts = data.split("_")
        if len(parts) >= 4:
            card_number = parts[1]
            cvv = parts[2] if parts[2] != 'None' else None
            expiry = parts[3] if parts[3] != 'None' else None

            # Сохраняем в БД
            card_id = db.add_card(
                card_number=card_number,
                cvv=cvv,
                expiry=expiry,
                card_name=f"Карта {card_number[-4:]}"
            )

            await query.edit_message_text(
                f"✅ Карта сохранена!\n\n"
                f"ID: {card_id}\n"
                f"Используйте /list для просмотра всех карт."
            )
            return

    # Просмотр карты
    if data.startswith("view_"):
        card_id = int(data.split("_")[1])
        card_data = db.get_card(card_id)

        if not card_data:
            await query.edit_message_text("❌ Карта не найдена.")
            return

        card_text = f"💳 **Карта #{card_id}**\n\n"
        card_text += f"**Номер:** `{card_data['card_number']}`\n"
        card_text += f"**CVV:** `{card_data['cvv']}`\n"
        card_text += f"**Срок:** `{card_data['expiry']}`\n\n"
        card_text += "Нажмите на данные для копирования"

        # Кнопки для управления
        keyboard = [
            [InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_{card_id}")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_list")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            card_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return

    # Удаление карты
    if data.startswith("delete_"):
        card_id = int(data.split("_")[1])

        keyboard = [
            [
                InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_{card_id}"),
                InlineKeyboardButton("❌ Отмена", callback_data=f"view_{card_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "⚠️ Вы уверены, что хотите удалить эту карту?",
            reply_markup=reply_markup
        )
        return

    # Подтверждение удаления
    if data.startswith("confirm_delete_"):
        card_id = int(data.split("_")[2])
        if db.delete_card(card_id):
            await query.edit_message_text("✅ Карта удалена.")
        else:
            await query.edit_message_text("❌ Ошибка при удалении карты.")
        return

    # Назад к списку
    if data == "back_to_list":
        cards = db.get_all_cards()

        if not cards:
            await query.edit_message_text("📭 У вас нет сохраненных карт.")
            return

        keyboard = []
        for card_id, card_name, created_at in cards:
            button_text = card_name if card_name else f"Карта #{card_id}"
            keyboard.append([
                InlineKeyboardButton(button_text, callback_data=f"view_{card_id}")
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "💳 **Ваши карты:**\nВыберите карту для просмотра:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return


async def add_card_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавление карты вручную"""
    user_id = update.effective_user.id
    if not check_user_access(user_id):
        await update.message.reply_text("⛔ У вас нет доступа к этому боту.")
        return

    help_text = """
📝 **Добавление карты вручную**

Отправьте данные в формате:
`номер CVV MM/YY`

Пример:
`4276 3801 2345 6789 123 12/25`

Или просто отправьте скриншот карты для автоматического распознавания.
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений для ручного добавления карт"""
    user_id = update.effective_user.id
    if not check_user_access(user_id):
        return

    text = update.message.text

    # Парсим данные из текста
    card_number = parser.parse_card_number(text)
    cvv = parser.parse_cvv(text, card_number)
    expiry = parser.parse_expiry(text)

    if card_number:
        # Сохраняем карту
        card_id = db.add_card(
            card_number=card_number,
            cvv=cvv,
            expiry=expiry,
            card_name=f"Карта {card_number[-4:]}"
        )

        result_text = f"✅ Карта сохранена!\n\n"
        result_text += f"ID: {card_id}\n"
        result_text += f"💳 Номер: `{card_number}`\n"
        result_text += f"🔐 CVV: `{cvv or 'Не указан'}`\n"
        result_text += f"📅 Срок: `{expiry or 'Не указан'}`"

        await update.message.reply_text(result_text, parse_mode='Markdown')
    else:
        await update.message.reply_text(
            "❌ Не удалось распознать данные карты.\n"
            "Используйте формат: `номер CVV MM/YY`",
            parse_mode='Markdown'
        )


def main():
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("list", list_cards))
    application.add_handler(CommandHandler("add", add_card_manual))

    # Обработчики сообщений
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Обработчик кнопок
    application.add_handler(CallbackQueryHandler(button_callback))

    # Запускаем бота
    logger.info("🤖 Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
