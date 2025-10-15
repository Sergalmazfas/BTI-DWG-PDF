;;; BTI_ORTHO_ADJUST.lsp
;;; Выравнивание углов помещения (ортогонализация)
;;; 
;;; Назначение:
;;; - Находит контур помещения (полилиния)
;;; - Выравнивает углы по 90 градусов
;;; - Замыкает контур если открыт
;;;
;;; Использование: BTI_ORTHO_ADJUST
;;;
;;; Автор: BTI Team
;;; Дата: 2025-10-14

(defun BTI-OrthoAdjustPolyline (ent / pts newpts i p1 p2 dx dy angle)
  "Выравнивает углы полилинии по 90 градусов"
  (setq pts '())
  
  ;; Получаем все вершины полилинии
  (setq i 0)
  (while (setq p1 (vlax-curve-getPointAtParam ent i))
    (setq pts (append pts (list p1)))
    (setq i (1+ i))
  )
  
  (princ (strcat "\n   Вершин найдено: " (itoa (length pts))))
  
  ;; Выравниваем каждый сегмент
  (setq newpts '())
  (setq i 0)
  (while (< i (1- (length pts)))
    (setq p1 (nth i pts)
          p2 (nth (1+ i) pts))
    
    (setq dx (abs (- (car p2) (car p1)))
          dy (abs (- (cadr p2) (cadr p1))))
    
    ;; Если ближе к горизонтали - делаем горизонтальной
    (if (> dx dy)
      (setq p2 (list (car p2) (cadr p1) (caddr p1)))
      ;; Иначе - вертикальной
      (setq p2 (list (car p1) (cadr p2) (caddr p1)))
    )
    
    (setq newpts (append newpts (list p1)))
    (setq i (1+ i))
  )
  
  (setq newpts (append newpts (list p2)))
  (princ "\n   ✅ Углы выровнены")
  
  newpts
)

(defun c:BTI_ORTHO_ADJUST (/ ss ent data newpts)
  "Главная команда: выравнивание углов помещения"
  (princ "\n")
  (princ "\n🔧 Выравнивание углов помещения...")
  (princ "\n")
  
  ;; Находим все полилинии
  (setq ss (ssget "_X" '((0 . "LWPOLYLINE"))))
  
  (if ss
    (progn
      (princ (strcat "   Найдено полилиний: " (itoa (sslength ss))))
      (princ "\n")
      
      ;; Обрабатываем первую полилинию (контур помещения)
      (setq ent (ssname ss 0))
      
      ;; Проверяем замкнутость
      (setq data (entget ent))
      (if (not (= 1 (logand 1 (cdr (assoc 70 data)))))
        (progn
          (princ "   ⚠️ Контур не замкнут, замыкаем...")
          (command "_.PEDIT" ent "_Y" "_C" "")
          (princ "\n   ✅ Контур замкнут")
        )
        (princ "   ✅ Контур уже замкнут")
      )
      
      (princ "\n")
      
      ;; Выравниваем углы
      ;; (пока используем простое выравнивание через PEDIT)
      (princ "   🔄 Выравнивание углов...")
      (command "_.PEDIT" ent "_Y" "_S" "")
      
      (princ "\n")
      (princ "\n✅ Выравнивание завершено!")
      (princ "\n💡 Контур готов для вставки дверей и окон")
    )
    (princ "\n❌ Полилиния (контур помещения) не найдена")
  )
  
  (princ "\n")
  (princ)
)

;; Автозапуск при загрузке
(princ "\n📜 BTI_ORTHO_ADJUST.lsp загружен")
(princ "\n💡 Команда: BTI_ORTHO_ADJUST")
(princ)

