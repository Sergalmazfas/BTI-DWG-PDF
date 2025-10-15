;;; mark_blocks.lsp
;;; Создание POINT + TEXT меток вместо INSERT для совместимости с Forge
;;; Использование:
;;;   (load "mark_blocks.lsp")
;;;   MARK_BLOCKS
;;;
;;; Поддержка меток: двери, окна и произвольные типы по слою/цвету

(defun MB-EnsureMarkersLayer ()
  "Создает слой BTI_MARKERS, если он отсутствует"
  (command "_.-LAYER" "M" "BTI_MARKERS" "C" "2" "BTI_MARKERS" "")
  (princ))

(defun MB-PointWithText (pt label / textPt)
  "Создает POINT и подпись TEXT слева-сверху от точки"
  (setq textPt (list (+ (car pt) 100.0) (cadr pt)))
  (command "_.-POINT" pt)
  (command "_.-TEXT" "J" "L" textPt 150.0 0.0 label)
  (princ))

(defun MB-FromLayer (markLayer label / ss i n e vla pmin pmax mid)
  "Создает метки для всех объектов на слое markLayer"
  (MB-EnsureMarkersLayer)
  (setq ss (ssget "_X" (list (cons 8 markLayer))))
  (if ss
    (progn
      (setq n (sslength ss) i 0)
      (while (< i n)
        (setq e (ssname ss i)
              vla (vlax-ename->vla-object e))
        (vl-catch-all-apply
          '(lambda ()
             (vlax-invoke-method vla 'GetBoundingBox 'pmin 'pmax)
             (setq mid (mapcar '(lambda (a b) (/ (+ a b) 2.0))
                               (vlax-safearray->list (vlax-variant-value pmin))
                               (vlax-safearray->list (vlax-variant-value pmax))))
             (MB-PointWithText mid label)
           )
        )
        (setq i (1+ i))
      )
    )
  )
  (princ))

(defun MB-DoorsWindows ()
  "Создание меток дверей и окон по слоям MARK_DOOR / MARK_WINDOW"
  (MB-FromLayer "MARK_DOOR" "door_900_left")
  (MB-FromLayer "MARK_WINDOW" "window_1200")
  (princ))

(defun c:MARK_BLOCKS ()
  "Главная команда: создать POINT+TEXT метки для дверей и окон"
  (princ "\n🔖 Создание POINT+TEXT меток (MARK_BLOCKS)...")
  (MB-EnsureMarkersLayer)
  (MB-DoorsWindows)
  (princ "\n✅ MARK_BLOCKS завершено")
  (princ))

(princ "\n📜 mark_blocks.lsp загружен. Команда: MARK_BLOCKS")
