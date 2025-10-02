# Настройка Cloud Build триггера для BTI-DWG-PDF

## ✅ Статус деплоя

**Ручной деплой выполнен успешно!** 
- ✅ Сервис `dwg-processor-metadata` обновлен новым кодом
- ✅ Health check: `{"status":"OK","message":"BTI DWG → PDF Converter is running"}`
- ✅ Status endpoint работает корректно
- ✅ Все переменные окружения и секреты сохранены

## 🔧 Настройка автоматического триггера

### Вариант 1: Через Google Cloud Console (рекомендуется)

1. **Перейдите в Cloud Build Console**:
   - https://console.cloud.google.com/cloud-build/triggers?project=talkhint

2. **Создайте новый триггер**:
   - Нажмите "Создать триггер"
   - **Название**: `btidwg-deploy`
   - **Событие**: Push в ветку
   - **Источник**: GitHub → `Sergalmazfas/BTI-DWG-PDF`
   - **Ветка**: `^main$`
   - **Конфигурация**: Cloud Build configuration file (yaml или json)
   - **Расположение**: `/cloudbuild.yaml`

3. **Настройки триггера**:
   - **Сервисный аккаунт**: `637190449180-compute@developer.gserviceaccount.com`
   - **Регион**: europe-west1

4. **Сохраните триггер**

### Вариант 2: Через gcloud CLI

```bash
# Подключите GitHub репозиторий к Cloud Build
gcloud source repos create BTI-DWG-PDF --project=talkhint

# Создайте триггер
gcloud builds triggers create github \
  --repo-name=BTI-DWG-PDF \
  --repo-owner=Sergalmazfas \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml \
  --name=btidwg-deploy \
  --description="Build and deploy BTI DWG → PDF Converter to dwg-processor-metadata service"
```

### Вариант 3: Редактирование существующего триггера

Если есть существующий триггер для `dwg-processor-metadata`:

1. Найдите триггер в Cloud Build Console
2. Нажмите "Редактировать"
3. Измените репозиторий на `Sergalmazfas/BTI-DWG-PDF`
4. Обновите конфигурацию на `cloudbuild.yaml`
5. Сохраните изменения

## 🧪 Тестирование автоматического деплоя

После настройки триггера:

1. **Сделайте тестовое изменение**:
   ```bash
   echo "# Test deployment $(date)" >> README.md
   git add README.md
   git commit -m "Test automatic deployment trigger"
   git push origin main
   ```

2. **Проверьте Cloud Build**:
   - Перейдите в Cloud Build Console
   - Убедитесь, что сборка запустилась автоматически
   - Дождитесь завершения

3. **Проверьте сервис**:
   ```bash
   curl https://dwg-processor-metadata-637190449180.europe-west1.run.app/health
   ```

## 📊 Мониторинг

### Логи Cloud Build
- **URL**: https://console.cloud.google.com/cloud-build/builds?project=talkhint
- **Фильтр**: `trigger:btidwg-deploy`

### Логи Cloud Run
- **URL**: https://console.cloud.google.com/run/detail/europe-west1/dwg-processor-metadata?project=talkhint
- **Логи**: https://console.cloud.google.com/logs?project=talkhint

### Health Check
```bash
# Проверка состояния
curl https://dwg-processor-metadata-637190449180.europe-west1.run.app/health

# Подробная информация
curl https://dwg-processor-metadata-637190449180.europe-west1.run.app/status
```

## 🎯 Критерии готовности

- ✅ Cloud Run сервис `dwg-processor-metadata` работает с кодом из нового репозитория
- ✅ Все секреты и переменные окружения подтягиваются без изменений
- ✅ Telegram-бот готов принимать файлы и возвращать PDF
- 🔄 Настройка автоматического триггера (выполняется через Console)

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи Cloud Build
2. Проверьте логи Cloud Run
3. Убедитесь, что секреты настроены корректно
4. Проверьте права доступа сервисного аккаунта

---

**Статус**: ✅ Деплой успешно переведен на новый репозиторий!
**Следующий шаг**: Настройка автоматического триггера через Console
