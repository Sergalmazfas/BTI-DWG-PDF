;;; BTI_APPLY.lsp
;;; Автоматическая вставка блоков БТИ по меткам
;;; 
;;; Использование:
;;; 1. Leica создает DWG с метками на слоях MARK_DOOR, MARK_WINDOW
;;; 2. Скрипт находит метки и вставляет блоки BTI_DOOR, BTI_WINDOW
;;; 3. Создает стандартные слои БТИ
;;;
;;; Автор: BTI Team
;;; Дата: 2025-10-14

(defun BTI-InsertFromLayer (markLayer blockName / ss i n e vla pmin pmax mid)
  "Находит объекты на слое markLayer и вставляет блок blockName в центре"
  (setq ss (ssget "_X" (list (cons 8 markLayer))))
  (if ss
    (progn
      (setq n (sslength ss) i 0)
      (princ (strcat "\n🔍 Найдено объектов на слое " markLayer ": " (itoa n)))
      (while (< i n)
        (setq e (ssname ss i)
              vla (vlax-ename->vla-object e))
        
        ;; Получаем границы объекта
        (vl-catch-all-apply 
          '(lambda ()
            (vlax-invoke-method vla 'GetBoundingBox 'pmin 'pmax)
            
            ;; Вычисляем центр
            (setq mid (mapcar '(lambda (a b) (/ (+ a b) 2.0))
                              (vlax-safearray->list (vlax-variant-value pmin))
                              (vlax-safearray->list (vlax-variant-value pmax))))
            
            ;; Вставляем блок
            (command "_.INSERT" blockName mid 1.0 1.0 0.0)
            (princ (strcat "\n✅ Вставлен " blockName " в точку " (vl-princ-to-string mid)))
          )
        )
        
        (setq i (1+ i))
      )
    )
    (princ (strcat "\n⚠️  Слой " markLayer " пуст или не найден"))
  )
  (princ)
)

(defun BTI-CreateStandardLayers ()
  "Создает стандартные слои БТИ"
  (princ "\n📋 Создание стандартных слоев БТИ...")
  
  ;; Слои и их цвета
  (setq layers 
    '(("A-WALL" 8 "Continuous")      ;; Стены - серый
      ("A-DOOR" 2 "Continuous")      ;; Двери - желтый
      ("A-WINDOW" 4 "Continuous")    ;; Окна - голубой
      ("A-PLUMBING" 3 "Continuous")  ;; Сантехника - зеленый
      ("A-DIM" 1 "Continuous")       ;; Размеры - красный
      ("A-TEXT" 7 "Continuous")      ;; Текст - белый
      ("MARK_DOOR" 5 "Continuous")   ;; Метки дверей - фиолетовый
      ("MARK_WINDOW" 5 "Continuous") ;; Метки окон - фиолетовый
    )
  )
  
  ;; Создаем каждый слой
  (foreach layer layers
    (command "_.LAYER" 
             "M" (nth 0 layer)           ;; Make layer
             "C" (nth 1 layer) (nth 0 layer)  ;; Color
             "L" (nth 2 layer) (nth 0 layer)  ;; Linetype
             ""                          ;; Exit
    )
    (princ (strcat "\n✅ Слой создан: " (nth 0 layer)))
  )
  
  (princ "\n✅ Все слои БТИ созданы")
  (princ)
)

(defun c:BTI_APPLY ()
  "Главная команда: применить стандарт БТИ к чертежу"
  (princ "\n")
  (princ "\n╔══════════════════════════════════════════════════════════════╗")
  (princ "\n║             🏛️  BTI Auto-Processor                          ║")
  (princ "\n╚══════════════════════════════════════════════════════════════╝")
  (princ "\n")
  
  ;; 1. Создать стандартные слои
  (BTI-CreateStandardLayers)
  
  ;; 2. Вставить двери по меткам
  (princ "\n")
  (princ "\n🚪 Обработка дверей...")
  (BTI-InsertFromLayer "MARK_DOOR" "BTI_DOOR")
  
  ;; 3. Вставить окна по меткам
  (princ "\n")
  (princ "\n🪟 Обработка окон...")
  (BTI-InsertFromLayer "MARK_WINDOW" "BTI_WINDOW")
  
  ;; 4. Финал
  (princ "\n")
  (princ "\n✅ Обработка БТИ завершена!")
  (princ "\n")
  (princ)
)

;; Автозапуск при загрузке скрипта
(princ "\n📜 BTI_APPLY.lsp загружен")
(princ "\n💡 Используйте команду: BTI_APPLY")
(princ)

