;;; BTI_APPLY_OBJECTS.lsp
;;; Вставка дверей и окон на основе меток или цветов
;;; 
;;; Назначение:
;;; - Находит метки дверей/окон (блоки или цветные объекты)
;;; - Вставляет типовые блоки БТИ (BTI_DOOR, BTI_WINDOW)
;;; - Размещает на правильных слоях
;;;
;;; Использование: BTI_APPLY_OBJECTS
;;;
;;; Автор: BTI Team
;;; Дата: 2025-10-14

(defun BTI-InsertDoorWindow (insertType pt / blockName layer)
  "Вставляет дверь или окно в указанную точку"
  (cond
    ((= insertType "DOOR")
      (setq blockName "BTI_DOOR"
            layer "A-DOOR"))
    ((= insertType "WINDOW")
      (setq blockName "BTI_WINDOW"
            layer "A-WINDOW"))
    (T
      (setq blockName nil))
  )
  
  (if blockName
    (progn
      (command "_.LAYER" "M" layer "")
      (command "_.-INSERT" blockName pt 1.0 1.0 0.0)
      (princ (strcat "\n   ✅ " blockName " вставлен"))
    )
  )
)

(defun BTI-FindAndReplace (searchName replaceName / ss i ent pt)
  "Находит блоки по имени и заменяет на типовые БТИ"
  (setq ss (ssget "_X" (list (cons 0 "INSERT") (cons 2 searchName))))
  (if ss
    (progn
      (princ (strcat "\n   Найдено " searchName ": " (itoa (sslength ss))))
      (setq i 0)
      (repeat (sslength ss)
        (setq ent (ssname ss i))
        (setq pt (cdr (assoc 10 (entget ent))))
        (command "_ERASE" ent "")
        (BTI-InsertDoorWindow replaceName pt)
        (setq i (1+ i))
      )
    )
    (princ (strcat "\n   ⚪ " searchName " не найдено"))
  )
)

(defun c:BTI_APPLY_OBJECTS ()
  "Главная команда: вставка дверей и окон"
  (princ "\n")
  (princ "\n🚪 Расстановка дверей и окон...")
  (princ "\n")
  
  ;; Находим и заменяем типовые метки
  (BTI-FindAndReplace "*Door*" "DOOR")
  (BTI-FindAndReplace "*DOOR*" "DOOR")
  (BTI-FindAndReplace "*door*" "DOOR")
  
  (BTI-FindAndReplace "*Window*" "WINDOW")
  (BTI-FindAndReplace "*WINDOW*" "WINDOW")
  (BTI-FindAndReplace "*window*" "WINDOW")
  
  (princ "\n")
  (princ "\n✅ Двери и окна установлены!")
  (princ "\n")
  (princ)
)

;; Автозапуск при загрузке
(princ "\n📜 BTI_APPLY_OBJECTS.lsp загружен")
(princ "\n💡 Команда: BTI_APPLY_OBJECTS")
(princ)

