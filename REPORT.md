# REPORT — arithmetic Kakeya, rebuild-the-objects seat (2026-08-24)

Main deliverable: **`KAKEYA-WORKBENCH.md`** in this folder. Machine-readable summary:
**`results.json`**. Scan output: **`logs/`**.

## Mandate vs. delivered

| # | asked | delivered |
|---|---|---|
| 1 | implement the Epoch-verifiable formalism as a clean library with a scorer | `src/kakeya.py`, `src/fastcore.py` — done |
| 2 | unit-test the trivial AK(2) object | `tests/test_basic.py`, 13/13, AK(2) scores exactly 2 |
| 3 | rebuild the easy published 1.75 construction and certify it | **DONE — 7/4 certified in exact rational arithmetic**, `objects/obj_175.py`, `tests/test_175.py`; matches Epoch's own Figure 3 vertex for vertex. Bonus: the **11/6** sums-differences object (Epoch Figure 2) also rebuilt and certified, `objects/obj_11_6.py` |
| 4 | attempt the 1.675 record object; document the blocker | both Katz–Tao iterations decoded and verified; **the blocker is that no finite object attains the record** — see below |
| 5 | write `KAKEYA-WORKBENCH.md` | done, 600+ lines |

Seat success criterion (working scorer + 1.75 certified): **met**.

## Two published objects certified

**Cross-check that settles the implementation question.** The full write-up behind the
problem page (`https://epoch.ai/files/open-problems/arithmetic-kakeya.pdf`, mirrored at
`papers/epoch-ak.pdf`) draws both Katz–Tao configurations. The object rebuilt here is
theirs vertex for vertex, and **our engine forces the same vertex first as their hand
derivation** — for both objects, with no knowledge of their derivations. The formalism is
implemented faithfully.

| object | `X` | `n` | `m` | `r` | `t` | score | status |
|---|---|---|---|---|---|---|---|
| trivial `AK(2)` | 2 slopes | 1 | 0 | 2 | 0 | **2** | certified, exact `Q` |
| Katz–Tao trapezoid (Epoch Fig. 3) | `{0,∞,1,2}` | 4 | 4 | 3 | 0 | **7/4** | certified, exact `Q` |
| Katz–Tao configuration 1 (Epoch Fig. 2) | `{0,∞,1}` | 6 | 7 | 4 | 0 | **11/6** | certified, exact `Q` |

The third is the **sums-differences record** — Goal 2 of the Epoch page asks for anything
below `11/6` using only the three slopes `{(1,0),(0,1),(1,1)}`. That is a second, softer
prize on the same page, and the one where a small-object search has the best odds: the
alphabet is fixed at three slopes and the record object has only six vertices.

## The 1.75 object

Katz–Tao's trapezoid (`math/0010069` Thm 3.2 = `SD(0,1/2,2/3,1; 2-1/4)`), realised as a
`2 x 2` box:
```
score = 7/4   m = 4, |R| = 3, n = 4, |T| = 0
X   = [[0,0],[1,0],[0,1],[1,1],[1,2]]
d   = [2, 2]
f   = [{(1,): (1,0)},  {(1,1): (0,1), (2,1): (1,2)}]
T   = []
R   = [{(1,1): (1,1)}, {(2,1): (1,1)}, {(2,2): (0,1)}]
```
Under Epoch's own naming (`g1=(2,1), g2=(1,1), g3=(1,2), g4=(2,2)`) this is their
Figure 3 exactly, generators included. The forcing log shows the first vertex forced is
`g3 = (1,2)` — the vertex their hand derivation forces first, via
`(1,-1)g3 = (2,2)g1 - (1,1)g2 - (0,2)g4`. The engine finds its own witness for the same
vertex and knows nothing of theirs. Verified by four independent engine configurations.

## The blocker on 1.675 (the load-bearing finding)

`gamma = 1.6751308706`, the largest root of `x^3 - 4x + 2`, is the **fixed point** of
Katz–Tao's corner iteration `SD(beta) => SD((3b^2+2b-2)/(b^2+3b-2))`
(`math/0102135` Thm 4.1). On object parameters `beta = (m+|R|)/(n-|T|) = p/q` that map is
`(p,q) -> (3p^2+2pq-2q^2, p^2+3pq-2q^2)`, and starting from the trivial object it gives
```
2  ->  7/4  ->  171/101  ->  101863/60652  ->  36127271451/21553324589  ->  ... -> gamma
```
strictly decreasing, never reaching `gamma`. **Every finite object has a rational score
strictly above `gamma`, and the Epoch target 1.675 is 1.31e-4 below `gamma`.** So there
is no "1.675 record object" to reconstruct; the task is to find an object outside the
published family. (Epoch's own prompt confirms this: "the best-known current value is
slightly greater than 1.675".) The second-order blocker: the first published object that
beats 1.75 is the depth-2 corner object with `n - |T| = 101`, `m + |R| = 171`, and
Katz–Tao's proof of Thm 4.1 is heuristic in the source, so unrolling it into explicit
coordinates is a construction job, not a transcription. Not attempted here.

## Other results established this seat

* **Theorem (two slopes are never enough).** If every label used lies in at most two slope
  classes, any object that forces has score `>= 2`. Proved; machine-checked on 445 random
  successful two-slope objects. Consequence: all progress comes from the linear relations
  among three or more slopes.
* **Exhaustive `n = 4`.** Four-slope alphabet, `d = [2,2]` and `d = [4]`, `|T| = 0`: best
  score `7/4`, 16 witnesses; a 4-vertex path gives nothing `<= 7/4`. Rerun complete over
  the **six-slope** alphabet with `|T| <= 1` (343 graphs): still `7/4`, 120 witnesses
  (`logs/n4_p6_t1.log`). The trapezoid is the 4-vertex optimum over everything tried.
* **Lemma P7/P8 (new; the cut lemma).** For any `A` subset of `V`, `sum_{u in A} f(u)`
  lies in the span of the labels crossing the cut plus the generator labels inside `A`.
  `A = {v}` recovers the local rank-2 condition; `A = V` with `T` empty gives: **`tau`
  must lie in the span of the generator labels alone**, so any object with `T` empty needs
  at least two generators of two different slopes, and a generator-free object with `T`
  empty can never force anything. Checked on 515 instances. P8 is the natural starting
  point for the missing `3/2` barrier proof.
* **Lemma P6 (new; a real search reduction).** Putting a vertex into `T` is equivalent,
  for the forcing dynamics, to giving it two independent generators — but it costs 1 in
  the denominator instead of 2 in the numerator, and `(p-2)/(q-1) < p/q` exactly when
  `score < 2`. So **any object with score below 2 has at most one generator per vertex**,
  and `r <= n`. Proved; machine-checked on 419 instances. Restricting the search to one
  generator per vertex gives a 6x speedup at `n = 4` and provably loses nothing.
* **Chain remark (a route closed off).** Gluing `D` copies of a block with a per-gap
  interface is score-neutral if the copies are forced one at a time: an interface edge from
  a fully-forced copy acts *exactly* like a generator. Improvements require forcing orders
  that interleave copies — global cancellations, as in the trapezoid.
* **Goal 2 exists and is softer.** The Epoch write-up states a second goal: beat `11/6`
  for `X = {(1,0),(0,1),(1,1)}` (sums-differences, three slopes only). Lower bound
  `1.77898` (Lemm 2015), so there is a real `0.054` gap. Three slopes means the label
  space is `4^bundles`, and the record object has six vertices — this is where a
  small-object search has the best odds. Exhaustive at `n = 6` in the record's own box
  shapes: no improvement. Larger boxes were only partially covered.
* **Reachable-fraction table.** `q = n - |T| = 40` is the first denominator at which 1.675
  is exactly reachable (`67/40`). Any object with `q < 40` that beats the record
  automatically achieves `<= 5/3 = 1.6667`. Small objects must be substantially better,
  not marginally.
* **Engine.** Forcing reduces to one row-space membership test per round
  (`delta_v (x) tau in W|_U`), not one elimination per candidate — this is what makes
  verification cheap. Four pruning lemmas (P1–P4) proved and implemented; P4 (every vertex
  outside `T` must see two non-parallel label directions) pins the mandatory generator
  positions and is the one that collapses the search.

## Honest limits

* The search engine is a **correctness reference, not a search engine**: ~1.3 ms per closure
  in Python, and the min-`|R|` DFS dominates. **28 sweeps were run; no object below `1.675`
  and none below `11/6` was found.** Complete coverage was reached only at `n = 4` (both
  alphabets), at the two `n = 6` three-slope boxes for Goal 2, and for the generator-free
  question. Everything else is a truncated *prefix* of the enumeration — not a random
  sample — so absence of hits there proves nothing. Full table in §7 of the workbench.
* Two operational mistakes worth not repeating: re-launching a timed-out sweep re-walks
  the same prefix and adds no coverage (shard or randomise the seed); and an in-place
  `sed` on a log file that a running process holds open silently detaches the writer (two
  `RESULT` lines had to be recovered from the monitor stream, and are marked as such in
  `logs/g2_tall.log`).
* Epoch states the method cannot work below `3/2`; the lemmas proved here only give
  `score >= 1`. Reproducing the `3/2` barrier is open and is probably where the right
  objective function for a search comes from.
* Operation 1 in the problem text is ambiguous about whether the two endpoints must agree
  in their trailing coordinates. The library implements the matching-suffix (weaker, sound)
  reading, which is the one consistent with `m(G)`; nothing here depends on the difference.
* The six-line answer format is emitted with Python tuple keys; if a candidate is ever
  submitted, check it against Epoch's actual parser first.
