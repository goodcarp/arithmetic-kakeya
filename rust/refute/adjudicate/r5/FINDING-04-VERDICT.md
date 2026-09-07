# Adjudication r5, finding 4/10 (lens: science) — VERDICT: REAL (severity overstated)

Artifacts as tested (2026-09-06):
- rust/target/release/kakeya-search sha256 add554183aaa3d7cf1f2d468ba11e39926aea035853809811af4e6c40010fcf9 (matches the brief)
- src/fastcore_rs.abi3.so sha256 03db7ae995fdda76eed5d7d72474f5b27141bc9b15814e89827250e35d21ed4b
- KERNEL DISCLOSURE: every computation below ran the PURE-PYTHON kernel
  (KAKEYA_PURE_PY=1 verified: fastcore.force resolves to src/fastcore.py) and used
  kakeya.score(backend="exact"), which is exact rational Python and does not enter the
  PyO3 kernel at all. No Rust was exercised. Timings contended (other jobs on the box).

## 1. Repro of the lens's own commands

  $ grep -rn permissive src/*.py | wc -l
  13                      # lens comment says 14 -> off by one; all 13 are in kakeya.py
                          # (edges/ForcingProblem/score/build_rows/score_fast definitions
                          #  + the docstring). None in cycles8 / g2_tall / stacked /
                          #  rzero_one / scan1 / search.
  $ grep -rn permissive rust/crates | wc -l
  0                       # confirmed: the Rust port has no permissive reading at all

  $ grep -rn "permissive=True" --include=*.py .
  src/kakeya.py:131:  (docstring only)
  (no caller anywhere in the repo)

## 2. The logic: does a NEGATIVE transfer between the two readings?

KAKEYA-WORKBENCH.md:56-63 ("Ambiguity flagged") argues:
  "The matching-suffix reading ... is the *weaker* operation set, so any object valid
   under it is valid under either reading."
That is a HIT-transfer statement (weaker ops => valid stays valid when ops are added).
It says nothing about the converse. Confirmed against the code:
- ConstructibleGraph.m (kakeya.py:86-94) computes m(G) from the FORMULA
  sum_i sum_{e in dom f_i} [f_i(e)!=0]*d_{i+1}..d_k. It never calls edges() and never
  sees `permissive`. So the cost is identical under both readings.
- ConstructibleGraph.edges(permissive=True) (kakeya.py:125-151) emits the full
  t1 x t2 product, a strict SUPERSET of the matching t1==t2 edges.
Hence: same score, strictly larger module M, strictly easier forcing. A 0-hit sweep
under matching-suffix does not bound the permissive space. The lens is right.

## 3. It is not merely a possibility — the readings SEPARATE, and cheaply

rust/refute/adjudicate/r5/separator.py, exhaustive over the d=[2,2] box,
X = [(0,0),(1,0),(0,1),(1,1)], |R| in {0,1}, |T| in {1,2}: 8,320 configurations.

  configurations tried: 8320
  separating (invalid matching-suffix, VALID permissive, same score): 456
  best separating score: 5/3 = 1.6666666666666667

Smallest separator (rust/refute/adjudicate/r5/best.py), hand-checkable:

  f  = [ {(1,): (1,0)}, {(1,1): (0,1), (2,1): (0,1)} ]
  T  = [(2,1)]      R = [((1,1),(0,1))]
  matching-suffix: ok=False  m=4 r=1 n=4 t=1 score=5/3   log: STUCK, 2 vertices unforced
  permissive     : ok=True   m=4 r=1 n=4 t=1 score=5/3   log: SUCCESS: T = V
  edges matching  : (1,1)-(2,1)[1,0]  (1,2)-(2,2)[1,0]  (1,1)-(1,2)[0,1]  (2,1)-(2,2)[0,1]
  edges permissive: the above + (1,1)-(2,2)[1,0] + (1,2)-(2,1)[1,0]

## 4. The counter-argument the record does NOT make, and should

That same object is a *score-5/3 = 1.6667 answer on FOUR vertices* under the permissive
reading — below the Epoch target 1.675 and below the published record
gamma = 1.6751309... . If the permissive reading were the intended one, the Epoch problem
would be solved by a 2x2 box and the Katz-Tao record would not be a record. So the
permissive reading is untenable: with m(G) charging d_{i+1}..d_k for (d_{i+1}..d_k)^2
edges, the operation is simply undercharged and cannot be a sound upper-bound argument.
This closes the ambiguity in the direction the campaign assumed, for a stronger reason
than the one on the page. The correct fix to the record is ONE SENTENCE plus this repro
-- not a re-run of the campaign, and not a `permissive` port into Rust.

## 5. Two overstatements in the lens's wording

(a) "Every result the campaign has produced -- workbench sec 7, results.json,
    RESULTS-RUST.json, ... -- is a negative." results.json scans[11] (`n4_p6_t1`,
    target 7/4) is a 120-HIT row, complete, best 7/4. 27 of 28 rows are negatives;
    every row at a target <= 1.675 is a negative. The claim is right where it matters
    and wrong as literally written.
(b) "the Rust binary cannot test the other reading at all" -- true of Rust, but the
    Python library CAN and does (this adjudication exercised it in ~4 minutes of
    contended wall time). The reading is cheap to test, which is why the gap is small.

## 6. State of the on-disk correction

rust/refute/SWEEP-2026-09-06.md sec E, bullet 1 restates the finding accurately and
does not overstate it ("transfers HITS to the other reading, not 0-hit results. The
Rust binary cannot test the other reading at all"). It is filed as an unverified
research caveat. It is CORRECT but INCOMPLETE: it leaves the ambiguity open when sec 3-4
above settles it. KAKEYA-WORKBENCH.md sec 1 and sec 6.4 item 5 are unchanged.

## Verdict
real = true (the lens was substantively correct: hit-transfer does not give
negative-transfer, and the readings demonstrably separate).
Severity major -> MINOR. It is a one-sentence gap in a justification, on a question
that this adjudication answers in seconds with the campaign's own engine, in favour of
the reading the campaign already uses. No campaign result needs re-running.
