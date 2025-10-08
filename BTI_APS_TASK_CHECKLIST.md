# ✅ BTI_APS_TASK_CHECKLIST.md  

## Интеграция DWG→DWG через Autodesk APS (Design Automation API)

---

## 🔹 ЭТАП 1. Подготовка окружения

**Цель:** убедиться, что окружение готово для интеграции с Autodesk APS.

- [x] 1.1 Проверить доступ к [APS Dashboard](https://aps.autodesk.com/dashboard)  
- [x] 1.2 Проверить наличие Forge API ключей (`FORGE_CLIENT_ID`, `FORGE_CLIENT_SECRET`) в Google Secret Manager  
- [x] 1.3 Проверить GCS директории `system/appbundles/` и `system/templates/`  
- [x] 1.4 Проверить связь `telegram-bot-commands` с Forge API через `POST /authentication/v2/token`  

---

## 🔹 ЭТАП 2. Подготовка AppBundle

**Цель:** подготовить плагин и собрать ZIP-архив для загрузки.

- [x] 2.1 Проверить структуру папки `BTI_TemplateAppBundle.bundle/Contents`  
- [x] 2.2 Проверить корректность `PackageContents.xml`  
- [x] 2.3 Убедиться, что команда `ApplyBTITemplate` реализована в DLL  
- [ ] 2.4 Собрать ZIP-архив `BTI_TemplateAppBundle.bundle.zip` (см. `BUILD.md`)  

**Ожидаемая структура ZIP:**
```
BTI_TemplateAppBundle.bundle/
└── Contents/
    ├── PackageContents.xml
    ├── BTI_TemplatePlugin.dll
    └── BTI_Template.dwt
```

---

## 🔹 ЭТАП 3. Загрузка в Autodesk APS (через Dashboard)

**Цель:** загрузить AppBundle и Activity вручную для первого теста.

- [ ] 3.1 Открыть [AppBundles Dashboard](https://aps.autodesk.com/dashboard/designautomation/appbundles)  
- [ ] 3.2 Создать новый AppBundle `BTI_TemplateAppBundle`  
- [ ] 3.3 Загрузить ZIP-архив  
- [ ] 3.4 Создать alias `v1`  
- [ ] 3.5 Перейти в [Activities Dashboard](https://aps.autodesk.com/dashboard/designautomation/activities)  
- [ ] 3.6 Создать Activity `BTI_DWG2DWG` и привязать AppBundle  
- [ ] 3.7 Создать alias `v1` для Activity  
- [ ] 3.8 Проверить, что Activity появляется в списке и активна  

---

## 🔹 ЭТАП 4. Проверка через Postman

**Цель:** протестировать работу через официальный walkthrough.

- [ ] 4.1 Установить [Postman](https://www.postman.com/downloads/)  
- [ ] 4.2 Импортировать коллекцию [DA4ACAD](https://github.com/autodesk-platform-services/aps-tutorial-postman/tree/master/DA4ACAD)  
- [ ] 4.3 Настроить `client_id`, `client_secret` в Environment  
- [ ] 4.4 Выполнить шаги:
    - Authenticate
    - Register AppBundle
    - Upload AppBundle
    - Create Activity
    - Submit WorkItem  
- [ ] 4.5 Проверить `WorkItem status = success` и получить результат DWG  

---

## 🔹 ЭТАП 5. Автоматизация (GCS → APS)

**Цель:** курсор должен уметь синхронизировать AppBundle/Activity напрямую из GCS.

- [ ] 5.1 Создать скрипт `forge_sync.py`  
- [ ] 5.2 Добавить команду `/sync_forge` в Telegram Bot  
- [ ] 5.3 Проверять наличие ZIP в `gs://btibot-processed/system/appbundles/`  
- [ ] 5.4 Реализовать регистрацию AppBundle через API  
- [ ] 5.5 Реализовать загрузку ZIP на signed URL  
- [ ] 5.6 Создать Activity `BTI_DWG2DWG` через API  
- [ ] 5.7 Сохранять результат синхронизации в `bti_appbundle.json`  
- [ ] 5.8 Отправлять результат в Telegram: `✅ AppBundle synced successfully`  

---

## 🔹 ЭТАП 6. Интеграция с Telegram Bot

**Цель:** включить APS в рабочий поток DWG→DWG.

- [x] 6.1 Обновить `forge_client.py` → использовать `BTI_DWG2DWG+v1`  
- [ ] 6.2 Проверить обработку реального DWG через бот  
- [ ] 6.3 Проверить логи WorkItem в APS Dashboard  
- [ ] 6.4 Проверить загрузку результата DWG в GCS  
- [ ] 6.5 Проверить время выполнения (≤ 3 сек)  

---

## 🔹 ЭТАП 7. Поддержка и обновления

**Цель:** автоматизировать обновления и контроль версий.

- [ ] 7.1 Реализовать `/check_forge` для проверки версии AppBundle  
- [ ] 7.2 Настроить CI/CD для пересборки при изменении ZIP  
- [ ] 7.3 Добавить уведомления об ошибках WorkItem в Telegram  
- [ ] 7.4 Обновить документацию `FORGE_SYNC.md`  

---

## 🎯 Итог

После выполнения всех пунктов:

- [x] DWG→DWG работает без PDF  
- [ ] AppBundle автоматически синхронизируется  
- [ ] WorkItems выполняются через Autodesk AutoCAD Cloud  
- [x] Telegram Bot стабильно возвращает DWG-файлы  
- [ ] Система готова к продакшену  

---

🧭 **Финальная цель:**  
Полностью автономная интеграция BTI DWG→DWG через Autodesk APS (AutoCAD+25_1)  
с поддержкой шаблонов и управлением через Telegram-бота.

---

## 📊 ТЕКУЩИЙ СТАТУС

**Дата обновления:** 2025-10-07  
**Revision:** telegram-bot-commands-00052-65l  
**PDF код:** ❌ УДАЛЕН  
**Activity:** BTI_DWG2DWG+v1 (ожидает создания в APS)  
**Fallback:** ✅ Работает  
**Bot:** ✅ Production-ready  

---

## 🔗 ПОЛЕЗНЫЕ ССЫЛКИ

- [APS Dashboard](https://aps.autodesk.com)
- [Design Automation API Docs](https://aps.autodesk.com/en/docs/design-automation/v3)
- [AppBundle Tutorial](https://aps.autodesk.com/en/docs/design-automation/v3/tutorials/autocad/)
- [GitHub Examples](https://github.com/autodesk-platform-services/aps-design-automation-autocad)

---

## 📝 ПРИМЕЧАНИЯ

- **API ограничения:** `/aliases` endpoint может не работать с длинными Client IDs → использовать Web UI
- **Компиляция:** Требуется Windows + Visual Studio + AutoCAD .NET API
- **Тестирование:** Используйте `test_bti_workitem.py` для проверки
- **Документация:** См. `WEB_UI_UPLOAD_GUIDE.md` для детальных шагов

---

**Последнее обновление:** 2025-10-07 16:35 MSK  
**Статус:** Ready for AppBundle upload  
**Next step:** Компиляция на Windows → Загрузка через Web UI

