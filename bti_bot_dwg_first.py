"""
BTI Bot - DWG-first поэтапный режим
Обработка DWG файлов через AutoDesk Forge API с поэтапным workflow
"""

import os
import sys
import json
import logging
import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from enum import Enum

# Third-party imports
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from google.cloud import storage, secretmanager, firestore
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class BotState(Enum):
    """Состояния бота"""
    IDLE = "idle"
    WAIT_DWG = "wait_dwg"
    PROCESSING_DWG = "processing_dwg"
    DWG_READY = "dwg_ready"
    ASK_PDF = "ask_pdf"
    PDF_CONVERT = "pdf_convert"
    DONE_NO_PDF = "done_no_pdf"
    DONE = "done"

class BTIBotDWGFirst:
    """BTI Bot с поэтапным DWG-first режимом"""
    
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'talkhint')
        self.gcs_bucket = os.getenv('GCS_BUCKET', 'btibot-processed')
        self.job_timeout = int(os.getenv('JOB_TIMEOUT_SEC', '900'))  # 15 минут
        
        # Инициализация клиентов
        self.storage_client = storage.Client()
        self.secret_client = secretmanager.SecretManagerServiceClient()
        self.db = firestore.Client(project=self.project_id)
        
        # Кэш токена Forge
        self._forge_token = None
        self._token_expires = None
        
        # Состояния пользователей
        self.user_states = {}
        
        # Forge API URLs
        self.forge_auth_url = "https://developer.api.autodesk.com/authentication/v1/authenticate"
        self.forge_workitems_url = "https://developer.api.autodesk.com/da/us-east/v3/workitems"
    
    def get_forge_token(self) -> str:
        """Получает токен для Forge API"""
        if self._forge_token and self._token_expires and datetime.now() < self._token_expires:
            return self._forge_token
        
        try:
            # Получаем credentials из Secret Manager
            client_id = self._get_secret("FORGE_CLIENT_ID")
            client_secret = self._get_secret("FORGE_CLIENT_SECRET")
            
            response = requests.post(
                self.forge_auth_url,
                data={
                    'grant_type': 'client_credentials',
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'scope': 'data:read data:write data:create bucket:read bucket:create'
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Forge auth failed: {response.status_code} - {response.text}")
                raise Exception(f"Forge authentication failed: {response.status_code}")
            
            token_data = response.json()
            self._forge_token = token_data['access_token']
            expires_in = token_data.get('expires_in', 3600)
            self._token_expires = datetime.now() + timedelta(seconds=expires_in - 60)
            
            logger.info("✅ Forge access token получен")
            return self._forge_token
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения Forge token: {e}")
            raise
    
    def _get_secret(self, secret_name: str) -> str:
        """Получает секрет из Secret Manager"""
        try:
            name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
            response = self.secret_client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"❌ Ошибка получения секрета {secret_name}: {e}")
            raise
    
    async def check_user_lock(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Проверяет есть ли активная задача у пользователя"""
        try:
            lock_ref = self.db.collection('bti_locks').document(str(chat_id))
            lock_doc = lock_ref.get()
            
            if lock_doc.exists:
                lock_data = lock_doc.to_dict()
                # Проверяем не истек ли TTL
                if lock_data.get('expires_at', 0) > time.time():
                    return lock_data
                else:
                    # Удаляем истекший lock
                    lock_ref.delete()
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки lock для {chat_id}: {e}")
            return None
    
    async def set_user_lock(self, chat_id: str, job_id: str, state: BotState) -> bool:
        """Устанавливает lock для пользователя"""
        try:
            lock_ref = self.db.collection('bti_locks').document(str(chat_id))
            lock_data = {
                'job_id': job_id,
                'state': state.value,
                'created_at': time.time(),
                'expires_at': time.time() + 1800,  # 30 минут TTL
                'chat_id': str(chat_id)
            }
            
            lock_ref.set(lock_data)
            logger.info(f"🔒 Lock установлен для {chat_id}, job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка установки lock для {chat_id}: {e}")
            return False
    
    async def update_user_lock(self, chat_id: str, state: BotState, **kwargs) -> bool:
        """Обновляет состояние lock"""
        try:
            lock_ref = self.db.collection('bti_locks').document(str(chat_id))
            update_data = {'state': state.value}
            update_data.update(kwargs)
            
            lock_ref.update(update_data)
            logger.info(f"🔄 Lock обновлен для {chat_id}: {state.value}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления lock для {chat_id}: {e}")
            return False
    
    async def clear_user_lock(self, chat_id: str) -> bool:
        """Снимает lock с пользователя"""
        try:
            lock_ref = self.db.collection('bti_locks').document(str(chat_id))
            lock_ref.delete()
            logger.info(f"🔓 Lock снят для {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка снятия lock для {chat_id}: {e}")
            return False
    
    async def bti_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /bti - запуск поэтапного режима БТИ"""
        chat_id = str(update.effective_user.id)
        
        try:
            # Проверяем есть ли активная задача
            active_lock = await self.check_user_lock(chat_id)
            if active_lock:
                job_id = active_lock.get('job_id', 'unknown')
                await update.message.reply_text(
                    f"⚠️ Сейчас в работе проект <code>{job_id}</code>. Новый файл приму, когда закончу.",
                    parse_mode='HTML'
                )
                return
            
            # Создаем новую задачу
            job_id = str(uuid.uuid4())
            
            # Устанавливаем lock
            await self.set_user_lock(chat_id, job_id, BotState.WAIT_DWG)
            
            # Отправляем описание этапов
            message = (
                "🏢 <b>Режим: БТИ техпаспорт</b>\n\n"
                "📋 <b>Что будет сделано:</b>\n"
                "• Построение чертежа по шаблону БТИ (BTI_Template.dwt)\n"
                "• Вы получите ГЛАВНОЕ: готовый DWG для доработок\n\n"
                "После этого спрошу: нужен ли PDF (A4, Landscape)\n\n"
                "📐 <b>Отправьте DWG-файл для обработки.</b>"
            )
            
            await update.message.reply_text(message, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"❌ Ошибка в команде /bti: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка. Попробуйте позже.",
                parse_mode='HTML'
            )
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка загруженного документа"""
        chat_id = str(update.effective_user.id)
        document = update.message.document
        
        try:
            # Проверяем активную задачу
            active_lock = await self.check_user_lock(chat_id)
            if not active_lock:
                await update.message.reply_text(
                    "❌ Сначала используйте команду /bti для начала обработки.",
                    parse_mode='HTML'
                )
                return
            
            job_id = active_lock['job_id']
            
            # Валидация файла
            if not self._validate_dwg_file(document):
                await update.message.reply_text(
                    "❌ <b>Поддерживается только DWG</b>\n\n"
                    f"Ваш файл: <code>{document.file_name}</code>\n"
                    f"Формат: <code>{os.path.splitext(document.file_name)[1]}</code>\n\n"
                    "💡 Экспортируйте чертёж как DWG и попробуйте снова",
                    parse_mode='HTML'
                )
                return
            
            # Обновляем состояние
            await self.update_user_lock(chat_id, BotState.PROCESSING_DWG, 
                                      file_name=document.file_name,
                                      file_size=document.file_size)
            
            # Отправляем подтверждение
            await update.message.reply_text(
                "✅ Файл принят. Запускаю обработку в режиме БТИ (Autodesk API)…",
                parse_mode='HTML'
            )
            
            # Загружаем файл из Telegram
            file_obj = await context.bot.get_file(document.file_id)
            file_content = await file_obj.download_as_bytearray()
            
            # Сохраняем в GCS
            input_path = f"raw/{chat_id}/{job_id}/input.dwg"
            success = await self._save_to_gcs(file_content, input_path)
            
            if not success:
                await self._handle_processing_error(chat_id, job_id, "Ошибка сохранения файла")
                return
            
            # Запускаем обработку через Forge API
            await self._process_dwg_with_forge(chat_id, job_id, input_path)
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки документа: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при обработке файла.",
                parse_mode='HTML'
            )
    
    def _validate_dwg_file(self, document) -> bool:
        """Валидация DWG файла"""
        if not document.file_name:
            return False
        
        # Проверяем расширение
        if not document.file_name.lower().endswith('.dwg'):
            return False
        
        # Проверяем размер
        if document.file_size <= 0:
            return False
        
        # Проверяем MIME type (если доступен)
        if hasattr(document, 'mime_type') and document.mime_type:
            if 'acad' not in document.mime_type.lower() and 'dwg' not in document.mime_type.lower():
                return False
        
        return True
    
    async def _save_to_gcs(self, file_content: bytes, path: str) -> bool:
        """Сохраняет файл в GCS"""
        try:
            bucket = self.storage_client.bucket(self.gcs_bucket)
            blob = bucket.blob(path)
            blob.upload_from_string(file_content, content_type='application/octet-stream')
            
            logger.info(f"✅ Файл сохранен в GCS: gs://{self.gcs_bucket}/{path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения в GCS: {e}")
            return False
    
    async def _process_dwg_with_forge(self, chat_id: str, job_id: str, input_path: str):
        """Обрабатывает DWG через Forge API"""
        try:
            # Создаем WorkItem для обработки DWG
            workitem_result = await self._create_forge_workitem(chat_id, job_id, input_path)
            
            if not workitem_result['success']:
                await self._handle_processing_error(chat_id, job_id, workitem_result['error'])
                return
            
            # Запускаем мониторинг в фоне
            asyncio.create_task(self._monitor_forge_workitem(chat_id, job_id, workitem_result['workitem_id']))
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки через Forge: {e}")
            await self._handle_processing_error(chat_id, job_id, str(e))
    
    async def _create_forge_workitem(self, chat_id: str, job_id: str, input_path: str) -> Dict[str, Any]:
        """Создает WorkItem в Forge API"""
        try:
            access_token = self.get_forge_token()
            
            # Создаем signed URLs
            input_url = self._create_signed_url(f"{input_path}", "GET")
            template_url = self._create_signed_url("templates/BTI_Template.dwt", "GET")
            output_url = self._create_signed_url(f"ready/{chat_id}/{job_id}/out.dwg", "PUT")
            
            # Формируем payload для Forge API
            payload = {
                "activityId": "btiProcessor.AutoCAD+prod",
                "arguments": {
                    "inputFile": {
                        "verb": "get",
                        "url": input_url,
                        "localName": "input.dwg"
                    },
                    "templateFile": {
                        "verb": "get",
                        "url": template_url,
                        "localName": "template.dwt"
                    },
                    "result": {
                        "verb": "put",
                        "url": output_url,
                        "localName": "out.dwg"
                    }
                }
            }
            
            # Отправляем запрос в Forge API
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                self.forge_workitems_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code not in [200, 201, 202]:
                logger.error(f"❌ Forge API error: {response.status_code} - {response.text}")
                return {'success': False, 'error': f'Forge API error: {response.status_code}'}
            
            workitem_data = response.json()
            workitem_id = workitem_data['id']
            
            logger.info(f"✅ Forge WorkItem создан: {workitem_id}")
            return {'success': True, 'workitem_id': workitem_id}
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания Forge WorkItem: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_signed_url(self, path: str, method: str) -> str:
        """Создает signed URL для GCS объекта"""
        try:
            bucket = self.storage_client.bucket(self.gcs_bucket)
            blob = bucket.blob(path)
            
            return blob.generate_signed_url(
                version="v4",
                expiration=datetime.now() + timedelta(hours=2),
                method=method
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания signed URL: {e}")
            raise
    
    async def _monitor_forge_workitem(self, chat_id: str, job_id: str, workitem_id: str):
        """Мониторит выполнение WorkItem в Forge API"""
        try:
            start_time = time.time()
            
            while time.time() - start_time < self.job_timeout:
                # Проверяем статус WorkItem
                status = await self._check_forge_workitem_status(workitem_id)
                
                if status['status'] == 'success':
                    await self._handle_dwg_ready(chat_id, job_id)
                    return
                elif status['status'] == 'failed':
                    await self._handle_processing_error(chat_id, job_id, status.get('error', 'Unknown error'))
                    return
                elif status['status'] in ['pending', 'inprogress']:
                    # Продолжаем ждать
                    await asyncio.sleep(30)  # Проверяем каждые 30 секунд
                else:
                    logger.warning(f"⚠️ Неизвестный статус WorkItem: {status}")
                    await asyncio.sleep(30)
            
            # Таймаут
            await self._handle_processing_timeout(chat_id, job_id, workitem_id)
            
        except Exception as e:
            logger.error(f"❌ Ошибка мониторинга WorkItem: {e}")
            await self._handle_processing_error(chat_id, job_id, str(e))
    
    async def _check_forge_workitem_status(self, workitem_id: str) -> Dict[str, Any]:
        """Проверяет статус WorkItem в Forge API"""
        try:
            access_token = self.get_forge_token()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.forge_workitems_url}/{workitem_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 401:
                # Токен просрочен, обновляем
                self._forge_token = None
                access_token = self.get_forge_token()
                headers['Authorization'] = f'Bearer {access_token}'
                
                response = requests.get(
                    f"{self.forge_workitems_url}/{workitem_id}",
                    headers=headers,
                    timeout=30
                )
            
            if response.status_code != 200:
                logger.error(f"❌ Forge status API error: {response.status_code}")
                return {'status': 'error', 'error': f'API error: {response.status_code}'}
            
            return response.json()
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки статуса WorkItem: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def _handle_dwg_ready(self, chat_id: str, job_id: str):
        """Обрабатывает готовый DWG файл"""
        try:
            # Обновляем состояние
            await self.update_user_lock(chat_id, BotState.DWG_READY)
            
            # Получаем готовый файл из GCS
            output_path = f"ready/{chat_id}/{job_id}/out.dwg"
            dwg_url = self._create_signed_url(output_path, "GET")
            
            # Отправляем файл пользователю
            await self._send_dwg_to_user(chat_id, output_path, dwg_url)
            
            # Переходим к вопросу о PDF
            await self._ask_for_pdf(chat_id, job_id)
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки готового DWG: {e}")
            await self._handle_processing_error(chat_id, job_id, str(e))
    
    async def _send_dwg_to_user(self, chat_id: str, output_path: str, dwg_url: str):
        """Отправляет готовый DWG файл пользователю"""
        try:
            # Здесь должна быть логика отправки файла через Telegram Bot API
            # Для демонстрации отправляем сообщение с ссылкой
            
            message = f"🏁 Готово. Ваш DWG: {dwg_url}"
            
            # В реальной реализации здесь был бы вызов Telegram Bot API
            logger.info(f"📤 Отправляем DWG пользователю {chat_id}: {message}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки DWG пользователю: {e}")
    
    async def _ask_for_pdf(self, chat_id: str, job_id: str):
        """Спрашивает пользователя нужен ли PDF"""
        try:
            # Обновляем состояние
            await self.update_user_lock(chat_id, BotState.ASK_PDF)
            
            # Создаем inline кнопки
            keyboard = [
                [
                    InlineKeyboardButton("Сделать PDF", callback_data=f"pdf_yes:{job_id}"),
                    InlineKeyboardButton("Не нужно", callback_data=f"pdf_no:{job_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = "Нужен ли PDF (A4, Landscape)?"
            
            # В реальной реализации здесь был бы вызов Telegram Bot API
            logger.info(f"❓ Спрашиваем пользователя {chat_id} о PDF: {message}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка запроса PDF: {e}")
            await self._handle_processing_error(chat_id, job_id, str(e))
    
    async def handle_pdf_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает выбор пользователя по PDF"""
        query = update.callback_query
        await query.answer()
        
        chat_id = str(query.from_user.id)
        data = query.data
        
        try:
            if data.startswith("pdf_yes:"):
                job_id = data.split(":", 1)[1]
                await self._handle_pdf_yes(chat_id, job_id)
            elif data.startswith("pdf_no:"):
                job_id = data.split(":", 1)[1]
                await self._handle_pdf_no(chat_id, job_id)
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки callback PDF: {e}")
            await query.edit_message_text("❌ Произошла ошибка.")
    
    async def _handle_pdf_yes(self, chat_id: str, job_id: str):
        """Обрабатывает выбор 'Сделать PDF'"""
        try:
            # Обновляем состояние
            await self.update_user_lock(chat_id, BotState.PDF_CONVERT)
            
            # Создаем WorkItem для конвертации в PDF
            pdf_result = await self._create_pdf_workitem(chat_id, job_id)
            
            if not pdf_result['success']:
                await self._handle_processing_error(chat_id, job_id, pdf_result['error'])
                return
            
            # Запускаем мониторинг PDF конвертации
            asyncio.create_task(self._monitor_pdf_workitem(chat_id, job_id, pdf_result['workitem_id']))
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки PDF: {e}")
            await self._handle_processing_error(chat_id, job_id, str(e))
    
    async def _handle_pdf_no(self, chat_id: str, job_id: str):
        """Обрабатывает выбор 'Не нужно' PDF"""
        try:
            # Обновляем состояние
            await self.update_user_lock(chat_id, BotState.DONE_NO_PDF)
            
            # Отправляем сообщение
            message = "👌 Ок, оставляем только DWG. Задача завершена."
            
            # В реальной реализации здесь был бы вызов Telegram Bot API
            logger.info(f"✅ Задача завершена без PDF для {chat_id}: {message}")
            
            # Снимаем lock
            await self.clear_user_lock(chat_id)
            
        except Exception as e:
            logger.error(f"❌ Ошибка завершения без PDF: {e}")
    
    async def _create_pdf_workitem(self, chat_id: str, job_id: str) -> Dict[str, Any]:
        """Создает WorkItem для конвертации в PDF"""
        try:
            access_token = self.get_forge_token()
            
            # Создаем signed URLs
            dwg_url = self._create_signed_url(f"ready/{chat_id}/{job_id}/out.dwg", "GET")
            pdf_url = self._create_signed_url(f"ready/{chat_id}/{job_id}/out.pdf", "PUT")
            
            # Формируем payload для PDF конвертации
            payload = {
                "activityId": "dwg2pdf.AutoCAD+prod",  # Другая активность для PDF
                "arguments": {
                    "inputFile": {
                        "verb": "get",
                        "url": dwg_url,
                        "localName": "input.dwg"
                    },
                    "result": {
                        "verb": "put",
                        "url": pdf_url,
                        "localName": "output.pdf"
                    }
                }
            }
            
            # Отправляем запрос в Forge API
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                self.forge_workitems_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code not in [200, 201, 202]:
                logger.error(f"❌ PDF Forge API error: {response.status_code} - {response.text}")
                return {'success': False, 'error': f'PDF Forge API error: {response.status_code}'}
            
            workitem_data = response.json()
            workitem_id = workitem_data['id']
            
            logger.info(f"✅ PDF Forge WorkItem создан: {workitem_id}")
            return {'success': True, 'workitem_id': workitem_id}
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания PDF WorkItem: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _monitor_pdf_workitem(self, chat_id: str, job_id: str, workitem_id: str):
        """Мониторит выполнение PDF WorkItem"""
        try:
            start_time = time.time()
            
            while time.time() - start_time < self.job_timeout:
                # Проверяем статус WorkItem
                status = await self._check_forge_workitem_status(workitem_id)
                
                if status['status'] == 'success':
                    await self._handle_pdf_ready(chat_id, job_id)
                    return
                elif status['status'] == 'failed':
                    await self._handle_processing_error(chat_id, job_id, status.get('error', 'PDF conversion failed'))
                    return
                elif status['status'] in ['pending', 'inprogress']:
                    # Продолжаем ждать
                    await asyncio.sleep(30)
                else:
                    logger.warning(f"⚠️ Неизвестный статус PDF WorkItem: {status}")
                    await asyncio.sleep(30)
            
            # Таймаут
            await self._handle_processing_timeout(chat_id, job_id, workitem_id)
            
        except Exception as e:
            logger.error(f"❌ Ошибка мониторинга PDF WorkItem: {e}")
            await self._handle_processing_error(chat_id, job_id, str(e))
    
    async def _handle_pdf_ready(self, chat_id: str, job_id: str):
        """Обрабатывает готовый PDF файл"""
        try:
            # Обновляем состояние
            await self.update_user_lock(chat_id, BotState.DONE)
            
            # Получаем готовый PDF файл
            pdf_path = f"ready/{chat_id}/{job_id}/out.pdf"
            pdf_url = self._create_signed_url(pdf_path, "GET")
            
            # Отправляем PDF пользователю
            message = f"📄 PDF готов: {pdf_url}"
            
            # В реальной реализации здесь был бы вызов Telegram Bot API
            logger.info(f"📤 Отправляем PDF пользователю {chat_id}: {message}")
            
            # Завершаем задачу
            await self._complete_task(chat_id, job_id)
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки готового PDF: {e}")
            await self._handle_processing_error(chat_id, job_id, str(e))
    
    async def _complete_task(self, chat_id: str, job_id: str):
        """Завершает задачу и снимает lock"""
        try:
            # Обновляем состояние
            await self.update_user_lock(chat_id, BotState.DONE)
            
            # Отправляем сообщение о завершении
            message = "✅ Задача завершена."
            
            # В реальной реализации здесь был бы вызов Telegram Bot API
            logger.info(f"✅ Задача завершена для {chat_id}: {message}")
            
            # Снимаем lock
            await self.clear_user_lock(chat_id)
            
        except Exception as e:
            logger.error(f"❌ Ошибка завершения задачи: {e}")
    
    async def _handle_processing_error(self, chat_id: str, job_id: str, error: str):
        """Обрабатывает ошибки обработки"""
        try:
            logger.error(f"❌ Ошибка обработки для {chat_id}, job {job_id}: {error}")
            
            # Отправляем сообщение об ошибке
            raw_url = self._create_signed_url(f"raw/{chat_id}/{job_id}/input.dwg", "GET")
            message = f"⛔ Ошибка обработки. Исходный DWG сохранён: {raw_url}"
            
            # В реальной реализации здесь был бы вызов Telegram Bot API
            logger.info(f"❌ Отправляем ошибку пользователю {chat_id}: {message}")
            
            # Снимаем lock
            await self.clear_user_lock(chat_id)
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки ошибки: {e}")
    
    async def _handle_processing_timeout(self, chat_id: str, job_id: str, workitem_id: str):
        """Обрабатывает таймаут обработки"""
        try:
            logger.warning(f"⏰ Таймаут обработки для {chat_id}, job {job_id}")
            
            # Отправляем сообщение о таймауте
            raw_url = self._create_signed_url(f"raw/{chat_id}/{job_id}/input.dwg", "GET")
            message = f"⏰ Превышено время обработки. Исходный DWG сохранён: {raw_url}"
            
            # В реальной реализации здесь был бы вызов Telegram Bot API
            logger.info(f"⏰ Отправляем таймаут пользователю {chat_id}: {message}")
            
            # Снимаем lock
            await self.clear_user_lock(chat_id)
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки таймаута: {e}")
    
    # Flask endpoints
    @app.route('/health', methods=['GET'])
    def health(self):
        """Health check endpoint"""
        return jsonify({
            'status': 'OK',
            'message': 'BTI Bot DWG-first mode is running',
            'timestamp': datetime.now().isoformat()
        })
    
    @app.route('/status/<chat_id>', methods=['GET'])
    def get_user_status(self, chat_id):
        """Получает статус пользователя"""
        try:
            # Здесь должна быть логика получения статуса из Firestore
            return jsonify({
                'chat_id': chat_id,
                'status': 'unknown'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500


# Глобальный экземпляр бота
bti_bot = BTIBotDWGFirst()

def main():
    """Основная функция для запуска бота"""
    try:
        # Получаем токен бота
        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token:
            logger.error("❌ BOT_TOKEN not found in environment variables")
            return
        
        # Создаем приложение
        application = Application.builder().token(bot_token).build()
        
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("bti", bti_bot.bti_command))
        
        # Добавляем обработчик документов
        application.add_handler(MessageHandler(filters.Document.ALL, bti_bot.handle_document))
        
        # Добавляем обработчик callback кнопок
        application.add_handler(CallbackQueryHandler(bti_bot.handle_pdf_callback))
        
        # Запускаем бота
        logger.info("🚀 Starting BTI Bot DWG-first mode...")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")

if __name__ == '__main__':
    main()
