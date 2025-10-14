# 🪟 Windows VM Troubleshooting Guide

## ❌ Ошибка: "Did not receive password in a reasonable amount of time"

### Причина:
GCE Windows Agent ещё не запустился полностью. Windows VM требует **5-10 минут** для первой загрузки.

---

## ✅ Решение (выполнить в Google Cloud Shell):

### Шаг 1: Проверить статус VM

```bash
gcloud compute instances describe "instance-20251013-145106" \
  --zone="us-east1-c" \
  --project="talkhint" \
  --format="get(status)"
```

**Ожидаемый результат:** `RUNNING`

---

### Шаг 2: Проверить серийный порт (логи загрузки Windows)

```bash
gcloud compute instances get-serial-port-output "instance-20251013-145106" \
  --zone="us-east1-c" \
  --project="talkhint" \
  | grep -E "(GCEAgent|Instance setup|ready|password)" | tail -n 20
```

**Ищите строки:**
```
GCEAgent: GCE Agent Started
GCEMetadataScripts: Starting startup scripts
Instance setup finished. Instance is ready to use.
```

Если **НЕТ** таких строк → VM ещё загружается, подождать 5 минут.

---

### Шаг 3: Подождать 5-10 минут и повторить

```bash
# Подождать 5-10 минут, затем:
gcloud beta compute reset-windows-password "instance-20251013-145106" \
  --zone="us-east1-c" \
  --project="talkhint"
```

---

### Шаг 4 (альтернатива): Указать конкретного пользователя

```bash
# Попробовать с явным указанием пользователя:
gcloud beta compute reset-windows-password "instance-20251013-145106" \
  --zone="us-east1-c" \
  --project="talkhint" \
  --user="administrator"
```

---

## 🔧 Если ничего не помогает:

### Проверить firewall для RDP:

```bash
# Проверить существующие правила
gcloud compute firewall-rules list --project="talkhint" --filter="name~rdp"

# Создать правило RDP (если не существует)
gcloud compute firewall-rules create allow-rdp \
  --project="talkhint" \
  --allow=tcp:3389 \
  --source-ranges=0.0.0.0/0 \
  --description="Allow RDP"
```

### Перезапустить VM:

```bash
# Остановить
gcloud compute instances stop "instance-20251013-145106" \
  --zone="us-east1-c" \
  --project="talkhint"

# Подождать 30 секунд

# Запустить
gcloud compute instances start "instance-20251013-145106" \
  --zone="us-east1-c" \
  --project="talkhint"

# Подождать 5 минут, затем снова сбросить пароль
```

---

## 📊 Timeline первой загрузки Windows VM:

| Время | Событие |
|-------|---------|
| 0:00 | VM создана, статус RUNNING |
| 0:30 | Windows начинает загрузку |
| 2:00 | Windows загружает драйверы |
| 3:00 | GCE Agent устанавливается |
| 5:00 | GCE Agent запускается |
| 7:00 | ✅ Metadata service готов |
| 8:00 | ✅ Можно сбросить пароль |

---

## 🎯 Рекомендация:

**Подождать 10 минут** с момента создания VM, затем повторить:

```bash
gcloud beta compute reset-windows-password "instance-20251013-145106" \
  --zone="us-east1-c" \
  --project="talkhint"
```

---

## 📝 Текущее время создания VM:

**Создано:** ~15:00 UTC (судя по имени `instance-20251013-145106`)  
**Попытка сброса:** 15:26 UTC  
**Прошло:** ~26 минут

⚠️ **Если прошло > 15 минут, но ошибка повторяется** → проверить серийный порт на ошибки загрузки Windows.

---

## 🆘 Альтернатива: Создать новую VM с готовым образом

Если текущая VM не запускается корректно:

```bash
# Удалить проблемную VM
gcloud compute instances delete "instance-20251013-145106" \
  --zone="us-east1-c" \
  --project="talkhint" \
  --quiet

# Создать новую с проверенным образом
gcloud compute instances create windows-dev-vm \
  --project="talkhint" \
  --zone="us-east1-c" \
  --machine-type="e2-standard-2" \
  --image-family="windows-2022" \
  --image-project="windows-cloud" \
  --boot-disk-size="50GB" \
  --boot-disk-type="pd-balanced" \
  --tags="rdp-server"
```

Затем подождать 10 минут и сбросить пароль.

