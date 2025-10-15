"""
Telegram Bot Integration for Forge Notifications
Обработка уведомлений от AutoDesk Design Automation в Telegram Bot
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any
from google.cloud import storage, pubsub_v1
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import asyncio

logger = logging.getLogger(__name__)

class TelegramForgeIntegration:
    """Интеграция Telegram Bot с Forge уведомлениями"""
    
    def __init__(self, project_id: str = "talkhint"):
        self.project_id = project_id
        self.storage_client = storage.Client()
        self.subscriber = pubsub_v1.SubscriberClient()
        
        # Настройки Pub/Sub
        self.subscription_path = self.subscriber.subscription_path(
            project_id, "bti-jobs-done-subscription"
        )
    
    async def handle_forge_notification(self, notification_data: Dict[str, Any], 
                                      context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает уведомление о завершении Forge задачи"""
        try:
            chat_id = notification_data.get('chat_id')
            job_id = notification_data.get('job_id')
            status = notification_data.get('status')
            template = notification_data.get('template', 'unknown')
            
            if not chat_id:
                logger.error("❌ Missing chat_id in notification")
                return
            
            logger.info(f"📨 Processing Forge notification for chat {chat_id}, job {job_id}, status: {status}")
            
            if status == 'success':
                await self._handle_success_notification(notification_data, context)
            elif status == 'failed':
                await self._handle_failure_notification(notification_data, context)
            elif status == 'timeout':
                await self._handle_timeout_notification(notification_data, context)
            else:
                logger.warning(f"⚠️ Unknown notification status: {status}")
                
        except Exception as e:
            logger.error(f"❌ Error handling Forge notification: {e}")
    
    async def _handle_success_notification(self, notification_data: Dict[str, Any], 
                                         context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает уведомление об успешном завершении"""
        try:
            chat_id = notification_data.get('chat_id')
            job_id = notification_data.get('job_id')
            file_url = notification_data.get('file')
            report_url = notification_data.get('report')
            processing_time = notification_data.get('processing_time_ms', 0)
            template = notification_data.get('template', 'unknown')
            
            # Форматируем время обработки
            if processing_time > 0:
                if processing_time < 1000:
                    time_str = f"{processing_time:.0f} мс"
                elif processing_time < 60000:
                    time_str = f"{processing_time/1000:.1f} сек"
                else:
                    time_str = f"{processing_time/60000:.1f} мин"
            else:
                time_str = "неизвестно"
            
            # Создаем сообщение
            message = (
                f"✅ <b>БТИ-чертёж готов!</b>\n\n"
                f"🆔 ID задачи: <code>{job_id}</code>\n"
                f"🏢 Шаблон: <b>{self._format_template_name(template)}</b>\n"
                f"⏱️ Время обработки: {time_str}\n"
                f"📅 Завершено: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                f"📐 <b>Ваш готовый БТИ-чертёж:</b>\n"
                f"• Оформлен по стандартам БТИ\n"
                f"• Добавлена рамка и штамп\n"
                f"• Нормализованы слои и стили\n"
                f"• Расставлены размеры\n\n"
                f"💾 <b>Скачать файл:</b>"
            )
            
            # Создаем кнопки
            keyboard = []
            
            if file_url:
                # Создаем signed URL для скачивания
                download_url = self._create_download_url(file_url)
                keyboard.append([InlineKeyboardButton("📥 Скачать DWG", url=download_url)])
            
            if report_url:
                report_download_url = self._create_download_url(report_url)
                keyboard.append([InlineKeyboardButton("📊 Отчёт обработки", url=report_download_url)])
            
            keyboard.append([InlineKeyboardButton("🔄 Обработать ещё файл", callback_data="bti_start")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Отправляем сообщение
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            
            logger.info(f"✅ Success notification sent to chat {chat_id} for job {job_id}")
            
        except Exception as e:
            logger.error(f"❌ Error sending success notification: {e}")
    
    async def _handle_failure_notification(self, notification_data: Dict[str, Any], 
                                         context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает уведомление об ошибке"""
        try:
            chat_id = notification_data.get('chat_id')
            job_id = notification_data.get('job_id')
            error = notification_data.get('error', 'Неизвестная ошибка')
            template = notification_data.get('template', 'unknown')
            
            # Форматируем ошибку для пользователя
            user_friendly_error = self._format_error_for_user(error)
            
            message = (
                f"❌ <b>Ошибка обработки БТИ-чертежа</b>\n\n"
                f"🆔 ID задачи: <code>{job_id}</code>\n"
                f"🏢 Шаблон: <b>{self._format_template_name(template)}</b>\n"
                f"📅 Время ошибки: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                f"🚨 <b>Описание ошибки:</b>\n"
                f"{user_friendly_error}\n\n"
                f"💡 <b>Что можно сделать:</b>\n"
                f"• Проверьте формат DWG файла\n"
                f"• Убедитесь, что файл не повреждён\n"
                f"• Попробуйте другой шаблон\n"
                f"• Обратитесь к администратору"
            )
            
            # Создаем кнопки
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data="bti_start")],
                [InlineKeyboardButton("📋 Список шаблонов", callback_data="template_list")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Отправляем сообщение
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            
            logger.error(f"❌ Failure notification sent to chat {chat_id} for job {job_id}: {error}")
            
        except Exception as e:
            logger.error(f"❌ Error sending failure notification: {e}")
    
    async def _handle_timeout_notification(self, notification_data: Dict[str, Any], 
                                         context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает уведомление о таймауте"""
        try:
            chat_id = notification_data.get('chat_id')
            job_id = notification_data.get('job_id')
            template = notification_data.get('template', 'unknown')
            
            message = (
                f"⏰ <b>Превышено время обработки</b>\n\n"
                f"🆔 ID задачи: <code>{job_id}</code>\n"
                f"🏢 Шаблон: <b>{self._format_template_name(template)}</b>\n"
                f"📅 Время таймаута: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                f"🚨 <b>Причина:</b>\n"
                f"Обработка заняла больше 30 минут.\n"
                f"Возможно, файл слишком сложный или большой.\n\n"
                f"💡 <b>Рекомендации:</b>\n"
                f"• Упростите чертёж\n"
                f"• Удалите лишние элементы\n"
                f"• Попробуйте другой шаблон\n"
                f"• Разделите на несколько файлов"
            )
            
            # Создаем кнопки
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data="bti_start")],
                [InlineKeyboardButton("📋 Список шаблонов", callback_data="template_list")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Отправляем сообщение
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            
            logger.warning(f"⏰ Timeout notification sent to chat {chat_id} for job {job_id}")
            
        except Exception as e:
            logger.error(f"❌ Error sending timeout notification: {e}")
    
    def _format_template_name(self, template: str) -> str:
        """Форматирует название шаблона для пользователя"""
        template_names = {
            'moscow': 'Москва',
            'mo': 'Московская область',
            'region': 'Регион',
            'default': 'По умолчанию'
        }
        return template_names.get(template, template.capitalize())
    
    def _format_error_for_user(self, error: str) -> str:
        """Форматирует ошибку для пользователя"""
        # Маппинг технических ошибок на понятные пользователю
        error_mappings = {
            'invalid dwg format': 'Неправильный формат DWG файла',
            'corrupted file': 'Файл повреждён или не читается',
            'unsupported version': 'Неподдерживаемая версия DWG',
            'authentication failed': 'Ошибка авторизации в системе',
            'template not found': 'Шаблон не найден',
            'processing timeout': 'Превышено время обработки',
            'insufficient permissions': 'Недостаточно прав для обработки',
            'storage error': 'Ошибка сохранения файла',
            'forge api error': 'Ошибка облачной обработки'
        }
        
        error_lower = error.lower()
        for key, value in error_mappings.items():
            if key in error_lower:
                return value
        
        # Если не найдено точное соответствие, возвращаем общее сообщение
        return "Произошла ошибка при обработке файла. Попробуйте ещё раз или обратитесь к администратору."
    
    def _create_download_url(self, gcs_url: str) -> str:
        """Создает signed URL для скачивания файла"""
        try:
            # Извлекаем путь к blob из GCS URL
            if gcs_url.startswith('gs://'):
                path_parts = gcs_url[5:].split('/', 1)
                bucket_name = path_parts[0]
                blob_name = path_parts[1]
                
                bucket = self.storage_client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                
                if blob.exists():
                    # Создаем signed URL на 1 час
                    signed_url = blob.generate_signed_url(
                        version="v4",
                        expiration=datetime.now() + timedelta(hours=1),
                        method="GET"
                    )
                    return signed_url
                else:
                    logger.error(f"❌ Blob does not exist: {gcs_url}")
                    return None
            else:
                logger.error(f"❌ Invalid GCS URL: {gcs_url}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating download URL for {gcs_url}: {e}")
            return None
    
    async def start_pubsub_listener(self, context: ContextTypes.DEFAULT_TYPE):
        """Запускает слушатель Pub/Sub уведомлений"""
        try:
            logger.info("🎧 Starting Pub/Sub listener for Forge notifications...")
            
            def callback(message):
                try:
                    # Декодируем сообщение
                    data = json.loads(message.data.decode('utf-8'))
                    
                    # Обрабатываем уведомление асинхронно
                    asyncio.create_task(
                        self.handle_forge_notification(data, context)
                    )
                    
                    # Подтверждаем получение сообщения
                    message.ack()
                    
                except Exception as e:
                    logger.error(f"❌ Error processing Pub/Sub message: {e}")
                    message.nack()
            
            # Запускаем слушатель
            streaming_pull_future = self.subscriber.pull(
                request={"subscription": self.subscription_path, "max_messages": 10},
                callback=callback
            )
            
            logger.info("✅ Pub/Sub listener started successfully")
            
            # Блокируем выполнение для прослушивания
            with self.subscriber:
                try:
                    streaming_pull_future.result()
                except KeyboardInterrupt:
                    streaming_pull_future.cancel()
                    logger.info("🛑 Pub/Sub listener stopped")
                    
        except Exception as e:
            logger.error(f"❌ Error starting Pub/Sub listener: {e}")


# Интеграция в основной app.py
def add_forge_integration_to_bot(app_instance):
    """Добавляет интеграцию с Forge в существующий Telegram Bot"""
    
    # Создаем экземпляр интеграции
    forge_integration = TelegramForgeIntegration()
    
    # Добавляем обработчик уведомлений от Forge
    async def handle_forge_notification_webhook(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Webhook для получения уведомлений от Forge"""
        try:
            # Получаем данные из webhook
            notification_data = update.message.text if update.message else None
            if notification_data:
                data = json.loads(notification_data)
                await forge_integration.handle_forge_notification(data, context)
        except Exception as e:
            logger.error(f"❌ Error in Forge notification webhook: {e}")
    
    # Добавляем команду для проверки статуса задач
    async def check_forge_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /forge_status - проверка статуса Forge задач"""
        try:
            user_id = update.effective_user.id
            chat_id = str(user_id)
            
            # Получаем список активных задач пользователя
            active_jobs = await get_user_active_jobs(chat_id)
            
            if not active_jobs:
                message = (
                    "📋 <b>Статус задач Forge</b>\n\n"
                    "✅ Нет активных задач обработки\n\n"
                    "💡 Для начала обработки используйте:\n"
                    "🏢 <code>/bti_moscow</code>\n"
                    "🏘️ <code>/bti_mo</code>\n"
                    "🌍 <code>/bti_region</code>"
                )
            else:
                message = "📋 <b>Активные задачи Forge</b>\n\n"
                
                for job in active_jobs:
                    status_emoji = {
                        'submitted': '⏳',
                        'inprogress': '🔄',
                        'pending': '⏳'
                    }.get(job.get('status', 'unknown'), '❓')
                    
                    message += (
                        f"{status_emoji} <b>Задача {job['job_id'][:8]}...</b>\n"
                        f"🏢 Шаблон: {job.get('template', 'unknown')}\n"
                        f"📅 Создана: {job.get('submitted_at', 'unknown')[:16]}\n"
                        f"⏱️ Статус: {job.get('status', 'unknown')}\n\n"
                    )
                
                message += "💡 Статус обновляется автоматически"
            
            await update.message.reply_text(message, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"❌ Error in forge status command: {e}")
            await update.message.reply_text(
                "❌ Ошибка получения статуса задач. Попробуйте позже.",
                parse_mode='HTML'
            )
    
    async def get_user_active_jobs(chat_id: str) -> list:
        """Получает список активных задач пользователя"""
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket("btibot-processed")
            job_blobs = list(bucket.list_blobs(prefix=f"jobs/"))
            
            active_jobs = []
            for blob in job_blobs:
                if not blob.name.endswith('.json'):
                    continue
                
                try:
                    job_info = json.loads(blob.download_as_text())
                    
                    # Проверяем, что задача принадлежит пользователю и не завершена
                    if (job_info.get('chat_id') == chat_id and 
                        job_info.get('status') not in ['success', 'failed', 'timeout']):
                        active_jobs.append(job_info)
                        
                except Exception as e:
                    logger.error(f"❌ Error reading job {blob.name}: {e}")
            
            return active_jobs
            
        except Exception as e:
            logger.error(f"❌ Error getting user active jobs: {e}")
            return []
    
    # Возвращаем функции для добавления в основное приложение
    return {
        'forge_notification_handler': handle_forge_notification_webhook,
        'forge_status_command': check_forge_status_command,
        'forge_integration': forge_integration
    }
