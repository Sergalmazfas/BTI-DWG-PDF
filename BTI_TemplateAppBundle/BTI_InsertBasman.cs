using System;
using System.IO;
using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.EditorInput;
using Autodesk.AutoCAD.Runtime;
using Autodesk.AutoCAD.Geometry;

[assembly: CommandClass(typeof(BTI_InsertBasman.Commands))]
[assembly: ExtensionApplication(typeof(BTI_InsertBasman.Initialization))]

namespace BTI_InsertBasman
{
    public class Initialization : IExtensionApplication
    {
        public void Initialize()
        {
            var ed = Application.DocumentManager.MdiActiveDocument?.Editor;
            ed?.WriteMessage("\n✅ BTI Insert Basmann Plugin v1.0 загружен");
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
            Document doc = Application.DocumentManager.MdiActiveDocument;
            Database db = doc.Database;
            Editor ed = doc.Editor;

            try
            {
                ed.WriteMessage("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
                ed.WriteMessage("\n🔧 BTI INSERT BASMANN PLUGIN - START");
                ed.WriteMessage("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");

                // Путь к template.dwg (загружается APS автоматически)
                string templatePath = "template.dwg";
                
                if (!File.Exists(templatePath))
                {
                    ed.WriteMessage($"\n❌ Template не найден: {templatePath}");
                    ed.WriteMessage($"\n⚠️ Сохраняем исходный файл без изменений");
                    
                    db.SaveAs("result.dwg", DwgVersion.AC1032);
                    ed.WriteMessage($"\n✅ result.dwg сохранён (без шаблона)");
                    return;
                }

                ed.WriteMessage($"\n✅ Template найден: {templatePath} ({new FileInfo(templatePath).Length} bytes)");

                using (Transaction tr = db.TransactionManager.StartTransaction())
                {
                    try
                    {
                        // Загружаем шаблон в отдельную базу данных
                        using (Database templateDb = new Database(false, true))
                        {
                            ed.WriteMessage($"\n📖 Загружаем template.dwg...");
                            templateDb.ReadDwgFile(templatePath, FileShare.Read, true, "");
                            ed.WriteMessage($"\n✅ Template загружен в память");

                            // Вставляем шаблон как блок
                            ed.WriteMessage($"\n🔨 Вставка блока BasmanTemplate...");
                            
                            // Insert возвращает ObjectId блока в текущей БД
                            ObjectId blockId = db.Insert("BasmanTemplate", templateDb, true);
                            
                            if (blockId.IsNull || blockId.IsErased)
                            {
                                ed.WriteMessage($"\n❌ Не удалось создать блок");
                                throw new Exception("Block Insert failed");
                            }
                            
                            ed.WriteMessage($"\n✅ Блок создан: {blockId}");
                            
                            // Создаём ссылку на блок (BlockReference) в Model Space
                            BlockTable bt = (BlockTable)tr.GetObject(db.BlockTableId, OpenMode.ForRead);
                            BlockTableRecord modelSpace = (BlockTableRecord)tr.GetObject(
                                bt[BlockTableRecord.ModelSpace], 
                                OpenMode.ForWrite
                            );
                            
                            // Вставляем блок в начало координат
                            BlockReference blockRef = new BlockReference(Point3d.Origin, blockId);
                            blockRef.ScaleFactors = new Scale3d(1.0, 1.0, 1.0);
                            blockRef.Rotation = 0;
                            
                            modelSpace.AppendEntity(blockRef);
                            tr.AddNewlyCreatedDBObject(blockRef, true);
                            
                            ed.WriteMessage($"\n✅ BlockReference добавлен в Model Space");
                            ed.WriteMessage($"\n   Координаты: 0,0,0");
                            ed.WriteMessage($"\n   Масштаб: 1:1:1");
                        }

                        tr.Commit();
                        ed.WriteMessage($"\n✅ Transaction committed");
                    }
                    catch (Exception ex)
                    {
                        ed.WriteMessage($"\n❌ Ошибка при вставке: {ex.Message}");
                        tr.Abort();
                        throw;
                    }
                }

                // Сохраняем результат в формате DWG 2018 (AC1032)
                ed.WriteMessage($"\n💾 Сохранение result.dwg...");
                db.SaveAs("result.dwg", DwgVersion.AC1032);
                
                ed.WriteMessage("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
                ed.WriteMessage("\n🎉 УСПЕХ! ШАБЛОН БАСМАННАЯ ВСТАВЛЕН!");
                ed.WriteMessage($"\n📁 result.dwg создан (формат: AC1032)");
                ed.WriteMessage("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
            }
            catch (Exception ex)
            {
                ed.WriteMessage("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
                ed.WriteMessage($"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {ex.Message}");
                ed.WriteMessage($"\n📋 Stack trace:");
                ed.WriteMessage($"\n{ex.StackTrace}");
                
                // Fallback: сохраняем исходный файл
                try
                {
                    ed.WriteMessage($"\n⚠️ Fallback: сохранение исходного файла");
                    db.SaveAs("result.dwg", DwgVersion.AC1032);
                    ed.WriteMessage($"\n✅ result.dwg сохранён (исходный файл без изменений)");
                }
                catch (Exception saveEx)
                {
                    ed.WriteMessage($"\n❌ Не удалось сохранить: {saveEx.Message}");
                    // Последняя попытка - WBLOCK
                    try
                    {
                        ed.Command("._WBLOCK", "result.dwg", "*", "0,0,0");
                        ed.WriteMessage($"\n✅ result.dwg создан через WBLOCK");
                    }
                    catch
                    {
                        ed.WriteMessage($"\n❌ Все попытки сохранения провалились");
                    }
                }
                
                ed.WriteMessage("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
            }
        }
    }
}

