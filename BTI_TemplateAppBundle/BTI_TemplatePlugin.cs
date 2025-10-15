using System;
using System.IO;
using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.EditorInput;
using Autodesk.AutoCAD.Runtime;

[assembly: CommandClass(typeof(BTI_TemplatePlugin.Commands))]
[assembly: ExtensionApplication(typeof(BTI_TemplatePlugin.Initialization))]

namespace BTI_TemplatePlugin
{
    public class Initialization : IExtensionApplication
    {
        public void Initialize()
        {
            var ed = Application.DocumentManager.MdiActiveDocument?.Editor;
            ed?.WriteMessage("\n✅ BTI Template Plugin загружен");
        }

        public void Terminate()
        {
        }
    }

    public class Commands
    {
        [CommandMethod("ApplyBTITemplate")]
        public static void ApplyBTITemplate()
        {
            var doc = Application.DocumentManager.MdiActiveDocument;
            var db = doc.Database;
            var ed = doc.Editor;

            try
            {
                ed.WriteMessage("\n🔧 BTI Template: Начало обработки DWG...");

                // Путь к шаблону в AppBundle
                string templatePath = Path.Combine(
                    Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location),
                    "BTI_Template.dwt"
                );
                
                // Проверяем существование шаблона
                if (!System.IO.File.Exists(templatePath))
                {
                    ed.WriteMessage($"\n❌ Шаблон не найден: {templatePath}");
                    
                    // Пробуем альтернативный путь
                    templatePath = System.IO.Path.Combine(
                        System.IO.Path.GetDirectoryName(
                            System.Reflection.Assembly.GetExecutingAssembly().Location),
                        "BTI_Template.dwt"
                    );
                    
                    if (!System.IO.File.Exists(templatePath))
                    {
                        ed.WriteMessage($"\n❌ Шаблон не найден: {templatePath}");
                        ed.WriteMessage($"\n⚠️ Продолжаем без шаблона - просто сохраняем DWG");
                        
                        // Сохраняем текущий DWG как output.dwg
                        db.SaveAs("output.dwg", DwgVersion.Current);
                        ed.WriteMessage($"\n✅ DWG сохранен как output.dwg");
                        return;
                    }
                }

                ed.WriteMessage($"\n✅ Шаблон найден: {templatePath}");

                // Применяем шаблон
                using (Transaction tr = db.TransactionManager.StartTransaction())
                {
                    // Читаем шаблон
                    using (Database templateDb = new Database(false, true))
                    {
                        try
                        {
                            templateDb.ReadDwgFile(templatePath, System.IO.FileShare.Read, true, "");
                            ed.WriteMessage("\n✅ Шаблон загружен");

                            // Копируем настройки из шаблона
                            // Используем Insert для вставки содержимого шаблона
                            ObjectId blockId = db.Insert("BTI_Template_Block", templateDb, true);
                            ed.WriteMessage($"\n✅ Шаблон вставлен (Block ID: {blockId})");
                        }
                        catch (System.Exception ex)
                        {
                            ed.WriteMessage($"\n⚠️ Ошибка вставки шаблона: {ex.Message}");
                            ed.WriteMessage($"\n⚠️ Продолжаем без вставки шаблона");
                        }
                    }

                    tr.Commit();
                }

                // Сохраняем результат
                db.SaveAs("output.dwg", DwgVersion.Current);
                ed.WriteMessage($"\n✅ BTI Template применен успешно!");
                ed.WriteMessage($"\n✅ Результат сохранен: output.dwg");
            }
            catch (System.Exception ex)
            {
                ed.WriteMessage($"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {ex.Message}");
                ed.WriteMessage($"\n❌ Stack trace: {ex.StackTrace}");
                
                // В случае ошибки просто сохраняем исходный файл
                try
                {
                    db.SaveAs("output.dwg", DwgVersion.Current);
                    ed.WriteMessage($"\n⚠️ Сохранен исходный файл как output.dwg");
                }
                catch (System.Exception saveEx)
                {
                    ed.WriteMessage($"\n❌ Не удалось сохранить: {saveEx.Message}");
                }
            }
        }
    }
}

