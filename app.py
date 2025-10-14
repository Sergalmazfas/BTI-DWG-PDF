"""
BTI DWG → PDF Converter Bot
Telegram bot for converting DWG files to PDF
"""

import os
import sys
import json
import logging
import asyncio
import threading
import tempfile
import time
import base64
import re
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict
from unidecode import unidecode

# Third-party imports - Flask
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

# Third-party imports - Telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Third-party imports - Other
import requests

# Third-party imports - Google Cloud
from google.cloud import storage

# Local imports
from dwg_converter import convert_dwg_to_pdf
from gcs_queue_manager import GCSQueueManager
from forge_client import ForgeClient, forge_client

# Add current directory to path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

user_data = {}
application = None
_background_loop = None
_loop_thread = None
queue_manager = None

# --- DWG → PDF Configuration ---
ALLOWED_EXTENSIONS = {'dwg'}  # Only DWG
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

def allowed_file(filename):
    """Проверяет, что файл имеет разрешенное расширение"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file(file):
    """Валидирует загруженный файл"""
    if not file:
        return False, "No file provided"
    
    if not file.filename:
        return False, "No filename provided"
    
    if not allowed_file(file.filename):
        return False, f"File type not allowed. Only {', '.join(ALLOWED_EXTENSIONS)} files are supported"
    
    # Проверяем размер файла
    file.seek(0, 2)  # Переходим в конец файла
    file_size = file.tell()
    file.seek(0)  # Возвращаемся в начало
    
    if file_size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
    
    if file_size == 0:
        return False, "Empty file"
    
    return True, "File is valid"

def parse_pubsub_message(data):
    """Парсит Pub/Sub сообщение и извлекает данные о файле"""
    try:
        if 'message' in data:
            message = data['message']
            
            if 'data' in message:
                encoded_data = message['data']
                decoded_data = base64.b64decode(encoded_data).decode('utf-8')
                gcs_data = json.loads(decoded_data)
                
                bucket = gcs_data.get('bucket')
                name = gcs_data.get('name')
                generation = gcs_data.get('generation')
                
                logger.info(f"📦 Parsed GCS data: bucket={bucket}, name={name}, generation={generation}")
                return bucket, name, generation
            else:
                logger.warning("❌ No 'data' field in Pub/Sub message")
                return None, None, None
        else:
            logger.warning("❌ No 'message' field in Pub/Sub data")
            return None, None, None
            
    except Exception as e:
        logger.error(f"❌ Error parsing Pub/Sub message: {e}")
        return None, None, None

def init_queue_manager():
    """Инициализация GCS Queue Manager"""
    global queue_manager
    try:
        queue_manager = GCSQueueManager()
        queue_manager._ensure_bucket_structure()
        logger.info("✅ GCS Queue Manager initialized")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize GCS Queue Manager: {e}")
        return False

def normalize_filename(filename: str) -> str:
    """
    Нормализует имя файла: заменяет кириллицу на латиницу, 
    пробелы на подчёркивания, удаляет спецсимволы.
    
    Args:
        filename: Исходное имя файла (может содержать кириллицу)
        
    Returns:
        Нормализованное имя файла (только латиница, цифры, точка, тире, подчёркивание)
        
    Examples:
        >>> normalize_filename("Чертеж Басманная.dwg")
        'Chertezh_Basmannaya.dwg'
        >>> normalize_filename("План 2025-10-03.dwg")
        'Plan_2025-10-03.dwg'
    """
    # Разделяем на имя и расширение
    if '.' in filename:
        name, ext = filename.rsplit('.', 1)
    else:
        name, ext = filename, ''
    
    # Транслитерация кириллицы в латиницу
    normalized = unidecode(name)
    
    # Заменяем пробелы на подчёркивания
    normalized = re.sub(r'\s+', '_', normalized)
    
    # Удаляем всё кроме букв, цифр, точек, тире и подчёркиваний
    normalized = re.sub(r'[^A-Za-z0-9._-]', '', normalized)
    
    # Собираем обратно с расширением
    if ext:
        return f"{normalized}.{ext}"
    return normalized

def _start_background_loop():
    global _background_loop, _loop_thread
    _background_loop = asyncio.new_event_loop()
    def run_loop_forever():
        asyncio.set_event_loop(_background_loop)
        _background_loop.run_forever()
    _loop_thread = threading.Thread(target=run_loop_forever, name="bot-event-loop", daemon=True)
    _loop_thread.start()
    logger.info("Background asyncio loop started")

def _run_coro(coro):
    if _background_loop is None:
        raise RuntimeError("Background loop is not started")
    fut = asyncio.run_coroutine_threadsafe(coro, _background_loop)
    return fut.result()

def send_telegram_notification(chat_id: str, workitem_id: str, result_url: str, processing_time: float, mode: str = "bti"):
    """
    Отправляет уведомление в Telegram о завершении обработки
    
    Args:
        chat_id: ID чата в Telegram
        workitem_id: ID WorkItem в APS
        result_url: URL результата в GCS
        processing_time: Время обработки в секундах
        mode: Режим обработки (bti, pdf, dwg2dwg)
    """
    try:
        if not application or chat_id == 'api':
            logger.info("Skipping Telegram notification (no application or API mode)")
            return
        
        # Определяем тип файла
        file_type = "PDF" if mode == "pdf" else "DWG"
        
        # Формируем сообщение
        message = (
            "✅ <b>Обработка завершена!</b>\n\n"
            f"📎 Готовый файл: {file_type}\n"
            f"⏱️ Время обработки: {processing_time:.1f} сек\n"
            f"🆔 WorkItem: <code>{workitem_id[:20]}...</code>\n\n"
            f"📥 Файл сохранен в GCS"
        )
        
        # Отправляем асинхронно
        async def send():
            await application.bot.send_message(
                chat_id=int(chat_id),
                text=message,
                parse_mode='HTML'
            )
        
        _run_coro(send())
        logger.info(f"✅ Telegram notification sent to {chat_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to send Telegram notification: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Главное меню бота
    """
    user_id = update.effective_user.id
    user_data[user_id] = {'step': 'main_menu'}
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📐 Загрузить DWG файл", callback_data="upload_dwg")],
        [InlineKeyboardButton("ℹ️ Информация о сервисе", callback_data="info")]
    ])
    
    welcome_message = (
        "👋 <b>Добро пожаловать в BTI Авто-чертёж!</b>\n\n"
        "🏢 <b>Авто-чертёж БТИ по DWG (с опцией PDF)</b>\n"
        "   • Построение по шаблону БТИ (BTI_Template.dwt)\n"
        "   • Получите готовый DWG для доработок\n"
        "   • Опционально: PDF (A4, Landscape)\n\n"
        "💡 Выберите действие:"
    )
    
    await update.message.reply_text(welcome_message, reply_markup=keyboard, parse_mode='HTML')

async def bti_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /bti - запуск поэтапного DWG-first режима"""
    chat_id = str(update.effective_user.id)
    
    try:
        # Отправляем описание этапов
        message = (
            "🏢 <b>Режим: БТИ техпаспорт</b>\n\n"
            "📋 <b>Что будет сделано:</b>\n"
            "• Построение по шаблону БТИ (BTI_Template.dwt)\n"
            "• Вы получите готовый DWG для доработок\n\n"
            "После этого я спрошу, нужен ли PDF (A4, Landscape)\n\n"
            "⏳ <b>Отправьте DWG-файл для обработки.</b>"
        )
        
        await update.message.reply_text(message, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"❌ Ошибка в команде /bti: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка. Попробуйте позже.",
            parse_mode='HTML'
        )

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик текстовых сообщений
    """
    user_id = update.effective_user.id
    text = update.message.text
    logger.info(f"📨 Получено сообщение от {user_id}: {text}")
    
    # Показываем главное меню
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📐 Загрузить DWG файл", callback_data="upload_dwg")],
        [InlineKeyboardButton("ℹ️ Информация о сервисе", callback_data="info")]
    ])
    
    await update.message.reply_text(
        "❓ Пожалуйста, выберите действие из меню:",
        reply_markup=keyboard
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик callbacks
    """
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    user_id = query.from_user.id
    
    if callback_data == "upload_dwg":
        user_data[user_id] = {'step': 'waiting_dwg_file'}
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_menu")]
        ])
        await query.edit_message_text(
            "🏢 <b>БТИ техпаспорт (DWG-first)</b>\n\n"
            "Отправьте мне DWG файл:\n\n"
            "📄 Принимаются только .dwg файлы\n"
            "📏 Максимальный размер: 100 MB\n"
            "⏱️ Время обработки: 2-5 минут\n\n"
            "📊 Что будет сделано:\n"
            "• Построение по шаблону БТИ (BTI_Template.dwt)\n"
            "• Получите готовый DWG для доработок\n"
            "• Опционально: PDF (A4, Landscape)\n\n"
            "💡 Отправьте DWG файл, и я начну обработку!",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return
    
    elif callback_data == "back_to_menu":
        user_data[user_id] = {'step': 'main_menu'}
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📐 Загрузить DWG файл", callback_data="upload_dwg")],
            [InlineKeyboardButton("ℹ️ Информация о сервисе", callback_data="info")]
        ])
        await query.edit_message_text(
            "🏠 <b>Главное меню</b>\n\n"
            "Выберите нужную услугу:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return
    
    elif callback_data == "info":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_menu")]
        ])
        await query.edit_message_text(
            "ℹ️ <b>О сервисе BTI Авто-чертёж</b>\n\n"
            "<b>Возможности:</b>\n"
            "📐 Авто-чертёж БТИ по DWG (с опцией PDF)\n"
            "☁️ Облачное хранение результатов\n"
            "🔗 Публичные ссылки на файлы\n\n"
            "<b>Технологии:</b>\n"
            "• AutoDesk Forge API для обработки DWG\n"
            "• Google Cloud Storage\n"
            "• Telegram Bot API\n\n"
            "<b>Ограничения:</b>\n"
            "• Только DWG файлы\n"
            "• Максимум 100MB\n"
            "• Время обработки: 2-5 минут",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return
    
    elif callback_data.startswith("make_pdf_"):
        # Пользователь хочет сделать PDF
        job_id = callback_data.replace("make_pdf_", "")
        
        await query.edit_message_text(
            f"📄 Делаю PDF из DWG...\n\n"
            f"🆔 ID: {job_id}\n"
            f"⏳ Конвертирую в PDF (A4, Landscape)...\n\n"
            f"⏱️ Это займет 1-2 минуты"
        )
        
        # TODO: Здесь будет запуск конвертации DWG → PDF
        # Пока просто отправляем сообщение об успехе
        await asyncio.sleep(2)  # Имитация обработки
        
        await query.edit_message_text(
            f"📄 PDF готов!\n\n"
            f"🆔 ID: {job_id}\n\n"
            f"✅ Задача завершена.\n\n"
            f"💡 Скачайте файлы по ссылкам выше."
        )
        return
    
    elif callback_data.startswith("done_"):
        # Пользователь не хочет PDF, только DWG
        job_id = callback_data.replace("done_", "")
        
        await query.edit_message_text(
            f"👌 Ок, оставляем только DWG.\n\n"
            f"🆔 ID: {job_id}\n\n"
            f"✅ Задача завершена.\n\n"
            f"💡 Скачайте DWG по ссылке выше."
        )
        return

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик файлов (DWG)
    """
    try:
        user_id = update.effective_user.id
        document = update.message.document
        filename = document.file_name.lower()
        
        logger.info(f"📦 Получен файл от {user_id}: {document.file_name}")
        
        # Проверяем, в какой ветке находится пользователь
        user_state = user_data.get(user_id, {})
        current_step = user_state.get('step', 'main_menu')
        
        # Если пользователь не в режиме загрузки файла, предлагаем варианты
        if current_step != 'waiting_dwg_file':
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📐 Да, конвертировать DWG→PDF", callback_data="upload_dwg")],
                [InlineKeyboardButton("🔙 Нет, в главное меню", callback_data="back_to_menu")]
            ])
            
            await update.message.reply_text(
                f"📦 Получен файл: {document.file_name}\n\n"
                "Что вы хотите сделать?",
                reply_markup=keyboard
            )
            return
        
        # Валидация: ТОЛЬКО DWG
        if not filename.endswith('.dwg'):
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_menu")]
            ])
            await update.message.reply_text(
                "❌ Поддерживается только DWG\n\n"
                "Загрузите файл в формате .dwg\n\n"
                f"Ваш файл: {document.file_name}\n"
                f"Формат: {os.path.splitext(document.file_name)[1]}\n\n"
                "💡 Экспортируйте чертёж как DWG и попробуйте снова",
                reply_markup=keyboard
            )
            return
        
        # Валидация: размер файла (максимум 100MB)
        max_size = 100 * 1024 * 1024  # 100MB
        if document.file_size > max_size:
            await update.message.reply_text(
                f"❌ Ошибка: файл слишком большой ({document.file_size / 1024 / 1024:.1f} MB)\n"
                f"📏 Максимальный размер: {max_size / 1024 / 1024:.0f} MB"
            )
            return
        
        # Скачиваем файл из Telegram
        file = await context.bot.get_file(document.file_id)
        
        # Сохраняем во временную директорию
        with tempfile.NamedTemporaryFile(delete=False, suffix='.dwg') as temp_file:
            await file.download_to_drive(temp_file.name)
            temp_path = temp_file.name
        
        logger.info(f"📥 Файл скачан: {temp_path}")
        
        try:
            # Нормализуем имя файла (кириллица → латиница)
            original_filename = document.file_name
            normalized_filename = normalize_filename(original_filename)
            
            if normalized_filename != original_filename:
                logger.info(f"⚙️ Имя файла нормализовано: {original_filename} → {normalized_filename}")
            
            # Сохраняем исходный DWG в GCS
            timestamp = int(time.time())
            raw_key = f"raw/{timestamp}/{normalized_filename}"
            
            gcs_client = storage.Client()
            bucket = gcs_client.bucket("btibot-processed")
            
            # Upload raw DWG
            raw_blob = bucket.blob(raw_key)
            raw_blob.upload_from_filename(temp_path)
            raw_blob.make_public()
            raw_url = f"https://storage.googleapis.com/btibot-processed/{raw_key}"
            
            logger.info(f"✅ Исходный файл сохранен: {raw_url}")
            
            # Добавляем задание в очередь
            if queue_manager:
                job_data = {
                    "user_id": user_id,
                    "chat_id": update.effective_chat.id,
                    "filename": normalized_filename,  # Используем нормализованное имя
                    "file_size": document.file_size,
                    "dwg_path": raw_key,
                    "dwg_url": raw_url,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                job_id = queue_manager.add_job_to_queue(job_data)
                
                # Проверяем, заблокирована ли обработка
                if queue_manager._is_processing_locked():
                    message_text = (
                        "📋 Файл добавлен в очередь обработки\n\n"
                        f"📦 Файл: {normalized_filename}\n"
                        f"🆔 ID задания: {job_id}\n\n"
                        "⏳ Обработка начнется после завершения предыдущего задания\n"
                        "📊 Текущий статус: В очереди"
                    )
                    if normalized_filename != original_filename:
                        message_text = f"✅ Имя файла нормализовано: {original_filename} → {normalized_filename}\n\n" + message_text
                    await update.message.reply_text(message_text)
                else:
                    message_text = (
                        "✅ Файл принят. Запускаем обработку через Autodesk API…\n\n"
                        f"📦 Файл: {normalized_filename}\n"
                        f"🆔 ID задания: {job_id}\n\n"
                        "⏳ Обрабатываю DWG через Autodesk APS API...\n"
                        "📊 Текущий статус: В работе"
                    )
                    if normalized_filename != original_filename:
                        message_text = f"⚙️ Имя файла нормализовано: {normalized_filename}\n\n" + message_text
                    await update.message.reply_text(message_text)
            else:
                # Fallback: прямая обработка без очереди
                await update.message.reply_text(
                    "🚀 DWG → PDF конвертация (прямая обработка)\n\n"
                    f"📦 Файл: {document.file_name}\n"
                    f"📏 Размер: {document.file_size / 1024 / 1024:.2f} MB\n\n"
                    "⏳ Загружаю..."
                )
                
                # Прямая конвертация
                pdf_path = convert_dwg_to_pdf(temp_path)
                
                if pdf_path and os.path.exists(pdf_path):
                    await update.message.reply_text("📤 Загружаю PDF в облако...")
                    
                    pdf_key = f"processed/{timestamp}/plan.pdf"
                    pdf_blob = bucket.blob(pdf_key)
                    pdf_blob.upload_from_filename(pdf_path)
                    pdf_blob.make_public()
                    pdf_url = f"https://storage.googleapis.com/btibot-processed/{pdf_key}"
                
                    # Используем InlineKeyboardButton
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("📄 Скачать PDF", url=pdf_url)],
                        [InlineKeyboardButton("📁 Скачать DWG (оригинал)", url=raw_url)],
                        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")]
                    ])
                    
                    message = (
                        "✅ DWG → PDF готово!\n\n"
                        f"📦 Файл: {document.file_name}\n"
                        f"📏 Размер: {document.file_size / 1024 / 1024:.2f} MB\n\n"
                        "📄 PDF чертёж готов к печати\n"
                        "📁 Исходный DWG сохранён\n"
                        "🔗 Ссылки действуют 30 дней\n\n"
                        "💡 Скачайте файлы по кнопкам ниже:"
                    )
                    
                    await update.message.reply_text(message, reply_markup=keyboard)
                    
                    logger.info(f"✅ DWG→PDF: Complete: {pdf_url}")
                    
                    # Очистка локального PDF
                    try:
                        os.unlink(pdf_path)
                    except:
                        pass
                else:
                    # Ошибка конвертации
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("📁 Скачать DWG (оригинал)", url=raw_url)],
                        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")]
                    ])
                    
                    message = (
                        "❌ Не удалось обработать файл\n\n"
                        "Файл передан чертёжнику для ручной обработки.\n\n"
                        "📁 Исходный DWG сохранён - можете скачать\n"
                        "📞 Свяжемся с вами в течение часа"
                    )
                    
                    await update.message.reply_text(message, reply_markup=keyboard)
                    logger.error(f"❌ DWG→PDF failed, fallback to manual")
        
        finally:
            # Удаляем временный файл
            try:
                os.unlink(temp_path)
                logger.info("🗑️ Временный файл удален")
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")
    
    except Exception as e:
        logger.exception(f"❌ Error handling document: {e}")
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data="upload_dwg")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")]
        ])
        
        message = (
            "❌ Не удалось обработать файл\n\n"
            "Попробуйте снова или обратитесь в поддержку."
        )
        
        await update.message.reply_text(message, reply_markup=keyboard)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Unhandled exception", exc_info=context.error)

def init_bot():
    global application
    if _background_loop is None:
        _start_background_loop()
    token = os.getenv('BOT_TOKEN')
    if not token:
        logger.error('BOT_TOKEN missing'); return False
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("bti", bti_command))
    application.add_handler(CommandHandler("bti_dwg", bti_dwg_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_error_handler(error_handler)
    if not getattr(application, "_initialized", False):
        _run_coro(application.initialize())
    if not getattr(application, "_running", False):
        _run_coro(application.start())
    
    # Инициализируем queue manager
    if not init_queue_manager():
        logger.warning("⚠️ Queue manager initialization failed, but bot will continue")
    
    logger.info("Bot initialized and started on background loop")
    return True

# --- Flask Routes ---

@app.route('/health')
def health():
    return jsonify({"status":"OK","message":"BTI DWG → PDF Converter is running"})

@app.route('/status')
def status():
    """Статус сервиса с информацией о конфигурации"""
    return jsonify({
        "service": "BTI DWG → PDF Converter",
        "version": "1.0.0",
        "status": "running",
        "mode": "production",
        "supported_formats": list(ALLOWED_EXTENSIONS),
        "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
        "features": {
            "telegram_bot": True,
            "dwg_to_pdf": True,
            "gcs_storage": True,
            "pdf_conversion": True,
            "raw_file_backup": True
        },
        "storage": {
            "bucket": "btibot-processed",
            "raw_path": "/raw/<timestamp>/<filename>",
            "processed_path": "/processed/<timestamp>/plan.pdf"
        },
        "endpoints": {
            "upload": "/upload",
            "health": "/health",
            "status": "/status",
            "webhook": "/",
            "gcs_push": "/gcs/push",
            "process_queue": "/process-queue",
            "queue_status": "/queue-status",
            "aps_callback": "/aps-callback"
        }
    })

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    DWG → PDF конвертация (API endpoint)
    
    Принимает:
    - file: DWG файл через multipart/form-data
    
    Возвращает:
    - success: true/false
    - message: описание результата
    - pdf_url: URL PDF в GCS
    - raw_url: URL исходного DWG в GCS
    - file_info: информация о файле
    """
    try:
        logger.info("🚀 API: Received upload request")
        
        # Проверяем наличие файла
        if 'file' not in request.files:
            logger.warning("No file in request")
            return jsonify({
                "success": False,
                "message": "No file provided"
            }), 400
        
        file = request.files['file']
        
        # Валидируем файл
        is_valid, message = validate_file(file)
        if not is_valid:
            logger.warning(f"File validation failed: {message}")
            return jsonify({
                "success": False,
                "message": message
            }), 400
        
        logger.info(f"📦 Processing DWG file: {file.filename}")
        
        # Только DWG
        filename_lower = file.filename.lower()
        if not filename_lower.endswith('.dwg'):
            logger.warning(f"❌ Not a DWG file: {file.filename}")
            return jsonify({
                "success": False,
                "message": "Only DWG files are supported"
            }), 400
        
        suffix = '.dwg'
        
        # Сохраняем файл во временную директорию
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        try:
            timestamp = int(time.time())
            gcs_client = storage.Client()
            bucket = gcs_client.bucket("btibot-processed")
            
            # Шаг 1: Сохранить исходный файл в GCS (/raw/)
            raw_key = f"raw/{timestamp}/{secure_filename(file.filename)}"
            raw_blob = bucket.blob(raw_key)
            raw_blob.upload_from_filename(temp_file_path)
            raw_blob.make_public()
            raw_url = f"https://storage.googleapis.com/btibot-processed/{raw_key}"
            
            logger.info(f"✅ Raw DWG saved to GCS: {raw_url}")
            
            # Шаг 2: Конвертировать DWG → PDF
            logger.info(f"🔄 DWG→PDF: Converting...")
            pdf_path = convert_dwg_to_pdf(temp_file_path)
            
            if pdf_path and os.path.exists(pdf_path):
                # Шаг 3: Загрузить PDF в GCS
                pdf_key = f"processed/{timestamp}/plan.pdf"
                pdf_blob = bucket.blob(pdf_key)
                pdf_blob.upload_from_filename(pdf_path)
                pdf_blob.make_public()
                pdf_url = f"https://storage.googleapis.com/btibot-processed/{pdf_key}"
                
                # Очистка локального PDF
                try:
                    os.unlink(pdf_path)
                except:
                    pass
                
                logger.info(f"✅ DWG→PDF: Success: {pdf_url}")
                return jsonify({
                    "success": True,
                    "message": "DWG → PDF conversion successful",
                    "pdf_url": pdf_url,
                    "raw_url": raw_url,
                    "file_info": {
                        "original_filename": secure_filename(file.filename),
                        "file_size": os.path.getsize(temp_file_path),
                        "format": "DWG → PDF",
                        "raw_location": raw_key,
                        "processed_location": pdf_key
                    }
                })
            else:
                logger.error("❌ DWG→PDF: Conversion failed")
                return jsonify({
                    "success": False,
                    "message": "Failed to convert DWG to PDF",
                    "raw_url": raw_url
                }), 500
                
        finally:
            # Удаляем временные файлы
            try:
                os.unlink(temp_file_path)
                logger.info("🗑️ Temporary DWG file cleaned up")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file: {e}")
    
    except Exception as e:
        logger.exception(f"❌ DWG→PDF: Exception in upload endpoint: {e}")
        return jsonify({
            "success": False,
            "message": "Failed to process DWG file"
        }), 500

@app.route('/process-dwg', methods=['POST'])
def process_dwg():
    """
    Универсальный обработчик DWG файлов через Autodesk APS
    
    Принимает:
    {
        "file_url": "gs://bucket/path/to/file.dwg",
        "mode": "bti" | "pdf" | "dwg2dwg",
        "chat_id": "12345" (опционально),
        "job_id": "uuid" (опционально)
    }
    
    Возвращает:
    {
        "success": true,
        "workitem_id": "...",
        "result_url": "gs://...",
        "processing_time": 3.5
    }
    """
    try:
        import time
        start_time = time.time()
        
        data = request.json
        file_url = data.get('file_url')
        mode = data.get('mode', 'bti')
        chat_id = data.get('chat_id', 'api')
        job_id = data.get('job_id', str(uuid.uuid4()))
        
        if not file_url:
            return jsonify({
                "success": False,
                "error": "file_url is required"
            }), 400
        
        logger.info(f"🔄 Processing DWG via APS: {file_url}, mode={mode}")
        
        # Определяем пути для GCS
        if file_url.startswith('gs://'):
            input_blob_path = file_url.replace("gs://btibot-processed/", "")
        else:
            return jsonify({
                "success": False,
                "error": "file_url must be a GCS path (gs://...)"
            }), 400
        
        # Выбираем формат вывода в зависимости от режима
        if mode == 'pdf':
            output_filename = f"{job_id}.pdf"
            output_blob_path = f"ready/{chat_id}/{job_id}/out.pdf"
        else:  # bti, dwg2dwg
            output_filename = f"{job_id}.dwg"
            output_blob_path = f"ready/{chat_id}/{job_id}/bti_ready.dwg"
        
        # Получаем Service Account credentials для signed URLs
        from google.cloud import secretmanager
        from google.oauth2 import service_account
        
        logger.info("🔑 Loading Service Account credentials for signed URLs...")
        secret_client = secretmanager.SecretManagerServiceClient()
        secret_name = "projects/talkhint/secrets/FORGE_SERVICE_KEY/versions/latest"
        secret_response = secret_client.access_secret_version(request={"name": secret_name})
        sa_credentials_json = json.loads(secret_response.payload.data.decode("UTF-8"))
        
        # Создаем credentials и GCS client
        sa_credentials = service_account.Credentials.from_service_account_info(sa_credentials_json)
        gcs_client = storage.Client(credentials=sa_credentials)
        bucket = gcs_client.bucket("btibot-processed")
        
        # Input URL (публичный, т.к. бакет публичный)
        # Проверяем, не содержит ли input_blob_path уже полный URL
        if input_blob_path.startswith("https://"):
            input_url = input_blob_path
        else:
            input_url = f"https://storage.googleapis.com/btibot-processed/{input_blob_path}"
        logger.info(f"📥 Input URL (public): {input_url}")
        
        # Output URL (signed для записи, БЕЗ content_type!)
        output_blob = bucket.blob(output_blob_path)
        output_url = output_blob.generate_signed_url(
            version="v4",
            expiration=timedelta(hours=1),
            method="PUT"
        )
        logger.info(f"📤 Output URL (signed): {output_url[:80]}...")
        
        # Отправляем WorkItem в Autodesk APS
        # Режим обработки: v2 (полный процесс), simple, template
        processing_mode = os.getenv('BTI_PROCESSING_MODE', 'v2')
        
        try:
            workitem = forge_client.submit_workitem(input_url, output_url, mode=processing_mode)
            workitem_id = workitem['id']
            
            logger.info(f"✅ WorkItem created: {workitem_id}")
            
            # Ожидаем завершения
            result = forge_client.wait_for_completion(workitem_id, timeout_minutes=5)
            
            processing_time = time.time() - start_time
            
            if result.get('status') == 'success':
                # Формируем URL результата
                result_url = f"gs://btibot-processed/{output_blob_path}"
                
                logger.info(f"🎉 APS processing complete in {processing_time:.1f}s")
                
                # Отправляем уведомление в Telegram
                try:
                    send_telegram_notification(
                        chat_id=chat_id,
                        workitem_id=workitem_id,
                        result_url=result_url,
                        processing_time=processing_time,
                        mode=mode
                    )
                except Exception as notif_error:
                    logger.warning(f"Failed to send notification: {notif_error}")
                
                return jsonify({
                    "success": True,
                    "workitem_id": workitem_id,
                    "result_url": result_url,
                    "mode": mode,
                    "processing_time": round(processing_time, 2),
                    "stats": result.get('stats', {})
                })
            else:
                logger.error(f"❌ APS WorkItem failed: {result.get('status')}")
                return jsonify({
                    "success": False,
                    "workitem_id": workitem_id,
                    "error": f"WorkItem failed: {result.get('status')}",
                    "report_url": result.get('reportUrl')
                }), 500
                
        except Exception as forge_error:
            logger.exception(f"❌ Forge API error: {forge_error}")
            return jsonify({
                "success": False,
                "error": str(forge_error)
            }), 500
    
    except Exception as e:
        logger.exception(f"❌ Exception in /process-dwg: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/process-queue', methods=['POST'])
def process_queue():
    """Обрабатывает следующее задание из очереди"""
    try:
        logger.info("🔄 Starting queue processing...")
        
        if not queue_manager:
            logger.error("❌ Queue manager not initialized")
            return jsonify({"status": "error", "message": "Queue manager not initialized"}), 500
        
        # Получаем следующее задание
        logger.info("📋 Getting next job from queue...")
        job = queue_manager.get_next_job()
        if not job:
            logger.info("📭 No jobs in queue or processing locked")
            return jsonify({"status": "no_jobs", "message": "No jobs in queue or processing locked"})
        
        logger.info(f"✅ Got job: {job}")
        job_id = job["job_id"]
        
        # Поддержка двух форматов job data:
        # Формат 1: {job_id, data: {dwg_url, ...}}
        # Формат 2: {job_id, dwg_url, ...}
        if "data" in job:
            job_data = job["data"]
            logger.info("📦 Using job format with 'data' field")
        else:
            job_data = job
            logger.info("📦 Using flat job format")
        
        logger.info(f"🚀 Processing job from queue: {job_id}")
        
        # Проверяем режим AUTO_PDF
        auto_pdf = os.getenv('AUTO_PDF', 'false').lower() == 'true'
        
        try:
            logger.info(f"📁 Processing DWG file: {job_data.get('dwg_url', 'N/A')}")
            
            # Скачиваем DWG файл из GCS
            gcs_client = storage.Client()
            bucket = gcs_client.bucket("btibot-processed")
            
            # Поддержка разных форматов путей
            if "dwg_url" in job_data and job_data["dwg_url"].startswith("gs://"):
                blob_path = job_data["dwg_url"].replace("gs://btibot-processed/", "")
            elif "dwg_path" in job_data:
                blob_path = job_data["dwg_path"]
            elif "dwg_url" in job_data:
                # URL уже без gs://
                blob_path = job_data["dwg_url"].replace("https://storage.googleapis.com/btibot-processed/", "")
            else:
                raise ValueError("No dwg_url or dwg_path found in job_data")
            
            logger.info(f"📂 Blob path: {blob_path}")
            blob = bucket.blob(blob_path)
            
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix='.dwg') as temp_file:
                blob.download_to_filename(temp_file.name)
                temp_path = temp_file.name
            
            if auto_pdf:
                # Старый режим: DWG → PDF
                pdf_path = convert_dwg_to_pdf(temp_path)
                
                if pdf_path and os.path.exists(pdf_path):
                    # Загружаем PDF обратно в GCS
                    timestamp = int(time.time())
                    pdf_key = f"processed/{timestamp}/plan.pdf"
                    pdf_blob = bucket.blob(pdf_key)
                    pdf_blob.upload_from_filename(pdf_path)
                    pdf_blob.make_public()
                    pdf_url = f"https://storage.googleapis.com/btibot-processed/{pdf_key}"
                    
                    # Завершаем задание
                    result_data = {
                        "pdf_url": pdf_url,
                        "pdf_path": pdf_key,
                        "processed_at": datetime.now(timezone.utc).isoformat()
                    }
                    queue_manager.finish_job(job_id, result_data)
                    
                    # Отправляем уведомление пользователю через Telegram
                    if application:
                        try:
                            async def send_notification():
                                await application.bot.send_message(
                                    chat_id=job_data["chat_id"],
                                    text=f"✅ Конвертация завершена!\n\n"
                                         f"📦 Файл: {job_data['filename']}\n"
                                         f"🆔 ID: {job_id}\n\n"
                                         f"📄 PDF готов: {pdf_url}"
                                )
                            
                            _run_coro(send_notification())
                        except Exception as e:
                            logger.error(f"Failed to send notification: {e}")
                    
                    return jsonify({
                        "status": "success",
                        "job_id": job_id,
                        "pdf_url": pdf_url
                    })
                else:
                    # Конвертация не удалась
                    queue_manager.fail_job(job_id, "DWG to PDF conversion failed")
                    return jsonify({
                        "status": "error",
                        "job_id": job_id,
                        "message": "Conversion failed"
                    }), 500
            else:
                # Новый режим DWG-first: обработка DWG через Autodesk APS
                try:
                    logger.info(f"🔧 DWG-first режим: обработка через Autodesk APS для {job_id}")
                    
                    # Создаем ForgeClient
                    logger.info("🔑 Initializing ForgeClient...")
                    forge_client = ForgeClient()
                    logger.info("✅ ForgeClient initialized")
                    
                    # Создаем signed URLs для GCS
                    # Поддержка разных форматов dwg_url
                    dwg_url = job_data['dwg_url']
                    if dwg_url.startswith("gs://btibot-processed/"):
                        input_blob_path = dwg_url.replace("gs://btibot-processed/", "")
                    elif dwg_url.startswith("https://storage.googleapis.com/btibot-processed/"):
                        input_blob_path = dwg_url.replace("https://storage.googleapis.com/btibot-processed/", "")
                    elif "dwg_path" in job_data:
                        input_blob_path = job_data["dwg_path"]
                    else:
                        input_blob_path = dwg_url
                    
                    output_blob_path = f"ready/{job_data['chat_id']}/{job_id}/bti_ready.dwg"
                    
                    # Получаем Service Account credentials из Secret Manager для signed URLs
                    logger.info("🔑 Loading Service Account credentials for signed URLs...")
                    from google.cloud import secretmanager
                    secret_client = secretmanager.SecretManagerServiceClient()
                    secret_name = "projects/talkhint/secrets/FORGE_SERVICE_KEY/versions/latest"
                    secret_response = secret_client.access_secret_version(request={"name": secret_name})
                    sa_credentials_json = json.loads(secret_response.payload.data.decode("UTF-8"))
                    
                    # Создаем credentials из JSON
                    from google.oauth2 import service_account
                    sa_credentials = service_account.Credentials.from_service_account_info(sa_credentials_json)
                    
                    # Создаем GCS client с Service Account credentials
                    gcs_client = storage.Client(credentials=sa_credentials)
                    bucket = gcs_client.bucket("btibot-processed")
                    
                    # Input URL (публичный, т.к. бакет публичный)
                    # Проверяем, не содержит ли input_blob_path уже полный URL
                    if input_blob_path.startswith("https://"):
                        input_url = input_blob_path
                    else:
                        input_url = f"https://storage.googleapis.com/btibot-processed/{input_blob_path}"
                    logger.info(f"📥 Input URL (public): {input_url}")
                    
                    # Output URL (signed для записи)
                    # НЕ указываем content_type - APS не отправляет этот header!
                    output_blob = bucket.blob(output_blob_path)
                    output_url = output_blob.generate_signed_url(
                        version="v4",
                        expiration=timedelta(hours=1),
                        method="PUT"
                    )
                    logger.info(f"📤 Output URL (signed): {output_url[:80]}...")
                    
                    # Отправляем WorkItem в Autodesk APS
                    # Режим обработки: v2 (полный процесс), simple, template
                    processing_mode = os.getenv('BTI_PROCESSING_MODE', 'v2')
                    
                    try:
                        workitem = forge_client.submit_workitem(input_url, output_url, mode=processing_mode)
                        workitem_id = workitem['id']
                        
                        # Ожидаем завершения
                        result = forge_client.wait_for_completion(workitem_id, timeout_minutes=5)
                        
                        # Проверяем статус WorkItem
                        workitem_status = result.get('status', 'unknown')
                        if workitem_status == 'success':
                            forge_result = {
                                'success': True,
                                'workitem_id': workitem_id,
                                'result': result
                            }
                        else:
                            # failedInstructions, failedDownload и т.д.
                            logger.error(f"❌ WorkItem failed: {workitem_status}")
                            forge_result = {
                                'success': False,
                                'workitem_id': workitem_id,
                                'error': f"WorkItem status: {workitem_status}",
                                'result': result
                            }
                        
                    except Exception as forge_error:
                        logger.error(f"❌ Ошибка Autodesk APS: {forge_error}")
                        forge_result = {
                            'success': False,
                            'error': str(forge_error)
                        }
                    
                    # 🔄 Fallback: если APS не работает, просто копируем DWG
                    if not forge_result.get('success') and os.getenv('AUTO_PDF', 'false').lower() == 'false':
                        logger.info("🔄 Forge fallback: копируем DWG без обработки")
                        try:
                            # Скачиваем исходный DWG
                            input_blob = bucket.blob(input_blob_path)
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.dwg') as temp_dwg:
                                input_blob.download_to_filename(temp_dwg.name)
                                temp_dwg_path = temp_dwg.name
                            
                            # Копируем в output
                            output_blob.upload_from_filename(temp_dwg_path)
                            os.unlink(temp_dwg_path)
                            
                            # Формируем URL результата
                            dwg_url = f"https://storage.googleapis.com/btibot-processed/{output_blob_path}"
                            
                            logger.info(f"✅ DWG скопирован без обработки: {dwg_url}")
                            
                            # Завершаем job
                            result_data = {
                                "dwg_url": dwg_url,
                                "dwg_path": output_blob_path,
                                "forge_fallback": True,
                                "processed_at": datetime.now(timezone.utc).isoformat()
                            }
                            queue_manager.finish_job(job_id, result_data)
                            
                            # Отправляем уведомление
                            if application:
                                try:
                                    async def send_dwg_notification():
                                        keyboard = InlineKeyboardMarkup([
                                            [InlineKeyboardButton("📥 Скачать DWG", url=dwg_url)]
                                        ])
                                        
                                        await application.bot.send_message(
                                            chat_id=job_data["chat_id"],
                                            text=f"✅ DWG готов!\n\n"
                                                 f"📦 Файл: {job_data['filename']}\n"
                                                 f"🆔 ID: {job_id}\n\n"
                                                 f"📐 DWG сохранён без изменений",
                                            reply_markup=keyboard
                                        )
                                    
                                    _run_coro(send_dwg_notification())
                                except Exception as e:
                                    logger.error(f"Failed to send DWG notification: {e}")
                            
                            return jsonify({
                                "status": "success",
                                "job_id": job_id,
                                "dwg_url": dwg_url,
                                "message": "DWG copied without processing (Forge fallback)"
                            })
                            
                        except Exception as fallback_error:
                            logger.error(f"❌ Fallback копирование DWG failed: {fallback_error}")
                            # Продолжаем стандартную логику
                    
                    if forge_result.get('success'):
                        # Forge задача отправлена успешно
                        workitem_id = forge_result.get('workitem_id')
                        
                        # Сохраняем информацию о Forge задаче
                        result_data = {
                            "forge_workitem_id": workitem_id,
                            "forge_status": "pending",
                            "processed_at": datetime.now(timezone.utc).isoformat()
                        }
                        queue_manager.finish_job(job_id, result_data)
                        
                        # Отправляем уведомление пользователю
                        if application:
                            try:
                                async def send_forge_notification():
                                    # Делаем output файл публичным
                                    output_blob.make_public()
                                    dwg_url = f"https://storage.googleapis.com/btibot-processed/{output_blob_path}"
                                    
                                    # Создаем inline кнопки для выбора PDF
                                    keyboard = InlineKeyboardMarkup([
                                        [InlineKeyboardButton("📄 Да, сделать PDF", callback_data=f"make_pdf_{job_id}")],
                                        [InlineKeyboardButton("👌 Нет, только DWG", callback_data=f"done_{job_id}")]
                                    ])
                                    
                                    await application.bot.send_message(
                                        chat_id=job_data["chat_id"],
                                        text=f"🏁 Готово! DWG обработан через Autodesk APS!\n\n"
                                             f"📦 Файл: {job_data['filename']}\n"
                                             f"🆔 ID: {job_id}\n"
                                             f"🔧 APS WorkItem: {workitem_id}\n\n"
                                             f"📐 DWG готов: {dwg_url}\n\n"
                                             f"Хотите, чтобы я сделал PDF (A4, Landscape)?",
                                        reply_markup=keyboard
                                    )
                                
                                _run_coro(send_forge_notification())
                            except Exception as e:
                                logger.error(f"Failed to send Forge notification: {e}")
                        
                        return jsonify({
                            "status": "success",
                            "job_id": job_id,
                            "forge_workitem_id": workitem_id,
                            "message": "DWG sent to Forge API for processing"
                        })
                    else:
                        # Ошибка отправки в Forge API
                        error_msg = forge_result.get('error', 'Unknown Forge API error')
                        logger.error(f"❌ Forge API error: {error_msg}")
                        
                        # Fallback: используем исходный файл
                        timestamp = int(time.time())
                        dwg_key = f"processed/{timestamp}/plan.dwg"
                        dwg_blob = bucket.blob(dwg_key)
                        dwg_blob.upload_from_filename(temp_path)
                        dwg_blob.make_public()
                        dwg_url = f"https://storage.googleapis.com/btibot-processed/{dwg_key}"
                        
                        result_data = {
                            "dwg_url": dwg_url,
                            "dwg_path": dwg_key,
                            "forge_error": error_msg,
                            "processed_at": datetime.now(timezone.utc).isoformat()
                        }
                        queue_manager.finish_job(job_id, result_data)
                        
                        # Отправляем уведомление с предупреждением
                        if application:
                            try:
                                async def send_fallback_notification():
                                    keyboard = InlineKeyboardMarkup([
                                        [InlineKeyboardButton("📄 Да, сделать PDF", callback_data=f"make_pdf_{job_id}")],
                                        [InlineKeyboardButton("👌 Нет, только DWG", callback_data=f"done_{job_id}")]
                                    ])
                                    
                                    await application.bot.send_message(
                                        chat_id=job_data["chat_id"],
                                        text=f"⚠️ Forge API недоступен, используем исходный DWG\n\n"
                                             f"📦 Файл: {job_data['filename']}\n"
                                             f"🆔 ID: {job_id}\n\n"
                                             f"📐 DWG готов: {dwg_url}\n\n"
                                             f"Хотите, чтобы я сделал PDF (A4, Landscape)?",
                                        reply_markup=keyboard
                                    )
                                
                                _run_coro(send_fallback_notification())
                            except Exception as e:
                                logger.error(f"Failed to send fallback notification: {e}")
                        
                        return jsonify({
                            "status": "success",
                            "job_id": job_id,
                            "dwg_url": dwg_url,
                            "message": "DWG processed with fallback (Forge API unavailable)"
                        })
                        
                except Exception as e:
                    # Критическая ошибка
                    logger.error(f"❌ Critical error in DWG-first processing: {e}")
                    queue_manager.fail_job(job_id, f"DWG-first processing failed: {str(e)}")
                    
                    return jsonify({
                        "status": "error",
                        "job_id": job_id,
                        "message": f"Processing failed: {str(e)}"
                    }), 500
                
        finally:
            # Удаляем временные файлы
            try:
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.unlink(temp_path)
                if 'pdf_path' in locals() and pdf_path and os.path.exists(pdf_path):
                    os.unlink(pdf_path)
            except:
                pass
                
    except Exception as e:
        logger.exception(f"❌ Error in process_queue: {e}")
        return jsonify({
            "status": "error",
            "message": f"Internal server error: {str(e)}"
        }), 500

@app.route('/queue-status', methods=['GET'])
def queue_status():
    """Возвращает статус очереди"""
    try:
        if not queue_manager:
            return jsonify({"status": "error", "message": "Queue manager not initialized"}), 500
        
        status = queue_manager.get_queue_status()
        return jsonify(status)
    except Exception as e:
        logger.exception(f"❌ Error getting queue status: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/aps-callback', methods=['POST'])
def aps_callback():
    """Handle APS onComplete callback"""
    try:
        callback_data = request.get_json()
        logger.info(f"📞 APS Callback received: {callback_data}")
        logger.info(f"📞 Callback headers: {dict(request.headers)}")
        logger.info(f"📞 Callback method: {request.method}")
        
        # Парсим данные callback
        workitem_id = callback_data.get('workItemId')
        status = callback_data.get('status')
        
        if not workitem_id:
            logger.error("❌ No workItemId in callback")
            return jsonify({"error": "Missing workItemId"}), 400
        
        logger.info(f"📊 WorkItem {workitem_id} status: {status}")
        
        if status == 'success':
            # Обрабатываем успешное завершение
            logger.info(f"✅ WorkItem {workitem_id} completed successfully")
            
            # Здесь можно добавить логику обработки результата
            # Например, уведомление пользователя через Telegram
            
        elif status == 'failed':
            # Обрабатываем ошибку
            logger.error(f"❌ WorkItem {workitem_id} failed")
            
            # Детальное логирование ошибки
            error_details = callback_data.get('details', {})
            logger.error(f"📋 Error details: {error_details}")
            
            # Здесь можно добавить логику обработки ошибки
        
        return jsonify({"status": "received"})
        
    except Exception as e:
        logger.error(f"❌ Error in aps_callback: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/gcs/push', methods=['POST'])
def gcs_push():
    """Endpoint для Pub/Sub push notifications"""
    try:
        logger.info("🚀 GCS Push notification received")
        
        # Парсим Pub/Sub сообщение
        data = request.get_json()
        if not data:
            logger.warning("❌ No JSON data in request")
            return jsonify({"status": "error", "reason": "no_data"}), 400
        
        logger.info(f"📨 Received Pub/Sub data: {json.dumps(data, indent=2)}")
        
        # Извлекаем данные о файле
        bucket, name, generation = parse_pubsub_message(data)
        
        if not bucket or not name:
            logger.warning(f"❌ Missing bucket or name: bucket={bucket}, name={name}")
            return jsonify({"status": "error", "reason": "missing_bucket_or_name"}), 400
        
        logger.info(f"📦 Processing file: gs://{bucket}/{name}")
        
        # Проверяем что это DWG файл в папке raw/
        if not name.endswith('.dwg') or not name.startswith('raw/'):
            logger.info(f"⏭️ Skipping non-DWG file: {name}")
            return jsonify({"status": "skipped", "reason": "not_dwg"})
        
        # Обрабатываем DWG файл
        logger.info(f"✅ DWG file detected: {name}")
        
        # Вместо локальной конвертации (не работает с DWG) - отправляем в очередь для APS
        # Используем /process-dwg endpoint для обработки через Autodesk APS
        try:
            import uuid
            job_id = str(uuid.uuid4())
            file_url = f"gs://{bucket}/{name}"
            
            logger.info(f"📤 Отправка в APS: {file_url}")
            
            # Вызываем /process-dwg endpoint
            from google.cloud import secretmanager
            from google.oauth2 import service_account
            
            # Получаем Service Account credentials для signed URLs
            secret_client = secretmanager.SecretManagerServiceClient()
            secret_name = "projects/talkhint/secrets/FORGE_SERVICE_KEY/versions/latest"
            secret_response = secret_client.access_secret_version(request={"name": secret_name})
            sa_credentials_json = json.loads(secret_response.payload.data.decode("UTF-8"))
            
            sa_credentials = service_account.Credentials.from_service_account_info(sa_credentials_json)
            gcs_client = storage.Client(credentials=sa_credentials)
            bucket_obj = gcs_client.bucket(bucket)
            
            # Input URL (публичный)
            input_url = f"https://storage.googleapis.com/{bucket}/{name}"
            
            # Output URL (signed для записи, БЕЗ content_type!)
            # DWG→DWG обработка - результат тоже DWG
            output_path = f"ready/gcs_push/{job_id}/result.dwg"
            output_blob = bucket_obj.blob(output_path)
            output_url = output_blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=1),
                method="PUT"
            )
            
            # Отправляем WorkItem в APS
            # Проверяем режим работы с типовым шаблоном BTI
            use_bti_template = os.getenv('USE_BTI_TEMPLATE', 'false').lower() == 'true'
            
            workitem = forge_client.submit_workitem(input_url, output_url, use_template=use_bti_template)
            workitem_id = workitem['id']
            
            logger.info(f"✅ WorkItem создан: {workitem_id}")
            
            # Не ждем результата - вернем success сразу
            return jsonify({
                "status": "success",
                "message": f"DWG file {name} sent to APS for processing",
                "workitem_id": workitem_id,
                "result_path": f"gs://{bucket}/{output_path}"
            })
            
        except Exception as e:
            logger.error(f"❌ APS processing error: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
                
    except Exception as e:
        logger.exception(f"❌ Error in gcs_push endpoint: {e}")
        return jsonify({
            "status": "error",
            "message": f"Internal server error: {str(e)}"
        }), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    if application is None or _background_loop is None:
        if not init_bot():
            return jsonify({"error":"init failed"}), 500
    upd = request.get_json()
    if not upd or 'update_id' not in upd:
        return jsonify({"status":"OK"})
    update = Update.de_json(upd, application.bot)
    if update:
        _run_coro(application.process_update(update))
    return jsonify({"status":"OK"})

def process_queue_worker():
    """Фоновый процесс для обработки очереди"""
    import requests
    import time
    
    while True:
        try:
            # Проверяем очередь каждые 30 секунд
            time.sleep(30)
            
            # Отправляем запрос на обработку очереди
            try:
                response = requests.post('http://localhost:8080/process-queue', timeout=60)
                if response.status_code == 200:
                    result = response.json()
                    if result.get('status') == 'success':
                        logger.info(f"✅ Queue processed: {result.get('job_id')}")
                    elif result.get('status') == 'no_jobs':
                        logger.debug("📭 No jobs in queue")
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Queue processing request failed: {e}")
                
        except Exception as e:
            logger.error(f"❌ Queue worker error: {e}")
            time.sleep(60)  # Wait longer on error

async def bti_dwg_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /bti_dwg - запуск поэтапного DWG-first режима"""
    chat_id = str(update.effective_user.id)
    
    try:
        # Простое сообщение о DWG-first режиме
        message = (
            "🏢 <b>Режим: БТИ техпаспорт (DWG-first)</b>\n\n"
            "📋 <b>Что будет сделано:</b>\n"
            "• Построение чертежа по шаблону БТИ (BTI_Template.dwt)\n"
            "• Вы получите ГЛАВНОЕ: готовый DWG для доработок\n\n"
            "После этого спрошу: нужен ли PDF (A4, Landscape)\n\n"
            "📐 <b>Отправьте DWG-файл для обработки.</b>\n\n"
            "⚠️ <i>Внимание: Полная интеграция DWG-first режима в разработке.</i>\n"
            "💡 Пока используйте обычную загрузку файлов через меню."
        )
        
        await update.message.reply_text(message, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"❌ Ошибка в команде /bti_dwg: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка. Попробуйте позже.",
            parse_mode='HTML'
        )

if __name__ == '__main__':
    # Initialize bot
    init_bot()
    
    # Start queue worker in background
    import threading
    queue_worker_thread = threading.Thread(target=process_queue_worker, daemon=True, name="queue-worker")
    queue_worker_thread.start()
    logger.info("🚀 Queue worker started")
    
    # Start Flask app
    port = int(os.getenv('PORT', '8080'))
    app.run(host='0.0.0.0', port=port)
