# ✅ Контрольный чек-лист перед загрузкой в APS

| Шаг | Проверка | Статус |
|-----|----------|--------|
| 1 | В каталоге `BTI_TemplateAppBundle.bundle/Contents/` лежат `BTI_TemplatePlugin.dll`, `BTI_Template.dwt`, `PackageContents.xml` | ✅ |
| 2 | ZIP-архив называется строго `BTI_TemplateAppBundle.bundle.zip` | ✅ |
| 3 | В `PackageContents.xml` указаны `<RuntimeRequirements OS="Windows" Platform="AutoCAD" SeriesMin="R25.1"/>` | ✅ |
| 4 | В коде плагина команда `ApplyBTITemplate` — единственная экспортируемая | ✅ |
| 5 | В Cloud Run `forge_client.py` нет PlotToPDF, Model Derivative или PDF-mime-типов | ✅ |
| 6 | Environment vars: FORGE_CLIENT_ID, FORGE_CLIENT_SECRET, BOT_TOKEN — заданы | ✅ |
| 7 | В APS панели будет создаваться AppBundle → alias v1 → Activity BTI_DWG2DWG+v1 | ⚙️ предстоит |
| 8 | После создания Activity бот автоматически сможет вызывать WorkItem DWG→DWG | 🔜 |

---

## 🎯 Статус: READY FOR UPLOAD

Все файлы созданы и готовы к компиляции на Windows!

