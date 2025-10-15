;;; BTI_APPLY_COLOR.lsp
;;; Автоматическая вставка блоков БТИ по ЦВЕТАМ объектов
;;; 
;;; Leica DISTO размечает объекты цветами:
;;; - Синий (5) = окно
;;; - Оранжевый (30) = дверь
;;; - Зеленый (3) = унитаз
;;; - Красный (1) = раковина
;;;
;;; Forge AutoCAD Core распознает цвета и вставляет типовые блоки БТИ
;;;
;;; Автор: BTI Team
;;; Дата: 2025-10-14
;;; Версия: 2.0 (Color-based)

(defun BTI-InsertByColor (/ ss i n e vla color pmin pmax mid blockName inserted textPt)
  "Находит объекты по цветам и создает POINT-метки"
  (setq ss (ssget "_X"))
  (setq inserted 0)
  
  ;; Создаем слой для меток
  (command "_.-LAYER" "M" "BTI_MARKERS" "C" "2" "BTI_MARKERS" "")
  
  (if ss
    (progn
      (setq n (sslength ss) i 0)
      (princ (strcat "\n🔍 Обработка объектов: " (itoa n)))
      
      (while (< i n)
        (setq e (ssname ss i)
              vla (vlax-ename->vla-object e))
        
        (vl-catch-all-apply
          '(lambda ()
            ;; Получаем цвет объекта
            (setq color (vla-get-Color vla))
            
            ;; Получаем границы объекта для вычисления центра
            (vlax-invoke-method vla 'GetBoundingBox 'pmin 'pmax)
            
            ;; Вычисляем центральную точку
            (setq mid (mapcar '(lambda (a b) (/ (+ a b) 2.0))
                              (vlax-safearray->list (vlax-variant-value pmin))
                              (vlax-safearray->list (vlax-variant-value pmax))))
            
            ;; Определяем метку по цвету
            (setq blockName nil)
            (cond
              ((= color 5)  (setq blockName "BTI_WINDOW"))   ;; 🟦 Синий - окно
              ((= color 30) (setq blockName "BTI_DOOR"))     ;; 🟧 Оранжевый - дверь
              ((= color 3)  (setq blockName "BTI_TOILET"))   ;; 🟩 Зеленый - унитаз
              ((= color 1)  (setq blockName "BTI_SINK"))     ;; 🟥 Красный - раковина
              ((= color 6)  (setq blockName "BTI_SHOWER"))   ;; 🟪 Фиолетовый - душ
            )
            
            ;; Создаем POINT + TEXT метку если определена
            (if blockName
              (progn
                ;; Вычисляем точку для текста
                (setq textPt (list (+ (car mid) 100.0) (cadr mid)))
                
                ;; Создаем POINT
                (command "_.-POINT" mid)
                
                ;; Добавляем текстовую метку
                (command "_.-TEXT" "J" "L" textPt 150.0 0.0 blockName)
                
                (setq inserted (1+ inserted))
                (princ (strcat "\n  ✅ Цвет " (itoa color) " → POINT " blockName))
              )
            )
          )
        )
        
        (setq i (1+ i))
      )
      
      (princ (strcat "\n\n📊 Всего создано POINT-меток: " (itoa inserted)))
    )
    (princ "\n⚠️  Объекты не найдены")
  )
  (princ)
)

(defun BTI-CreateStandardLayers ()
  "Создает стандартные слои БТИ"
  (princ "\n📋 Создание стандартных слоев БТИ...")
  
  (setq layers 
    '(("A-WALL" 8 "Continuous")        ;; Стены - серый
      ("A-DOOR" 2 "Continuous")        ;; Двери - желтый
      ("A-WINDOW" 4 "Continuous")      ;; Окна - голубой
      ("A-PLUMBING" 3 "Continuous")    ;; Сантехника - зеленый
      ("A-DIM" 1 "Continuous")         ;; Размеры - красный
      ("A-TEXT" 7 "Continuous")        ;; Текст - белый
    )
  )
  
  (foreach layer layers
    (command "_.LAYER" 
             "M" (nth 0 layer)
             "C" (nth 1 layer) (nth 0 layer)
             "L" (nth 2 layer) (nth 0 layer)
             ""
    )
  )
  
  (princ "\n✅ Слои БТИ созданы")
  (princ)
)

(defun BTI-MoveToLayers ()
  "Перемещает вставленные блоки на правильные слои БТИ"
  (princ "\n📐 Перемещение блоков на слои БТИ...")
  
  ;; Окна на A-WINDOW
  (command "_.QSELECT" "" "Block Name" "=" "BTI_WINDOW" "")
  (command "_.CHPROP" "P" "" "LA" "A-WINDOW" "")
  
  ;; Двери на A-DOOR
  (command "_.QSELECT" "" "Block Name" "=" "BTI_DOOR" "")
  (command "_.CHPROP" "P" "" "LA" "A-DOOR" "")
  
  ;; Сантехника на A-PLUMBING
  (command "_.QSELECT" "" "Block Name" "=" "BTI_TOILET" "")
  (command "_.CHPROP" "P" "" "LA" "A-PLUMBING" "")
  
  (command "_.QSELECT" "" "Block Name" "=" "BTI_SINK" "")
  (command "_.CHPROP" "P" "" "LA" "A-PLUMBING" "")
  
  (princ "\n✅ Блоки перемещены на слои БТИ")
  (princ)
)

(defun c:BTI_APPLY_COLOR ()
  "Главная команда: обработка DWG по цветам объектов от Leica"
  (princ "\n")
  (princ "\n╔══════════════════════════════════════════════════════════════╗")
  (princ "\n║       🎨 BTI Auto-Processor (Color-based Recognition)       ║")
  (princ "\n╚══════════════════════════════════════════════════════════════╝")
  (princ "\n")
  (princ "\n🎨 Цветовая схема Leica:")
  (princ "\n   🟦 Синий (5)      → Окна (BTI_WINDOW)")
  (princ "\n   🟧 Оранжевый (30) → Двери (BTI_DOOR)")
  (princ "\n   🟩 Зеленый (3)    → Унитаз (BTI_TOILET)")
  (princ "\n   🟥 Красный (1)    → Раковина (BTI_SINK)")
  (princ "\n")
  
  ;; 1. Создать стандартные слои БТИ
  (BTI-CreateStandardLayers)
  
  ;; 2. Вставить блоки по цветам
  (princ "\n")
  (princ "\n🔄 Распознавание объектов по цветам...")
  (BTI-InsertByColor)
  
  ;; 3. Переместить блоки на правильные слои
  (princ "\n")
  (BTI-MoveToLayers)
  
  ;; 4. Финал
  (princ "\n")
  (princ "\n✅ Обработка БТИ завершена!")
  (princ "\n💡 Блоки вставлены по цветам от Leica DISTO")
  (princ "\n")
  (princ)
)

;; Автозапуск при загрузке
(princ "\n📜 BTI_APPLY_COLOR.lsp загружен")
(princ "\n💡 Команда: BTI_APPLY_COLOR")
(princ)

