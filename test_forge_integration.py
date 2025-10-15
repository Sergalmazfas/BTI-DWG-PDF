"""
Test Suite for Forge Integration
Тесты для интеграции AutoDesk Design Automation с BTI Processor
"""

import json
import time
import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import tempfile
import os

# Импорты наших модулей
from forge_controller import ForgeController
from forge_poller_service import ForgePollerService
from telegram_forge_integration import TelegramForgeIntegration
from forge_monitoring import ForgeMonitoring, ForgeErrorHandler

class TestForgeController:
    """Тесты для Forge Controller"""
    
    @pytest.fixture
    def forge_controller(self):
        """Создает экземпляр ForgeController для тестов"""
        with patch('forge_controller.storage.Client'), \
             patch('forge_controller.secretmanager.SecretManagerServiceClient'), \
             patch('forge_controller.pubsub_v1.PublisherClient'):
            return ForgeController("test-project")
    
    def test_get_access_token_success(self, forge_controller):
        """Тест успешного получения access token"""
        # Мокаем ответ API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test_token_123',
            'expires_in': 3600
        }
        
        with patch('requests.post', return_value=mock_response), \
             patch.object(forge_controller, '_get_secret') as mock_secret:
            
            mock_secret.side_effect = lambda x: 'test_id' if 'CLIENT_ID' in x else 'test_secret'
            
            token = forge_controller.get_access_token()
            
            assert token == 'test_token_123'
            assert forge_controller._access_token == 'test_token_123'
            assert forge_controller._token_expires is not None
    
    def test_get_access_token_failure(self, forge_controller):
        """Тест ошибки получения access token"""
        # Мокаем ошибку API
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        
        with patch('requests.post', return_value=mock_response), \
             patch.object(forge_controller, '_get_secret') as mock_secret:
            
            mock_secret.side_effect = lambda x: 'test_id' if 'CLIENT_ID' in x else 'test_secret'
            
            with pytest.raises(Exception, match="Forge authentication failed"):
                forge_controller.get_access_token()
    
    def test_create_signed_urls(self, forge_controller):
        """Тест создания signed URLs"""
        with patch.object(forge_controller.storage_client, 'bucket') as mock_bucket:
            mock_bucket_obj = Mock()
            mock_blob = Mock()
            mock_blob.generate_signed_url.return_value = 'https://signed-url.com'
            mock_bucket_obj.blob.return_value = mock_blob
            mock_bucket.return_value = mock_bucket_obj
            
            urls = forge_controller.create_signed_urls(
                'input/test.dwg',
                'output/result.dwg', 
                'templates/moscow.dwt'
            )
            
            assert 'input_url' in urls
            assert 'output_url' in urls
            assert 'template_url' in urls
            assert urls['input_url'] == 'https://signed-url.com'
    
    def test_submit_forge_job_success(self, forge_controller):
        """Тест успешной отправки задачи в Forge"""
        job_data = {
            'dwg': 'gs://btibot-processed/test.dwg',
            'template': 'moscow',
            'chat_id': '12345',
            'job_id': 'test-job-123',
            'meta': {'address': 'Test Address'}
        }
        
        # Мокаем все зависимости
        with patch.object(forge_controller, 'get_access_token', return_value='test_token'), \
             patch.object(forge_controller, 'create_signed_urls', return_value={
                 'input_url': 'https://input.url',
                 'output_url': 'https://output.url',
                 'template_url': 'https://template.url'
             }), \
             patch.object(forge_controller, '_save_job_info') as mock_save, \
             patch('requests.post') as mock_post:
            
            # Мокаем успешный ответ от Forge API
            mock_response = Mock()
            mock_response.status_code = 202
            mock_response.json.return_value = {'id': 'workitem-123'}
            mock_post.return_value = mock_response
            
            result = forge_controller.submit_forge_job(job_data)
            
            assert result['status'] == 'submitted'
            assert result['workitem_id'] == 'workitem-123'
            assert result['job_id'] == 'test-job-123'
            mock_save.assert_called_once()
    
    def test_submit_forge_job_api_error(self, forge_controller):
        """Тест ошибки API при отправке задачи"""
        job_data = {
            'dwg': 'gs://btibot-processed/test.dwg',
            'template': 'moscow',
            'chat_id': '12345',
            'job_id': 'test-job-123',
            'meta': {'address': 'Test Address'}
        }
        
        with patch.object(forge_controller, 'get_access_token', return_value='test_token'), \
             patch.object(forge_controller, 'create_signed_urls', return_value={
                 'input_url': 'https://input.url',
                 'output_url': 'https://output.url',
                 'template_url': 'https://template.url'
             }), \
             patch('requests.post') as mock_post:
            
            # Мокаем ошибку API
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = 'Bad Request'
            mock_post.return_value = mock_response
            
            with pytest.raises(Exception, match="Forge API error"):
                forge_controller.submit_forge_job(job_data)


class TestForgePollerService:
    """Тесты для Forge Poller Service"""
    
    @pytest.fixture
    def poller_service(self):
        """Создает экземпляр ForgePollerService для тестов"""
        with patch('forge_poller_service.storage.Client'), \
             patch('forge_poller_service.ForgeController'), \
             patch('forge_poller_service.pubsub_v1.PublisherClient'):
            return ForgePollerService("test-project")
    
    def test_poll_all_pending_jobs_no_jobs(self, poller_service):
        """Тест polling когда нет задач"""
        with patch.object(poller_service.storage_client, 'bucket') as mock_bucket:
            mock_bucket_obj = Mock()
            mock_bucket_obj.list_blobs.return_value = []
            mock_bucket.return_value = mock_bucket_obj
            
            result = poller_service.poll_all_pending_jobs()
            
            assert result['jobs_checked'] == 0
            assert result['jobs_updated'] == 0
            assert result['jobs_cleaned'] == 0
    
    def test_poll_job_success(self, poller_service):
        """Тест обработки успешной задачи"""
        job_info = {
            'job_id': 'test-job-123',
            'workitem_id': 'workitem-123',
            'status': 'submitted',
            'submitted_at': datetime.now().isoformat(),
            'chat_id': '12345',
            'template': 'moscow',
            'input_blob': 'input/test.dwg',
            'output_blob': 'output/result.dwg'
        }
        
        with patch.object(poller_service.forge_controller, 'get_job_status') as mock_status, \
             patch.object(poller_service, '_save_job_info') as mock_save, \
             patch.object(poller_service, '_save_report') as mock_report, \
             patch.object(poller_service, '_send_bot_notification') as mock_notify:
            
            # Мокаем успешный статус
            mock_status.return_value = {'status': 'success', 'result': 'completed'}
            
            result = poller_service._process_job(job_info)
            
            assert result['updated'] == True
            assert result['cleaned'] == False
            mock_save.assert_called()
            mock_report.assert_called()
            mock_notify.assert_called()
    
    def test_poll_job_failure(self, poller_service):
        """Тест обработки ошибки задачи"""
        job_info = {
            'job_id': 'test-job-123',
            'workitem_id': 'workitem-123',
            'status': 'submitted',
            'submitted_at': datetime.now().isoformat(),
            'chat_id': '12345',
            'template': 'moscow'
        }
        
        with patch.object(poller_service.forge_controller, 'get_job_status') as mock_status, \
             patch.object(poller_service, '_save_job_info') as mock_save, \
             patch.object(poller_service, '_send_bot_notification') as mock_notify:
            
            # Мокаем ошибку
            mock_status.return_value = {'status': 'failed', 'error': 'Processing failed'}
            
            result = poller_service._process_job(job_info)
            
            assert result['updated'] == True
            mock_save.assert_called()
            mock_notify.assert_called()
    
    def test_job_timeout(self, poller_service):
        """Тест таймаута задачи"""
        # Создаем задачу старше 30 минут
        old_time = datetime.now() - timedelta(minutes=35)
        job_info = {
            'job_id': 'test-job-123',
            'workitem_id': 'workitem-123',
            'status': 'submitted',
            'submitted_at': old_time.isoformat(),
            'chat_id': '12345',
            'template': 'moscow'
        }
        
        with patch.object(poller_service, '_save_job_info') as mock_save, \
             patch.object(poller_service, '_send_bot_notification') as mock_notify:
            
            result = poller_service._process_job(job_info)
            
            assert result['updated'] == True
            mock_save.assert_called()
            mock_notify.assert_called()


class TestTelegramForgeIntegration:
    """Тесты для интеграции с Telegram"""
    
    @pytest.fixture
    def telegram_integration(self):
        """Создает экземпляр TelegramForgeIntegration для тестов"""
        with patch('telegram_forge_integration.storage.Client'), \
             patch('telegram_forge_integration.pubsub_v1.SubscriberClient'):
            return TelegramForgeIntegration("test-project")
    
    @pytest.fixture
    def mock_context(self):
        """Создает мок контекста Telegram"""
        context = Mock()
        context.bot = Mock()
        context.bot.send_message = Mock()
        return context
    
    async def test_handle_success_notification(self, telegram_integration, mock_context):
        """Тест обработки уведомления об успехе"""
        notification_data = {
            'chat_id': '12345',
            'job_id': 'test-job-123',
            'status': 'success',
            'file': 'gs://btibot-processed/result.dwg',
            'report': 'gs://btibot-processed/report.json',
            'processing_time_ms': 45000,
            'template': 'moscow'
        }
        
        with patch.object(telegram_integration, '_create_download_url', return_value='https://download.url'):
            await telegram_integration.handle_forge_notification(notification_data, mock_context)
            
            mock_context.bot.send_message.assert_called_once()
            call_args = mock_context.bot.send_message.call_args
            assert call_args[1]['chat_id'] == '12345'
            assert 'БТИ-чертёж готов!' in call_args[1]['text']
    
    async def test_handle_failure_notification(self, telegram_integration, mock_context):
        """Тест обработки уведомления об ошибке"""
        notification_data = {
            'chat_id': '12345',
            'job_id': 'test-job-123',
            'status': 'failed',
            'error': 'Processing failed',
            'template': 'moscow'
        }
        
        await telegram_integration.handle_forge_notification(notification_data, mock_context)
        
        mock_context.bot.send_message.assert_called_once()
        call_args = mock_context.bot.send_message.call_args
        assert call_args[1]['chat_id'] == '12345'
        assert 'Ошибка обработки' in call_args[1]['text']
    
    def test_format_error_for_user(self, telegram_integration):
        """Тест форматирования ошибок для пользователя"""
        test_cases = [
            ('invalid dwg format', 'Неправильный формат DWG файла'),
            ('authentication failed', 'Ошибка авторизации в системе'),
            ('unknown error', 'Произошла ошибка при обработке файла')
        ]
        
        for error, expected in test_cases:
            result = telegram_integration._format_error_for_user(error)
            assert expected in result


class TestForgeMonitoring:
    """Тесты для мониторинга"""
    
    @pytest.fixture
    def monitoring(self):
        """Создает экземпляр ForgeMonitoring для тестов"""
        with patch('forge_monitoring.monitoring_v3.MetricServiceClient'):
            return ForgeMonitoring("test-project")
    
    def test_record_job_submitted(self, monitoring):
        """Тест записи отправки задачи"""
        with patch.object(monitoring, '_write_metric') as mock_write:
            monitoring.record_job_submitted('moscow')
            
            mock_write.assert_called_with(
                'forge_jobs_total', 
                1, 
                {'template': 'moscow', 'status': 'submitted'}
            )
    
    def test_record_job_completed(self, monitoring):
        """Тест записи завершения задачи"""
        with patch.object(monitoring, '_write_metric') as mock_write:
            monitoring.record_job_completed('moscow', 'success', 45000)
            
            assert mock_write.call_count == 2  # Два вызова: jobs_total и avg_duration_ms
    
    def test_record_job_failed(self, monitoring):
        """Тест записи ошибки задачи"""
        with patch.object(monitoring, '_write_metric') as mock_write:
            monitoring.record_job_failed('moscow', 'timeout error')
            
            mock_write.assert_called_with(
                'forge_jobs_failed',
                1,
                {'template': 'moscow', 'error_type': 'timeout'}
            )
    
    def test_categorize_error(self, monitoring):
        """Тест категоризации ошибок"""
        test_cases = [
            ('authentication failed', 'authentication'),
            ('request timeout', 'timeout'),
            ('invalid request', 'invalid_request'),
            ('server error 500', 'server_error'),
            ('network connection failed', 'network_error'),
            ('storage gcs error', 'storage_error'),
            ('unknown error', 'unknown')
        ]
        
        for error, expected in test_cases:
            result = monitoring._categorize_error(error)
            assert result == expected


class TestForgeErrorHandler:
    """Тесты для обработки ошибок"""
    
    @pytest.fixture
    def error_handler(self):
        """Создает экземпляр ForgeErrorHandler для тестов"""
        with patch('forge_monitoring.ForgeMonitoring'), \
             patch('forge_monitoring.monitoring_v3.MetricServiceClient'):
            return ForgeErrorHandler("test-project")
    
    def test_handle_authentication_error(self, error_handler):
        """Тест обработки ошибки авторизации"""
        error = requests.exceptions.HTTPError()
        error.response = Mock()
        error.response.status_code = 401
        error.response.text = 'Unauthorized'
        
        result = error_handler.handle_api_error(error, 'test_endpoint')
        
        assert result['error_type'] == 'authentication'
        assert result['error_code'] == 401
        assert result['should_retry'] == True  # Первая попытка
    
    def test_handle_server_error_retry(self, error_handler):
        """Тест повторной попытки при ошибке сервера"""
        error = requests.exceptions.HTTPError()
        error.response = Mock()
        error.response.status_code = 500
        error.response.text = 'Internal Server Error'
        
        result = error_handler.handle_api_error(error, 'test_endpoint', retry_count=1)
        
        assert result['error_type'] == 'server_error'
        assert result['error_code'] == 500
        assert result['should_retry'] == True
        assert result['retry_delay'] == 5
    
    def test_handle_bad_request_no_retry(self, error_handler):
        """Тест отсутствия повторной попытки при плохом запросе"""
        error = requests.exceptions.HTTPError()
        error.response = Mock()
        error.response.status_code = 400
        error.response.text = 'Bad Request'
        
        result = error_handler.handle_api_error(error, 'test_endpoint', retry_count=1)
        
        assert result['error_type'] == 'bad_request'
        assert result['should_retry'] == False


class TestIntegration:
    """Интеграционные тесты"""
    
    def test_end_to_end_workflow(self):
        """Тест полного workflow от отправки до получения результата"""
        # Этот тест проверяет интеграцию всех компонентов
        # В реальном проекте здесь были бы более детальные тесты
        
        # 1. Отправка задачи
        job_data = {
            'dwg': 'gs://btibot-processed/test.dwg',
            'template': 'moscow',
            'chat_id': '12345',
            'job_id': 'integration-test-123',
            'meta': {'address': 'Test Address'}
        }
        
        # 2. Mock всех внешних зависимостей
        with patch('forge_controller.requests.post') as mock_post, \
             patch('forge_controller.storage.Client'), \
             patch('forge_controller.secretmanager.SecretManagerServiceClient'):
            
            # Мокаем успешный ответ от Forge API
            mock_response = Mock()
            mock_response.status_code = 202
            mock_response.json.return_value = {'id': 'workitem-integration-123'}
            mock_post.return_value = mock_response
            
            # Создаем контроллер и отправляем задачу
            forge_controller = ForgeController("test-project")
            result = forge_controller.submit_forge_job(job_data)
            
            assert result['status'] == 'submitted'
            assert 'workitem_id' in result
    
    def test_error_recovery_workflow(self):
        """Тест восстановления после ошибок"""
        # Тест проверяет, что система корректно обрабатывает ошибки
        # и может восстановиться
        
        error_handler = ForgeErrorHandler("test-project")
        
        # Тестируем различные типы ошибок
        error_types = [
            ('authentication', 401),
            ('server_error', 500),
            ('timeout', 0),
            ('network', 0)
        ]
        
        for error_type, code in error_types:
            error = requests.exceptions.HTTPError()
            error.response = Mock()
            error.response.status_code = code
            error.response.text = f'{error_type} error'
            
            result = error_handler.handle_api_error(error, 'test_endpoint')
            
            assert 'error_type' in result
            assert 'should_retry' in result
            assert 'user_message' in result


# Фикстуры для тестов
@pytest.fixture
def sample_job_data():
    """Возвращает пример данных задачи"""
    return {
        'dwg': 'gs://btibot-processed/test.dwg',
        'template': 'moscow',
        'chat_id': '12345',
        'job_id': 'test-job-123',
        'meta': {
            'address': 'ул. Ленина, 10',
            'scale': '1:100',
            'executor': 'Иванов И.И.'
        }
    }


@pytest.fixture
def sample_notification_data():
    """Возвращает пример данных уведомления"""
    return {
        'chat_id': '12345',
        'job_id': 'test-job-123',
        'status': 'success',
        'file': 'gs://btibot-processed/result.dwg',
        'report': 'gs://btibot-processed/report.json',
        'processing_time_ms': 45000,
        'template': 'moscow'
    }


# Запуск тестов
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
