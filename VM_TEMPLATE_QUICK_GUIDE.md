# 🚀 Быстрая загрузка шаблона на VM

**VM:** instance-20251013-185458 (us-central1-c)  
**IP:** 34.58.217.128

---

## ⚡ Самый простой способ

### **1. Загрузить шаблон одной командой:**

```bash
gcloud compute scp \
  bte-appbundle/archives/basmannyi_novyi_obmernyi.dwg \
  instance-20251013-185458:bti_template.dwg \
  --zone=us-central1-c
```

**Файл появится на VM по пути:** `C:\Users\<username>\bti_template.dwg`

---

### **2. Или скачать на VM из GCS:**

**Подключиться к VM:**
```bash
gcloud compute rdp instance-20251013-185458 --zone=us-central1-c
```

**На VM в PowerShell выполнить:**
```powershell
# Скачать шаблон из GCS
Invoke-WebRequest -Uri "https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg" -OutFile "C:\bti_template.dwg"

# Проверить
Get-Item C:\bti_template.dwg
```

---

### **3. Использовать Postman на VM:**

Если Postman уже установлен на VM:

```
Method: GET
URL: https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg

Send → Save Response to File
→ Сохранить как: C:\bti_template.dwg
```

---

## ✅ Проверка

После загрузки проверить размер:

**Должно быть:** ~51-52 KB

---

## 📋 Что дальше

После загрузки шаблона на VM можно:
1. Использовать в .NET плагине BTI_InsertBasman
2. Компилировать AppBundle с шаблоном
3. Загрузить AppBundle в Autodesk APS

---

**💡 Самый быстрый вариант - использовать публичный URL:**

```
https://storage.googleapis.com/btibot-processed/templates/bti_basmanny_template.dwg
```

Этот URL можно использовать напрямую в Activity без загрузки на VM!


