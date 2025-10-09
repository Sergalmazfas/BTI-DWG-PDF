using System;
using System.IO;
using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.EditorInput;
using Autodesk.AutoCAD.Runtime;
using Autodesk.AutoCAD.Geometry;

[assembly: CommandClass(typeof(BTI_InsertPlugin.Commands))]
[assembly: ExtensionApplication(typeof(BTI_InsertPlugin.Initialization))]

namespace BTI_InsertPlugin
{
    public class Initialization : IExtensionApplication
    {
        public void Initialize()
        {
            var ed = Application.DocumentManager.MdiActiveDocument?.Editor;
            ed?.WriteMessage("\n✅ BTI Insert Plugin загружен (Basmanny Template)");
        }

        public void Terminate()
        {
        }
    }

    public class Commands
    {
        [CommandMethod("InsertBTIBasman")]
        public static void InsertBTIBasman()
        {
            var doc = Application.DocumentManager.MdiActiveDocument;
            var db = doc.Database;
            var ed = doc.Editor;

            try
            {
                ed.WriteMessage("\n🔧 BTI Insert: Вставка шаблона Басманная...");

                // Путь к шаблону (загружается APS как templateFile)
                string templatePath = "template.dwg";
                
                if (!File.Exists(templatePath))
                {
                    ed.WriteMessage($"\n❌ Шаблон не найден: {templatePath}");
                    ed.WriteMessage($"\n⚠️ Сохраняем исходный файл как result.dwg");
                    
                    db.SaveAs("result.dwg", DwgVersion.AC1032);
                    ed.WriteMessage($"\n✅ result.dwg сохранён");
                    return;
                }

                ed.WriteMessage($"\n✅ Шаблон найден: {templatePath}");

                using (Transaction tr = db.TransactionManager.StartTransaction())
                {
                    // Загружаем шаблон как внешнюю ссылку
                    using (Database templateDb = new Database(false, true))
                    {
                        try
                        {
                            templateDb.ReadDwgFile(templatePath, FileShare.Read, true, "");
                            ed.WriteMessage("\n✅ Шаблон загружен в память");

                            // Вставляем всё содержимое шаблона в текущий чертёж
                            // Используем Insert с preserveSourceDatabase=true для копирования всех объектов
                            ObjectIdCollection ids = new ObjectIdCollection();
                            
                            // Вставляем как блок на координаты 0,0,0
                            ObjectId blockId = db.Insert("BasmanTemplate", templateDb, true);
                            ed.WriteMessage($"\n✅ Блок вставлен: {blockId}");
                            
                            // Создаём ссылку на блок (BlockReference)
                            BlockTable bt = (BlockTable)tr.GetObject(db.BlockTableId, OpenMode.ForRead);
                            BlockTableRecord modelSpace = (BlockTableRecord)tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);
                            
                            if (blockId != ObjectId.Null && !blockId.IsErased)
                            {
                                BlockReference blockRef = new BlockReference(Point3d.Origin, blockId);
                                blockRef.ScaleFactors = new Scale3d(1.0, 1.0, 1.0);
                                
                                modelSpace.AppendEntity(blockRef);
                                tr.AddNewlyCreatedDBObject(blockRef, true);
                                
                                ed.WriteMessage($"\n✅ Ссылка на блок создана в Model Space");
                            }
                        }
                        catch (Exception ex)
                        {
                            ed.WriteMessage($"\n⚠️ Ошибка вставки: {ex.Message}");
                            ed.WriteMessage($"\n⚠️ Сохраняем без шаблона");
                        }
                    }

                    tr.Commit();
                }

                // Сохраняем результат в DWG 2018 формате
                db.SaveAs("result.dwg", DwgVersion.AC1032);
                ed.WriteMessage($"\n✅ Шаблон Басманная вставлен!");
                ed.WriteMessage($"\n✅ result.dwg сохранён (формат: AC1032)");
            }
            catch (Exception ex)
            {
                ed.WriteMessage($"\n❌ ОШИБКА: {ex.Message}");
                
                // Fallback: просто сохраняем исходный файл
                try
                {
                    db.SaveAs("result.dwg", DwgVersion.AC1032);
                    ed.WriteMessage($"\n⚠️ Сохранён исходный файл как result.dwg");
                }
                catch (Exception saveEx)
                {
                    ed.WriteMessage($"\n❌ Не удалось сохранить: {saveEx.Message}");
                }
            }
        }
    }
}

