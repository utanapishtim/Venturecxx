(declare (usual-integrations))

;; TODO First writing a version that just forward simulates to make
;; sure the rest works.
(define-structure (rdb (safe-accessors #t))
  parent
  addresses
  records
  constraints
  record-hook)

(define (rdb-trace-search trace addr win lose)
  (if (rdb? trace)
      (rdb-trace-search-one trace addr win
       (lambda () (trace-search (rdb-parent trace) addr win lose)))
      (lose)))

(define (rdb-trace-search-one-record trace addr win lose)
  (search-parallel-lists
   addr (rdb-addresses trace) (rdb-records trace) win lose))

(define (rdb-trace-search-one trace addr win lose)
  (rdb-trace-search-one-record trace addr (lambda (rec) (win (car (cddddr rec)))) lose))

(define (rdb-trace-store! trace addr thing)
  (set-rdb-addresses! trace (cons addr (rdb-addresses trace)))
  (set-rdb-records! trace (cons thing (rdb-records trace))))

(define (rdb-record! trace exp env addr read-traces answer)
  (let ((real-answer
         (aif (rdb-record-hook trace)
              (it exp env addr read-traces answer)
              answer)))
    (rdb-trace-store! trace addr (list exp env addr read-traces real-answer))
    real-answer))

(define (rdb-record-constraint! trace addr value)
  (set-rdb-constraints! trace (cons (cons addr value) (rdb-constraints trace))))

(define (rdb-extend trace)
  (make-rdb trace '() '() '() #f))

(define (rdb-empty) (rdb-extend #f))

;;; Translation of the Lightweight MCMC algorithm to the present context

(define (weight-at addr trace read-traces)
  (rdb-trace-search-one-record trace addr
   (lambda (rec)
     (weight-for-at (car (cddddr rec)) addr (car rec) trace read-traces))
   (lambda () (error "Trying to compute weight for a value that isn't there" addr))))

(define (weight-for-at val addr exp trace read-traces)
  ;; Expect exp for be an application
  ;; Do not look for it in the trace itself because it may not have been recorded yet.
  (let ((sub-vals (map (lambda (i)
                         (traces-lookup (cons trace read-traces) (extend-address addr `(app-sub ,i))))
                       (iota (length exp)))))
    (if (not (primitive? (car sub-vals)))
        (error "What!?"))
    (if (not (primitive-log-density (car sub-vals)))
        (error "What?!?"))
    ((access apply system-global-environment)
     (primitive-log-density (car sub-vals)) val (cdr sub-vals))))

(define (compatible-operators-for? addr new-trace old-trace)
  (let ((op-addr (extend-address addr '(app-sub 0))))
    (rdb-trace-search-one
     new-trace op-addr
     (lambda (new-op)
       (rdb-trace-search-one
        old-trace op-addr
        (lambda (old-op)
          (and (eqv? new-op old-op)
               (primitive? new-op)
               (primitive-log-density new-op)))
        (lambda () #f)))
     (lambda () #f))))

(define (rebuild-rdb orig replacements)
  (let ((new (rdb-extend (rdb-parent orig)))
        (log-weight 0))
    (define (add-weight w)
      (pp w)
      (set! log-weight (+ log-weight w)))
    (define (regeneration-hook exp env addr read-traces answer)
      (define new-value)
      (define (record-as-resampled)
        (set! new-value answer)) ; No weight
      (define (record-as-absorbed val)
        (set! new-value val)
        ;; TODO Could optimize this not to recompute weights if the
        ;; parameters did not change.
        (add-weight (- (weight-for-at new-value addr exp new read-traces)
                       (weight-at addr orig read-traces))))
      ;; Assume that replacements are added judiciously, namely to
      ;; random choices from the original trace (whose operators
      ;; didn't change due to other replacements?)
      (aif (assq addr replacements)
           (if (random-choice? addr new)
               (record-as-absorbed (cdr it))
               (error "Trying to replace the value of a deterministic computation"))
           (if (compatible-operators-for? addr new orig)
               ;; One?  Should be one...
               (rdb-trace-search-one orig addr record-as-absorbed record-as-resampled)
               (record-as-resampled)))
      ;; TODO I believe the fresh and stale log likelihoods
      ;; mentioned in Wingate, Stuhlmuller, Goodman 2008 are
      ;; actually a distraction, in that they always cancel against
      ;; the log likelihood of newly sampled randomness.
      new-value)
    (set-rdb-record-hook! new regeneration-hook)
    (for-each
     (lambda (addr record)
       ;; Order (not counting issues with coupled primitives) will be
       ;; enforced by evaluation recursion regardless of the order in
       ;; which the available expressions are traversed, provided the
       ;; replacement caches results.
       ;; However, I do need to order things so that defines get executed
       ;; before lookups of those symbols.
       ;; TODO: Mutation problem: define changes the evaluation environment!
       (case* record
         ((pair exp (pair env (pair addr (pair read-traces (pair answer null)))))
          (eval exp env new addr read-traces))))
     ;; Walking over exactly the expressions already recorded is the
     ;; right thing, because it will not attempt to rerun the extend
     ;; node that contains the executing inference program itself.
     (reverse (rdb-addresses orig))
     (reverse (rdb-records orig)))
    (values new log-weight)))

(define (random-choice? addr trace)
  ;; TODO Ignores possibility of constraints induced by observations.
  (rdb-trace-search-one
   trace (extend-address addr '(app-sub 0))
   (lambda (op)
     (and (primitive? op)
          (primitive-log-density op)))
   (lambda () #f)))

(define (unconstrained-random-choice? addr trace)
  (and (random-choice? addr trace)
       (not (assq addr (rdb-constraints trace)))))

(define (random-choices trace)
  (filter (lambda (a) (unconstrained-random-choice? a trace)) (rdb-addresses trace)))

(define (select-uniformly items)
  (let ((index (random (length items))))
    (list-ref items index)))

(define (prior-resimulate-exp addr exp trace)
  (let ((sub-vals (map (lambda (i)
                         (traces-lookup (list trace) (extend-address addr `(app-sub ,i))))
                       (iota (length exp)))))
    (if (not (primitive? (car sub-vals)))
        (error "What!?"))
    ((access apply system-global-environment)
     (primitive-simulate (car sub-vals)) (cdr sub-vals))))

(define (prior-resimulate addr trace)
  (rdb-trace-search-one-record
   trace addr
   (lambda (rec)
     (prior-resimulate-exp addr (car rec) trace))
   (lambda () (error "What?"))))

(define (enforce-constraints trace)
  (pp 'enforcing)
  (receive (new-trace weight) (rebuild-rdb trace (rdb-constraints trace))
     (rdb-trace-commit! new-trace trace)))

(define (mcmc-step trace)
  (let* ((target-addr (select-uniformly (random-choices trace)))
         (proposed-value (prior-resimulate target-addr trace))
         (replacements (cons `(,target-addr . ,proposed-value) (rdb-constraints trace))))
    (pp `(proposing ,target-addr ,proposed-value))
    (receive (new-trace weight) (rebuild-rdb trace replacements)
      (let ((correction (- (log (length (random-choices trace)))
                           (log (length (random-choices new-trace))))))
        (if (< (log (random 1.0)) (+ weight correction))
            (begin
              (pp 'accept)
              (rdb-trace-commit! new-trace trace))
            (pp 'reject))))))

(define (rdb-trace-commit! from to)
  (set-rdb-addresses! to (rdb-addresses from))
  (set-rdb-records! to (rdb-records from)))

(define inference-smoke-test-defn
  `(begin
     (define model-trace (rdb-extend (get-current-trace)))
     (trace-in model-trace
               (begin
                 (define x (flip))
                 x))
     (pp (trace-in (store-extend model-trace) x))
     (mcmc-step model-trace)
     (trace-in (store-extend model-trace) x)))

;; We can flip different choices

(define inference-smoke-test-2-defn
  `(begin
     (define model-trace (rdb-extend (get-current-trace)))
     (trace-in model-trace
               (begin (define x1 (flip))
                      (define x2 (flip))))
     ,map-defn
     (map (lambda (i)
            (begin
              (pp (trace-in (store-extend model-trace) (list x1 x2)))
              (mcmc-step model-trace)))
          '(1 2 3 4))
     (trace-in (store-extend model-trace) (list x1 x2))))

;; Trick coin

(define trick-coin-example
  `(begin
     ,infer-defn
     ,observe-defn
     (define model-trace (rdb-extend (get-current-trace)))
     (trace-in model-trace
               (begin
                 (define is-trick? (flip 0.5))
                 (define weight (if is-trick? (uniform 0 1) 0.5))
                 ($observe (flip weight) #t)
                 ($observe (flip weight) #t)
                 ($observe (flip weight) #t)
                 ($observe (flip weight) #t)
                 ($observe (flip weight) #t)
                 (define answer (list is-trick? weight))))
     (pp (trace-in (store-extend model-trace) answer))
     ,map-defn
     (enforce-constraints model-trace)
     (map (lambda (i) (mcmc-step model-trace))
          '(1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20))
     (trace-in (store-extend model-trace) answer)))

;;; On observations: VKM argues that requiring observe to accept only
;;; a constant (!) (wrt current trace) procedure that has a density as
;;; the top expression is fine, for deep philosophical reasons.  The
;;; extra flexibility afforded by nesting and inference programming
;;; may go a long way to alleviating the trouble that causes.

;;; Hm.  The way I wrote this program, it never actually garbage
;;; collects old addresses from the trace, which has the two funny
;;; effects that
;;; a) Old choices stick around and may come back
;;; b) Proposals to shadow choices are made (and always accepted
;;;    because there is no likelihood)

(define trick-coin-example-syntax
  `(begin
     ,observe-defn
     ,map-defn
     (define mcmc-20
       (lambda (t)
         (begin
           (enforce-constraints t)
           (map (lambda (i) (mcmc-step t))
                '(1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20)))))
     (model-in (rdb-extend (get-current-trace))
       (assume is-trick? (flip 0.5))
       (assume weight (if is-trick? (uniform 0 1) 0.5))
       (observe (flip weight) #t)
       (observe (flip weight) #t)
       (observe (flip weight) #t)
       (observe (flip weight) #t)
       (observe (flip weight) #t)
       (infer mcmc-20)
       (predict (list is-trick? weight)))))
