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

(defun BTI-InsertDoorWindow (insertType pt / blockName layer textPt)
  "Создает POINT-метку для двери или окна в указанной точке"
  (cond
    ((= insertType "DOOR")
      (setq blockName "BTI_DOOR"
            layer "BTI_MARKERS"))
    ((= insertType "WINDOW")
      (setq blockName "BTI_WINDOW"
            layer "BTI_MARKERS"))
    (T
      (setq blockName nil))
  )
  
  (if blockName
    (progn
      ;; Создаем слой для меток если его нет
      (command "_.LAYER" "M" layer "C" "2" layer "")
      
      ;; Вычисляем точку для текста
      (setq textPt (list (+ (car pt) 100.0) (cadr pt)))
      
      ;; Создаем POINT вместо блока
      (command "_.-POINT" pt)
      
      ;; Добавляем текстовую метку
      (command "_.-TEXT" "J" "L" textPt 150.0 0.0 blockName)
      
      (princ (strcat "\n   ✅ POINT-метка " blockName " создана"))
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

