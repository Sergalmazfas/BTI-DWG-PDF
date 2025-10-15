; === BTI_PROCESS.lsp ===
; Основная логика обработки DWG для БТИ
; Работает с 2D чертежами от Leica DISTO Plan

(defun BTI_PROCESS ( / tmpl ss ent)
  (princ "\n[BTI_PROCESS] Начало обработки DWG...")
  
  ;; Создаем основные слои БТИ
  (princ "\n[BTI_PROCESS] Создание слоев...")
  (command "_.-LAYER" "M" "BTI_WALLS" "C" "8" "" "")
  (command "_.-LAYER" "M" "BTI_MARKERS" "C" "2" "" "")
  (command "_.-LAYER" "M" "BTI_TEXT" "C" "7" "" "")
  (command "_.-LAYER" "M" "BTI_DIMENSIONS" "C" "3" "" "")
  (command "_.-LAYER" "M" "BTI_DOORS" "C" "4" "" "")
  (command "_.-LAYER" "M" "BTI_WINDOWS" "C" "6" "" "")
  
  ;; Ищем все полилинии (стены от Leica)
  (princ "\n[BTI_PROCESS] Поиск полилиний (стены)...")
  (setq ss (ssget "_X" '((0 . "LWPOLYLINE"))))
  
  (if ss
    (progn
      (princ (strcat "\n[BTI_PROCESS] Найдено полилиний: " (itoa (sslength ss))))
      
      ;; Переносим на слой BTI_WALLS
      (setq i 0)
      (repeat (sslength ss)
        (setq ent (ssname ss i))
        (command "_.-CHPROP" ent "" "LA" "BTI_WALLS" "")
        (setq i (1+ i))
      )
      (princ "\n[BTI_PROCESS] Полилинии перенесены на слой BTI_WALLS")
    )
    (princ "\n[BTI_PROCESS] ⚠️ Полилинии не найдены")
  )
  
  ;; Ищем точки (метки от Leica)
  (princ "\n[BTI_PROCESS] Поиск точек (метки)...")
  (setq ss (ssget "_X" '((0 . "POINT"))))
  
  (if ss
    (progn
      (princ (strcat "\n[BTI_PROCESS] Найдено точек: " (itoa (sslength ss))))
      
      ;; Обрабатываем каждую точку
      (setq i 0)
      (repeat (sslength ss)
        (setq ent (ssname ss i))
        (setq entdata (entget ent))
        (setq pt (cdr (assoc 10 entdata)))
        
        ;; Создаем текстовую метку рядом с точкой
        (BTI_MARKER_LABEL pt (strcat "M" (itoa (1+ i))))
        
        (setq i (1+ i))
      )
    )
    (princ "\n[BTI_PROCESS] ⚠️ Точки не найдены, создаем тестовые метки")
  )
  
  ;; Если точек нет, создаем несколько тестовых меток
  (if (not ss)
    (progn
      (BTI_MARKER_CREATE (list 1000.0 1500.0) "WINDOW_01")
      (BTI_MARKER_CREATE (list 2000.0 1500.0) "DOOR_01")
      (BTI_MARKER_CREATE (list 3000.0 1500.0) "MARKER_01")
    )
  )
  
  ;; Автоматический зум на все объекты
  (command "_ZOOM" "E")
  
  (princ "\n[BTI_PROCESS] ✅ Обработка завершена успешно")
  (princ)
)

;; Вспомогательная функция для создания текстовой метки
(defun BTI_MARKER_LABEL (pt label / textPt)
  (command "_.-LAYER" "S" "BTI_TEXT" "")
  (setq textPt (list (+ (car pt) 100.0) (cadr pt)))
  (command "_.-TEXT" "J" "L" textPt 120.0 0.0 label)
  (princ (strcat "\n[BTI_PROCESS] Создана метка: " label))
)

