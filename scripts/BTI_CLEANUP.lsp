;;; BTI_CLEANUP.lsp
;;; Очистка временных слоев и объектов после обработки БТИ
;;;
;;; Использование:
;;; После BTI_APPLY выполнить BTI_CLEANUP для удаления служебных слоев
;;;
;;; Автор: BTI Team
;;; Дата: 2025-10-14

(defun BTI-DeleteLayer (layerName / )
  "Удаляет слой если он существует и не используется"
  (if (tblsearch "LAYER" layerName)
    (progn
      (vl-catch-all-apply 
        '(lambda ()
          (command "_.LAYER" "D" layerName "" "")
          (princ (strcat "\n✅ Удален слой: " layerName))
        )
      )
    )
    (princ (strcat "\n⚪ Слой не найден: " layerName))
  )
  (princ)
)

(defun BTI-PurgeAll ()
  "Очистка неиспользуемых блоков, слоев, стилей"
  (princ "\n🧹 Очистка неиспользуемых объектов...")
  
  ;; Многократная очистка (некоторые объекты удаляются только после второго прохода)
  (repeat 3
    (command "_.PURGE" "A" "*" "N")
  )
  
  (princ "\n✅ Очистка завершена")
  (princ)
)

(defun c:BTI_CLEANUP ()
  "Главная команда: очистка временных слоев после обработки БТИ"
  (princ "\n")
  (princ "\n╔══════════════════════════════════════════════════════════════╗")
  (princ "\n║             🧹 BTI Cleanup - Очистка                        ║")
  (princ "\n╚══════════════════════════════════════════════════════════════╝")
  (princ "\n")
  
  ;; 1. Удалить временные слои меток
  (princ "\n📋 Удаление служебных слоев...")
  (BTI-DeleteLayer "MARK_DOOR")
  (BTI-DeleteLayer "MARK_WINDOW")
  (BTI-DeleteLayer "MARK_PLUMBING")
  (BTI-DeleteLayer "TEMP")
  (BTI-DeleteLayer "CONSTRUCTION")
  
  ;; 2. Очистка неиспользуемых объектов
  (princ "\n")
  (BTI-PurgeAll)
  
  ;; 3. Финал
  (princ "\n")
  (princ "\n✅ Очистка БТИ завершена!")
  (princ "\n💡 Чертёж готов к печати")
  (princ "\n")
  (princ)
)

;; Автозапуск при загрузке скрипта
(princ "\n📜 BTI_CLEANUP.lsp загружен")
(princ "\n💡 Используйте команду: BTI_CLEANUP")
(princ)

