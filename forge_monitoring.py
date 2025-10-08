"""
Forge Monitoring and Error Handling
Мониторинг AutoDesk Design Automation и обработка ошибок
"""

import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from google.cloud import monitoring_v3, storage
from google.cloud.monitoring_v3 import AlertPolicy, NotificationChannel
import requests

logger = logging.getLogger(__name__)

class ForgeMonitoring:
    """Мониторинг и метрики для Forge API"""
    
    def __init__(self, project_id: str = "talkhint"):
        self.project_id = project_id
        self.client = monitoring_v3.MetricServiceClient()
        self.project_name = f"projects/{project_id}"
        
        # Настройки метрик
        self.metric_descriptors = {
            'forge_jobs_total': {
                'type': 'custom.googleapis.com/forge/jobs_total',
                'display_name': 'Forge Jobs Total',
                'description': 'Total number of Forge jobs submitted',
                'labels': ['template', 'status']
            },
            'forge_jobs_failed': {
                'type': 'custom.googleapis.com/forge/jobs_failed',
                'display_name': 'Forge Jobs Failed',
                'description': 'Number of failed Forge jobs',
                'labels': ['template', 'error_type']
            },
            'forge_avg_duration_ms': {
                'type': 'custom.googleapis.com/forge/avg_duration_ms',
                'display_name': 'Forge Average Duration',
                'description': 'Average duration of Forge jobs in milliseconds',
                'labels': ['template', 'status']
            },
            'forge_api_errors': {
                'type': 'custom.googleapis.com/forge/api_errors',
                'display_name': 'Forge API Errors',
                'description': 'Number of Forge API errors',
                'labels': ['error_code', 'endpoint']
            }
        }
        
        # Инициализируем метрики
        self._initialize_metrics()
    
    def _initialize_metrics(self):
        """Инициализирует метрики в Cloud Monitoring"""
        try:
            for metric_name, descriptor in self.metric_descriptors.items():
                self._create_metric_descriptor(descriptor)
            
            logger.info("✅ Forge metrics initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Error initializing Forge metrics: {e}")
    
    def _create_metric_descriptor(self, descriptor: Dict[str, Any]):
        """Создает дескриптор метрики"""
        try:
            metric_descriptor = monitoring_v3.MetricDescriptor(
                type=descriptor['type'],
                metric_kind=monitoring_v3.MetricDescriptor.MetricKind.COUNTER,
                value_type=monitoring_v3.MetricDescriptor.ValueType.INT64,
                display_name=descriptor['display_name'],
                description=descriptor['description']
            )
            
            # Добавляем лейблы
            for label_name in descriptor['labels']:
                label_descriptor = monitoring_v3.LabelDescriptor(
                    key=label_name,
                    value_type=monitoring_v3.LabelDescriptor.ValueType.STRING,
                    description=f"Label for {label_name}"
                )
                metric_descriptor.labels.append(label_descriptor)
            
            # Создаем дескриптор (если не существует)
            try:
                self.client.create_metric_descriptor(
                    name=self.project_name,
                    metric_descriptor=metric_descriptor
                )
                logger.info(f"✅ Created metric descriptor: {descriptor['type']}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info(f"ℹ️ Metric descriptor already exists: {descriptor['type']}")
                else:
                    raise e
                    
        except Exception as e:
            logger.error(f"❌ Error creating metric descriptor {descriptor['type']}: {e}")
    
    def record_job_submitted(self, template: str):
        """Записывает отправку задачи"""
        self._write_metric('forge_jobs_total', 1, {'template': template, 'status': 'submitted'})
    
    def record_job_completed(self, template: str, status: str, duration_ms: float):
        """Записывает завершение задачи"""
        self._write_metric('forge_jobs_total', 1, {'template': template, 'status': status})
        self._write_metric('forge_avg_duration_ms', duration_ms, {'template': template, 'status': status})
    
    def record_job_failed(self, template: str, error: str):
        """Записывает ошибку задачи"""
        error_type = self._categorize_error(error)
        self._write_metric('forge_jobs_failed', 1, {'template': template, 'error_type': error_type})
    
    def record_api_error(self, error_code: int, endpoint: str):
        """Записывает ошибку API"""
        self._write_metric('forge_api_errors', 1, {
            'error_code': str(error_code),
            'endpoint': endpoint
        })
    
    def _categorize_error(self, error: str) -> str:
        """Категоризирует ошибку для метрик"""
        error_lower = error.lower()
        
        if 'authentication' in error_lower or '401' in error_lower:
            return 'authentication'
        elif 'timeout' in error_lower:
            return 'timeout'
        elif 'invalid' in error_lower or '400' in error_lower:
            return 'invalid_request'
        elif 'server' in error_lower or '500' in error_lower:
            return 'server_error'
        elif 'network' in error_lower or 'connection' in error_lower:
            return 'network_error'
        elif 'storage' in error_lower or 'gcs' in error_lower:
            return 'storage_error'
        else:
            return 'unknown'
    
    def _write_metric(self, metric_name: str, value: float, labels: Dict[str, str]):
        """Записывает метрику в Cloud Monitoring"""
        try:
            descriptor = self.metric_descriptors[metric_name]
            series = monitoring_v3.TimeSeries()
            series.metric.type = descriptor['type']
            
            # Добавляем лейблы
            for key, value in labels.items():
                series.metric.labels[key] = value
            
            # Добавляем точку данных
            point = monitoring_v3.Point()
            point.value.int64_value = int(value)
            point.interval.end_time.seconds = int(time.time())
            series.points.append(point)
            
            # Записываем серию
            self.client.create_time_series(
                name=self.project_name,
                time_series=[series]
            )
            
            logger.debug(f"📊 Metric recorded: {metric_name}={value}, labels={labels}")
            
        except Exception as e:
            logger.error(f"❌ Error writing metric {metric_name}: {e}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Получает сводку метрик"""
        try:
            # Здесь должна быть логика получения метрик из Cloud Monitoring
            # Упрощенная версия для демонстрации
            return {
                'forge_jobs_total': {'last_24h': 150, 'last_1h': 12},
                'forge_jobs_failed': {'last_24h': 3, 'last_1h': 0},
                'forge_avg_duration_ms': {'last_24h': 45000, 'last_1h': 38000},
                'forge_api_errors': {'last_24h': 1, 'last_1h': 0}
            }
        except Exception as e:
            logger.error(f"❌ Error getting metrics summary: {e}")
            return {}


class ForgeErrorHandler:
    """Обработка ошибок Forge API"""
    
    def __init__(self, project_id: str = "talkhint"):
        self.project_id = project_id
        self.monitoring = ForgeMonitoring(project_id)
        self.max_retries = 3
        self.retry_delays = [1, 5, 15]  # секунды
    
    def handle_api_error(self, error: Exception, endpoint: str, 
                        retry_count: int = 0) -> Dict[str, Any]:
        """Обрабатывает ошибку API"""
        try:
            error_info = self._analyze_error(error)
            
            # Записываем метрику ошибки
            self.monitoring.record_api_error(error_info['code'], endpoint)
            
            # Определяем стратегию обработки
            strategy = self._determine_retry_strategy(error_info, retry_count)
            
            result = {
                'error_type': error_info['type'],
                'error_message': error_info['message'],
                'error_code': error_info['code'],
                'endpoint': endpoint,
                'retry_count': retry_count,
                'strategy': strategy,
                'should_retry': strategy['should_retry'],
                'retry_delay': strategy['delay'],
                'user_message': strategy['user_message']
            }
            
            logger.error(f"❌ Forge API error handled: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in error handler: {e}")
            return {
                'error_type': 'handler_error',
                'error_message': str(e),
                'should_retry': False,
                'user_message': 'Произошла критическая ошибка. Обратитесь к администратору.'
            }
    
    def _analyze_error(self, error: Exception) -> Dict[str, Any]:
        """Анализирует ошибку и извлекает информацию"""
        error_str = str(error).lower()
        
        # HTTP ошибки
        if hasattr(error, 'response'):
            status_code = getattr(error.response, 'status_code', 0)
            response_text = getattr(error.response, 'text', '')
            
            if status_code == 401:
                return {
                    'type': 'authentication',
                    'code': 401,
                    'message': 'Authentication failed - token expired or invalid'
                }
            elif status_code == 400:
                return {
                    'type': 'bad_request',
                    'code': 400,
                    'message': f'Bad request: {response_text}'
                }
            elif status_code == 429:
                return {
                    'type': 'rate_limit',
                    'code': 429,
                    'message': 'Rate limit exceeded'
                }
            elif status_code >= 500:
                return {
                    'type': 'server_error',
                    'code': status_code,
                    'message': f'Server error: {response_text}'
                }
        
        # Таймауты
        if 'timeout' in error_str or 'timed out' in error_str:
            return {
                'type': 'timeout',
                'code': 0,
                'message': 'Request timeout'
            }
        
        # Сетевые ошибки
        if 'connection' in error_str or 'network' in error_str:
            return {
                'type': 'network',
                'code': 0,
                'message': 'Network connection error'
            }
        
        # Неизвестная ошибка
        return {
            'type': 'unknown',
            'code': 0,
            'message': str(error)
        }
    
    def _determine_retry_strategy(self, error_info: Dict[str, Any], 
                                 retry_count: int) -> Dict[str, Any]:
        """Определяет стратегию повторных попыток"""
        error_type = error_info['type']
        error_code = error_info['code']
        
        # Критические ошибки - не повторяем
        if error_type in ['authentication', 'bad_request'] and retry_count > 0:
            return {
                'should_retry': False,
                'delay': 0,
                'user_message': 'Ошибка авторизации или неверный запрос. Проверьте настройки.'
            }
        
        # Ошибки, которые можно повторить
        if error_type in ['server_error', 'timeout', 'network', 'rate_limit']:
            if retry_count < self.max_retries:
                delay = self.retry_delays[min(retry_count, len(self.retry_delays) - 1)]
                return {
                    'should_retry': True,
                    'delay': delay,
                    'user_message': f'Временная ошибка. Повтор через {delay} сек...'
                }
            else:
                return {
                    'should_retry': False,
                    'delay': 0,
                    'user_message': 'Превышено максимальное количество попыток. Попробуйте позже.'
                }
        
        # Ошибки авторизации - повторяем с обновлением токена
        if error_type == 'authentication' and retry_count == 0:
            return {
                'should_retry': True,
                'delay': 1,
                'user_message': 'Обновление токена авторизации...'
            }
        
        # По умолчанию не повторяем
        return {
            'should_retry': False,
            'delay': 0,
            'user_message': 'Произошла ошибка при обработке. Попробуйте позже.'
        }
    
    def retry_with_backoff(self, func, *args, **kwargs) -> Any:
        """Выполняет функцию с повторными попытками"""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"✅ Retry successful on attempt {attempt + 1}")
                return result
                
            except Exception as e:
                last_error = e
                error_result = self.handle_api_error(e, kwargs.get('endpoint', 'unknown'), attempt)
                
                if not error_result['should_retry'] or attempt >= self.max_retries:
                    break
                
                delay = error_result['retry_delay']
                logger.warning(f"⚠️ Retry {attempt + 1}/{self.max_retries} in {delay}s: {error_result['error_message']}")
                time.sleep(delay)
        
        # Если все попытки исчерпаны
        raise last_error


class ForgeAlertManager:
    """Управление алертами для Forge API"""
    
    def __init__(self, project_id: str = "talkhint"):
        self.project_id = project_id
        self.client = monitoring_v3.AlertPolicyServiceClient()
        self.notification_client = monitoring_v3.NotificationChannelServiceClient()
        self.project_name = f"projects/{project_id}"
    
    def setup_forge_alerts(self, notification_email: str = "admin@example.com"):
        """Настраивает алерты для Forge API"""
        try:
            # Создаем канал уведомлений
            notification_channel = self._create_notification_channel(notification_email)
            
            # Создаем алерты
            alerts = [
                self._create_high_error_rate_alert(),
                self._create_slow_processing_alert(),
                self._create_api_error_alert()
            ]
            
            for alert in alerts:
                alert.notification_channels.append(notification_channel.name)
                self._create_alert_policy(alert)
            
            logger.info("✅ Forge alerts configured successfully")
            
        except Exception as e:
            logger.error(f"❌ Error setting up Forge alerts: {e}")
    
    def _create_notification_channel(self, email: str) -> NotificationChannel:
        """Создает канал уведомлений"""
        notification_channel = NotificationChannel(
            type_="email",
            display_name="Forge Alerts",
            labels={
                "email_address": email
            }
        )
        
        return self.notification_client.create_notification_channel(
            name=self.project_name,
            notification_channel=notification_channel
        )
    
    def _create_high_error_rate_alert(self) -> AlertPolicy:
        """Создает алерт на высокий процент ошибок"""
        return AlertPolicy(
            display_name="Forge High Error Rate",
            documentation=AlertPolicy.Documentation(
                content="Alert when Forge job failure rate exceeds 5% over 15 minutes"
            ),
            conditions=[
                AlertPolicy.Condition(
                    display_name="High failure rate",
                    condition_threshold=AlertPolicy.Condition.MetricThreshold(
                        filter='metric.type="custom.googleapis.com/forge/jobs_failed"',
                        comparison=AlertPolicy.Condition.MetricThreshold.ComparisonType.COMPARISON_GREATER_THAN,
                        threshold_value=5.0,
                        duration={"seconds": 900}  # 15 minutes
                    )
                )
            ],
            combiner=AlertPolicy.ConditionCombinerType.OR,
            enabled=True
        )
    
    def _create_slow_processing_alert(self) -> AlertPolicy:
        """Создает алерт на медленную обработку"""
        return AlertPolicy(
            display_name="Forge Slow Processing",
            documentation=AlertPolicy.Documentation(
                content="Alert when average Forge processing time exceeds 8 minutes"
            ),
            conditions=[
                AlertPolicy.Condition(
                    display_name="Slow processing",
                    condition_threshold=AlertPolicy.Condition.MetricThreshold(
                        filter='metric.type="custom.googleapis.com/forge/avg_duration_ms"',
                        comparison=AlertPolicy.Condition.MetricThreshold.ComparisonType.COMPARISON_GREATER_THAN,
                        threshold_value=480000,  # 8 minutes in milliseconds
                        duration={"seconds": 900}  # 15 minutes
                    )
                )
            ],
            combiner=AlertPolicy.ConditionCombinerType.OR,
            enabled=True
        )
    
    def _create_api_error_alert(self) -> AlertPolicy:
        """Создает алерт на ошибки API"""
        return AlertPolicy(
            display_name="Forge API Errors",
            documentation=AlertPolicy.Documentation(
                content="Alert when Forge API errors occur"
            ),
            conditions=[
                AlertPolicy.Condition(
                    display_name="API errors",
                    condition_threshold=AlertPolicy.Condition.MetricThreshold(
                        filter='metric.type="custom.googleapis.com/forge/api_errors"',
                        comparison=AlertPolicy.Condition.MetricThreshold.ComparisonType.COMPARISON_GREATER_THAN,
                        threshold_value=0,
                        duration={"seconds": 300}  # 5 minutes
                    )
                )
            ],
            combiner=AlertPolicy.ConditionCombinerType.OR,
            enabled=True
        )
    
    def _create_alert_policy(self, alert_policy: AlertPolicy):
        """Создает политику алерта"""
        try:
            self.client.create_alert_policy(
                name=self.project_name,
                alert_policy=alert_policy
            )
            logger.info(f"✅ Created alert policy: {alert_policy.display_name}")
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info(f"ℹ️ Alert policy already exists: {alert_policy.display_name}")
            else:
                raise e


# Интеграция с основным приложением
def add_monitoring_to_forge_controller(forge_controller):
    """Добавляет мониторинг к Forge Controller"""
    
    # Создаем экземпляры мониторинга
    monitoring = ForgeMonitoring()
    error_handler = ForgeErrorHandler()
    
    # Оборачиваем методы контроллера
    original_submit_forge_job = forge_controller.submit_forge_job
    
    def monitored_submit_forge_job(job_data):
        """Версия submit_forge_job с мониторингом"""
        try:
            # Записываем метрику отправки
            monitoring.record_job_submitted(job_data.get('template', 'unknown'))
            
            # Выполняем с обработкой ошибок
            result = error_handler.retry_with_backoff(
                original_submit_forge_job,
                job_data,
                endpoint='submit_workitem'
            )
            
            return result
            
        except Exception as e:
            # Записываем метрику ошибки
            monitoring.record_job_failed(
                job_data.get('template', 'unknown'),
                str(e)
            )
            raise
    
    # Заменяем метод
    forge_controller.submit_forge_job = monitored_submit_forge_job
    forge_controller.monitoring = monitoring
    forge_controller.error_handler = error_handler
    
    return forge_controller
