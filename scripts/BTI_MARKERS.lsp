; === BTI_MARKERS.lsp ===
; Библиотека для создания меток POINT + TEXT в формате БТИ
; Используется для обозначения дверей, окон и других объектов

(defun BTI_MARKER_CREATE (pt label / textPt)
  "Создает метку: POINT + TEXT"
  
  ;; Переключаемся на слой маркеров
  (command "_.-LAYER" "S" "BTI_MARKERS" "")
  
  ;; Создаем точку
  (command "_.-POINT" pt)
  
  ;; Создаем текст справа от точки
  (setq textPt (list (+ (car pt) 200.0) (cadr pt)))
  (command "_.-TEXT" "J" "L" textPt 150.0 0.0 label)
  
  (princ (strcat "\n[BTI_MARKERS] Создан маркер: " label " в точке " (vl-prin1-to-string pt)))
  (princ)
)

(defun BTI_MARKER_DOOR (pt label / )
  "Создает метку двери"
  (command "_.-LAYER" "S" "BTI_DOORS" "")
  (command "_.-POINT" pt)
  
  (setq textPt (list (+ (car pt) 200.0) (cadr pt)))
  (command "_.-TEXT" "J" "L" textPt 150.0 0.0 (strcat "DOOR_" label))
  
  (princ (strcat "\n[BTI_MARKERS] Создана дверь: " label))
  (princ)
)

(defun BTI_MARKER_WINDOW (pt label / )
  "Создает метку окна"
  (command "_.-LAYER" "S" "BTI_WINDOWS" "")
  (command "_.-POINT" pt)
  
  (setq textPt (list (+ (car pt) 200.0) (cadr pt)))
  (command "_.-TEXT" "J" "L" textPt 150.0 0.0 (strcat "WIN_" label))
  
  (princ (strcat "\n[BTI_MARKERS] Создано окно: " label))
  (princ)
)

(defun BTI_MARKER_BATCH (pt-list prefix / i pt)
  "Создает несколько меток из списка точек"
  (setq i 1)
  (foreach pt pt-list
    (BTI_MARKER_CREATE pt (strcat prefix (itoa i)))
    (setq i (1+ i))
  )
  (princ (strcat "\n[BTI_MARKERS] Создано меток: " (itoa (length pt-list))))
  (princ)
)

(princ "\n[BTI_MARKERS] Библиотека загружена: BTI_MARKER_CREATE, BTI_MARKER_DOOR, BTI_MARKER_WINDOW, BTI_MARKER_BATCH")
(princ)

