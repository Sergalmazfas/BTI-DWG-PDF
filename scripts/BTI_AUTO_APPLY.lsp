;;; BTI_AUTO_APPLY.lsp
;;; Автоматическое применение БТИ обработки
;;; Выполняется сразу при загрузке файла
;;;
;;; Назначение:
;;; - Находит слои MARK_DOOR и MARK_WINDOW
;;; - Вставляет блоки BTI_DOOR и BTI_WINDOW
;;; - Автоматически сохраняет результат
;;;
;;; Автор: BTI Team
;;; Дата: 2025-10-14

(defun BTI-InsertFromLayer (markLayer blockName / ss i n e vla pmin pmax mid textPt)
  "Создает POINT-метки на основе объектов на заданном слое"
  (setq ss (ssget "X" (list (cons 8 markLayer))))
  (if ss
    (progn
      (setq n (sslength ss) i 0)
      (princ (strcat "\n   Найдено объектов на слое " markLayer ": " (itoa n)))
      
      ;; Создаем слой для меток если его нет
      (command "_.-LAYER" "M" "BTI_MARKERS" "C" "2" "BTI_MARKERS" "")
      
      (while (< i n)
        (setq e (ssname ss i)
              vla (vlax-ename->vla-object e))
        
        ;; Получаем центр объекта через BoundingBox
        (vlax-invoke-method vla 'GetBoundingBox 'pmin 'pmax)
        (setq mid (mapcar '(lambda (a b) (/ (+ a b) 2.0))
                          (vlax-safearray->list (vlax-variant-value pmin))
                          (vlax-safearray->list (vlax-variant-value pmax))))
        
        ;; Вычисляем точку для текста (смещение вправо на 100 единиц)
        (setq textPt (list (+ (car mid) 100.0) (cadr mid)))
        
        ;; Вставляем POINT вместо блока
        (command "_.-POINT" mid)
        
        ;; Добавляем текстовую метку
        (command "_.-TEXT" "J" "L" textPt 150.0 0.0 blockName)
        
        (princ (strcat "\n   ✓ POINT-метка " blockName " создана"))
        
        (setq i (1+ i))
      )
      (princ (strcat "\n   ✅ Обработано объектов: " (itoa n)))
    )
    (princ (strcat "\n   ℹ️  Слой " markLayer " не найден или пуст"))
  )
)

(defun BTI-AUTO-PROCESS ()
  "Автоматическая обработка BTI"
  (princ "\n")
  (princ "\n╔════════════════════════════════════════╗")
  (princ "\n║   🏛️  BTI АВТОМАТИЧЕСКАЯ ОБРАБОТКА    ║")
  (princ "\n╚════════════════════════════════════════╝")
  (princ "\n")
  
  ;; Создаем стандартные слои BTI если их нет
  (princ "\n1️⃣  Создание слоев БТИ...")
  (command "_.-LAYER" "M" "A-DOOR" "C" "2" "A-DOOR" "")
  (command "_.-LAYER" "M" "A-WINDOW" "C" "4" "A-WINDOW" "")
  (princ "\n   ✅ Слои созданы")
  
  ;; Обрабатываем двери
  (princ "\n")
  (princ "\n2️⃣  Обработка дверей (MARK_DOOR → BTI_DOOR)...")
  (BTI-InsertFromLayer "MARK_DOOR" "BTI_DOOR")
  
  ;; Обрабатываем окна
  (princ "\n")
  (princ "\n3️⃣  Обработка окон (MARK_WINDOW → BTI_WINDOW)...")
  (BTI-InsertFromLayer "MARK_WINDOW" "BTI_WINDOW")
  
  ;; Сохраняем
  (princ "\n")
  (princ "\n4️⃣  Сохранение результата...")
  (command "_QSAVE")
  (princ "\n   ✅ Файл сохранен")
  
  (princ "\n")
  (princ "\n╔════════════════════════════════════════╗")
  (princ "\n║        ✅ ОБРАБОТКА ЗАВЕРШЕНА!        ║")
  (princ "\n╚════════════════════════════════════════╝")
  (princ "\n")
  (princ)
)

;; АВТОЗАПУСК при загрузке файла
(princ "\n")
(princ "\n🚀 BTI_AUTO_APPLY.lsp загружен, запуск обработки...")
(BTI-AUTO-PROCESS)

