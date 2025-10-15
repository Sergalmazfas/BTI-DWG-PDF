;;; BTI_DIM_AREA.lsp
;;; Автоматическое нанесение размеров и площади помещения
;;; 
;;; Назначение:
;;; - Находит замкнутый контур помещения
;;; - Вычисляет площадь
;;; - Вставляет текст площади в центр помещения
;;; - Наносит размеры по периметру
;;;
;;; Использование: BTI_DIM_AREA
;;;
;;; Автор: BTI Team
;;; Дата: 2025-10-14

(defun BTI-GetPolylineArea (ent / vla area)
  "Вычисляет площадь замкнутой полилинии"
  (setq vla (vlax-ename->vla-object ent))
  (setq area (vla-get-Area vla))
  (/ area 1000000.0)  ;; Конвертируем в м² (из мм²)
)

(defun BTI-GetPolylineCenter (ent / pmin pmax mid)
  "Находит центр полилинии через BoundingBox"
  (setq vla (vlax-ename->vla-object ent))
  (vlax-invoke-method vla 'GetBoundingBox 'pmin 'pmax)
  
  (setq mid (mapcar '(lambda (a b) (/ (+ a b) 2.0))
                    (vlax-safearray->list (vlax-variant-value pmin))
                    (vlax-safearray->list (vlax-variant-value pmax))))
  mid
)

(defun BTI-DimPolyline (ent / pts i p1 p2)
  "Наносит размеры по всем сегментам полилинии"
  ;; Создаем слой для размеров
  (command "_.LAYER" "M" "A-DIM" "C" "1" "A-DIM" "")
  
  ;; Получаем количество вершин
  (setq numVert (vlax-curve-getEndParam ent))
  (setq i 0)
  
  (princ "\n   Нанесение размеров...")
  
  (while (< i numVert)
    (setq p1 (vlax-curve-getPointAtParam ent i))
    (setq p2 (vlax-curve-getPointAtParam ent (+ i 1)))
    
    ;; Вычисляем смещение для размера (100 мм от линии)
    (setq dx (- (car p2) (car p1))
          dy (- (cadr p2) (cadr p1)))
    
    ;; Определяем направление для смещения
    (if (> (abs dx) (abs dy))
      ;; Горизонтальная линия - смещение вверх
      (setq offset (list 0 100 0))
      ;; Вертикальная линия - смещение вправо
      (setq offset (list 100 0 0))
    )
    
    (command "_.DIMALIGNED" p1 p2 (mapcar '+ p1 offset))
    
    (setq i (1+ i))
  )
  
  (princ "\n   ✅ Размеры нанесены")
)

(defun c:BTI_DIM_AREA (/ ss ent area center areaText)
  "Главная команда: нанесение размеров и площади"
  (princ "\n")
  (princ "\n📏 Добавляем размеры и площадь помещения...")
  (princ "\n")
  
  ;; Находим замкнутый контур
  (setq ss (ssget "_X" '((0 . "LWPOLYLINE"))))
  
  (if ss
    (progn
      (setq ent (ssname ss 0))
      
      ;; Проверяем что контур замкнут
      (setq data (entget ent))
      (if (not (= 1 (logand 1 (cdr (assoc 70 data)))))
        (progn
          (princ "   ⚠️ Контур не замкнут! Сначала запустите BTI_ORTHO_ADJUST")
          (princ "\n")
          (princ)
          (exit)
        )
      )
      
      ;; Вычисляем площадь
      (setq area (BTI-GetPolylineArea ent))
      (princ (strcat "   Площадь помещения: " (rtos area 2 1) " м²"))
      
      ;; Находим центр
      (setq center (BTI-GetPolylineCenter ent))
      (princ (strcat "\n   Центр: " (vl-princ-to-string center)))
      
      ;; Создаем слой для текста
      (command "_.LAYER" "M" "A-TEXT" "C" "7" "A-TEXT" "")
      
      ;; Вставляем текст площади в центр
      (setq areaText (strcat (rtos area 2 1) " м²"))
      (command "_.-TEXT" "_J" "MC" center 250 "0" areaText)
      
      (princ "\n   ✅ Текст площади добавлен")
      (princ "\n")
      
      ;; Наносим размеры по периметру
      (BTI-DimPolyline ent)
      
      (princ "\n")
      (princ "\n✅ Размеры и площадь добавлены!")
      (princ "\n💡 Площадь: " (rtos area 2 1) " м²")
    )
    (princ "\n❌ Контур помещения (полилиния) не найден")
  )
  
  (princ "\n")
  (princ)
)

;; Автозапуск при загрузке
(princ "\n📜 BTI_DIM_AREA.lsp загружен")
(princ "\n💡 Команда: BTI_DIM_AREA")
(princ)

