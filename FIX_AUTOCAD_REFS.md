# 🔧 Исправление ссылок на AutoCAD для компиляции

## Проблема
```
The name 'Application' does not exist in the current context
```

Это означает, что компилятор не находит AutoCAD API библиотеки.

---

## ✅ Диагностика на Windows VM

### **Шаг 1: Проверить установку AutoCAD**

```powershell
# Поиск AutoCAD на диске
Get-ChildItem "C:\Program Files\Autodesk" -Directory

# Альтернативные пути
Get-ChildItem "C:\Program Files (x86)\Autodesk" -Directory -ErrorAction SilentlyContinue
```

### **Шаг 2: Найти DLL файлы AutoCAD**

```powershell
# Поиск acdbmgd.dll
Get-ChildItem "C:\Program Files\Autodesk" -Recurse -Filter "acdbmgd.dll" -ErrorAction SilentlyContinue | Select-Object FullName

# Поиск всех нужных DLL
$dlls = @("acdbmgd.dll", "acmgd.dll", "AcCoreMgd.dll")
foreach ($dll in $dlls) {
    Write-Host "`nПоиск $dll :" -ForegroundColor Cyan
    Get-ChildItem "C:\Program Files\Autodesk" -Recurse -Filter $dll -ErrorAction SilentlyContinue | 
        Select-Object FullName, @{Name="Size(KB)";Expression={[math]::Round($_.Length/1KB,2)}}
}
```

---

## 🔨 Решение

### **Вариант 1: Обновить пути в .csproj (если AutoCAD установлен)**

```powershell
# Скопировать правильный путь из вывода выше, например:
# C:\Program Files\Autodesk\AutoCAD 2024\acdbmgd.dll

# Открыть .csproj для редактирования
code C:\BTI-DWG-PDF\BTI_TemplateAppBundle\BTI_InsertBasman.csproj
```

**Обновить строки 15, 19, 23 на правильные пути:**

```xml
<Reference Include="acdbmgd">
  <HintPath>C:\Program Files\Autodesk\AutoCAD 2024\acdbmgd.dll</HintPath>
  <Private>False</Private>
</Reference>
<Reference Include="acmgd">
  <HintPath>C:\Program Files\Autodesk\AutoCAD 2024\acmgd.dll</HintPath>
  <Private>False</Private>
</Reference>
<Reference Include="AcCoreMgd">
  <HintPath>C:\Program Files\Autodesk\AutoCAD 2024\AcCoreMgd.dll</HintPath>
  <Private>False</Private>
</Reference>
```

---

### **Вариант 2: Если AutoCAD НЕ установлен - использовать NuGet пакет**

AutoCAD DLL недоступны через NuGet, поэтому нужно:

**A. Скачать DLL вручную:**

```powershell
# Создать директорию для библиотек
New-Item -Path "C:\BTI-DWG-PDF\lib" -ItemType Directory -Force

# Скачать из другой машины с AutoCAD или использовать ObjectARX SDK
# Нужные файлы:
# - acdbmgd.dll
# - acmgd.dll  
# - AcCoreMgd.dll
```

**B. Обновить .csproj на локальные DLL:**

```xml
<ItemGroup>
  <Reference Include="acdbmgd">
    <HintPath>..\lib\acdbmgd.dll</HintPath>
    <Private>False</Private>
  </Reference>
  <Reference Include="acmgd">
    <HintPath>..\lib\acmgd.dll</HintPath>
    <Private>False</Private>
  </Reference>
  <Reference Include="AcCoreMgd">
    <HintPath>..\lib\AcCoreMgd.dll</HintPath>
    <Private>False</Private>
  </Reference>
</ItemGroup>
```

---

### **Вариант 3: Упрощенный плагин БЕЗ AutoCAD API (для тестирования)**

Если нужно быстро протестировать компиляцию, создайте упрощенную версию:

```powershell
# Создать простой .csproj БЕЗ AutoCAD зависимостей
$simpleCsproj = @"
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Library</OutputType>
    <TargetFramework>net48</TargetFramework>
    <RootNamespace>BTI_InsertBasman</RootNamespace>
    <AssemblyName>BTI_InsertBasman</AssemblyName>
    <PlatformTarget>x64</PlatformTarget>
  </PropertyGroup>
</Project>
"@

Set-Content -Path "C:\BTI-DWG-PDF\BTI_TemplateAppBundle\BTI_InsertBasman_Simple.csproj" -Value $simpleCsproj

# Создать простой .cs файл
$simpleCs = @"
namespace BTI_InsertBasman
{
    public class SimplePlugin
    {
        public static string GetInfo()
        {
            return "BTI InsertBasman v1.0";
        }
    }
}
"@

Set-Content -Path "C:\BTI-DWG-PDF\BTI_TemplateAppBundle\Simple.cs" -Value $simpleCs

# Собрать
dotnet build C:\BTI-DWG-PDF\BTI_TemplateAppBundle\BTI_InsertBasman_Simple.csproj -c Release -o C:\out
```

---

### **Вариант 4: Использовать ГОТОВЫЙ Activity с LISP**

**Самое быстрое решение - использовать уже работающий Activity!**

```powershell
# НЕ НУЖНО компилировать .NET плагин!
# Используйте готовый Activity с LISP командами
```

**Activity уже существует:** `BotBti.BTI_INSERT_Basman+v1`

**Он использует LISP команды для вставки шаблона:**
```lisp
_INSERT
$(args[templateFile].path)
0,0,0
1
1
0
_SAVEAS
2018
result.dwg
_QUIT
```

**Включить в деплое:**
```bash
--set-env-vars="USE_BTI_TEMPLATE=true"
```

**Готово! Работает БЕЗ компиляции!**

---

## 🎯 Рекомендуемый путь

### **Для продакшена (СЕЙЧАС):**

✅ **Использовать `BotBti.BTI_INSERT_Basman+v1`**
- Работает через LISP
- Не требует компиляции
- Уже протестирован
- Шаблон из GCS

### **Для разработки (ПОТОМ):**

🔨 **Скомпилировать .NET плагин когда:**
1. Найдете машину с AutoCAD 2024/2025
2. Или получите AutoCAD DLL файлы
3. Или используете ObjectARX SDK

---

## 📋 Быстрая проверка на VM

```powershell
# 1. Есть ли AutoCAD?
Test-Path "C:\Program Files\Autodesk\AutoCAD 2025"

# 2. Есть ли DLL?
Test-Path "C:\Program Files\Autodesk\AutoCAD 2025\acdbmgd.dll"

# Если FALSE - AutoCAD не установлен, используйте Activity с LISP!
```

---

## ✅ Итог

**Если AutoCAD НЕ установлен на VM:**

👉 **Используйте готовый Activity:** `BotBti.BTI_INSERT_Basman+v1`  
👉 **Не нужна компиляция**  
👉 **Работает через `USE_BTI_TEMPLATE=true`**  
👉 **Деплой и готово!**

**Если AutoCAD установлен:**

👉 Найти DLL файлы (шаг 2)  
👉 Обновить пути в .csproj  
👉 Собрать проект  

---

**🚀 Самое простое решение: деплой с USE_BTI_TEMPLATE=true!**


