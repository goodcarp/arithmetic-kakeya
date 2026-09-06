# PREDICTIONS — pre-registered outcomes for the Rust re-runs (Fable, 2026-09-04)

Scope: the four searches Python could not finish or that are worth re-running as a
differential check. Everything here was written before any Rust result existed. Numbers
marked *computed* come from scripts in this folder (`count_pairs.py`, `time_sample.py`,
`cycle8_check.py`) run against `K/src` read-only; their raw output is in `*.out` and `bg/`.

## 0. Summary table

| target | Python status | predicted `best` | predicted `hits` | beats target? | credence |
|---|---|---|---|---|---|
| g2_tall 2x5 (`<11/6`, t<=1) | TIME LIMIT 818 s, incomplete | `null` | 0 | no | 0.93 |
| g2_tall 2x6 (`<11/6`, t<=1) | TIME LIMIT 867 s, incomplete | `null` | 0 | no | 0.90 (conditional on the run finishing; see 4) |
| cycles8 POOL6 (`<=67/40`, t<=2) | TIME LIMIT, tested 526 | `null` | 0 | no | 0.96; the three two-4-cycle patterns are **settled by argument** (2.2), the 8-cycle patterns for t=1,2 and t=0,r<=4 by an exhaustive side computation (2.3), t=0,r=5 pending |
| stacked POOL4 (`<7/4`, t<=2) | complete, 8268 s, best 7/4, hits 0 | `7/4`, witness all-ZERO interface, m=8 r=6 t=0 | 0 | no | 0.97 |
| stacked POOL6 (`<7/4`, t<=2) | complete, 16959 s, best 7/4, hits 0 | same | 0 | no | 0.97 |

"Credence" is my probability that a *correct* port prints that line. The residual mass is
mostly "the port has a bug and prints something else", not "an object exists".

## 1. What the drivers actually measure (so the port's output can be read)

* `best` in every driver is only ever assigned when `min_generators` returns a generator
  set **within the budget** `floor(target*den) - m`. So `best == None` means "nothing at or
  below the cutoff", not "nothing scored". A port that tracks the best score over all
  objects would print `11/6` for g2_tall 2x6 (two stacked records) and `7/4` for
  cycles8 (two trapezoids); that is a semantics divergence, not a discovery.
* g2_tall's cutoff is *strictly* below 11/6: `cap = floor(11q/6)`, decremented when
  `cap/q == 11/6`. For q=12 that is 21, for q=11 20, q=10 18, q=9 16.
* cycles8 counts `tested` **before** calling `min_generators`; a complete run prints
  exactly the number of (graph, T0) pairs surviving the budget/rank/P4 prunes
  (computed below: 1,905,420). If the port prints a different `tested` on a complete run,
  its prune or enumeration order differs from Python.
* stacked's witness is the **first** tuple reaching the best score (strict `<` update), and
  the first tuple in `itertools.product` order is the all-ZERO interface. A port that
  updates on `<=` or enumerates in a different order prints a different witness while
  being otherwise correct.
* All three drivers enumerate labels in `itertools.product` order with the alphabet
  `[ZERO] + pool` and the last slot varying fastest. `complete` is `elapsed < tlimit`.

## 2. Reasoning and what is settled by argument

### 2.1 Lemma C (component condition) — proved

Let c be any slope other than the slope of tau (every label slope qualifies, and so does
any unused slope with a+b != 0). Let G_{-c} be the graph of edges whose label is **not**
parallel to c, and Gamma_{-c} the set of vertices carrying a generator not parallel to c.
If the object forces, then

    every connected component of G_{-c} contains a vertex of T0 or of Gamma_{-c},

hence `#comp(G_{-c}) <= t + r_{-c}` for every such c.

*Proof.* Pick a linear functional lambda: Q^2 -> Q with kernel c; then lambda(tau) != 0.
For f in M, lambda∘f = sum_e c_e lambda(x_e)(delta_u - delta_v) + sum_g c_g lambda(x_g)
delta_w; edges and generators parallel to c drop out, so lambda∘f lies in
B(G_{-c}) + span{delta_w : w in Gamma_{-c}}, where B(G) is the image of the coboundary of
G, i.e. the vectors summing to zero on every component of G. Let f_j witness the forcing
of v_j: supported on S_{j-1} ∪ {v_j}, f_j(v_j) = tau. Then u = lambda∘f_j is supported on
S_{j-1} ∪ {v_j} with u(v_j) = lambda(tau) != 0. If the component K of v_j in G_{-c} has no
Gamma_{-c} vertex, u sums to zero on K, so some other vertex of K carries u != 0 and
therefore lies in S_{j-1}. Apply this to the first-forced vertex of each component: K
contains a T0 vertex or a Gamma_{-c} vertex. Distinct components need distinct such
vertices. []

Machine check: `lemma_c_test.py` — 40,000 random (box, POOL6 labels, T0, generators)
instances, 8,196 of which force; Lemma C violated 0 times over eight slopes each
(the six pool slopes plus two unused ones).

This is Theorem 2's mechanism (kill one slope, look at components) applied one slope at a
time. It reproduces P7 (T0 empty: the component of the first vertex needs non-c
generators for every c, so two distinct generator slopes) and it is the prune used in
`cycle8_check.py`.

### 2.2 cycles8: the three "two 4-cycles" patterns are settled — no object within budget

`cycles8.main` finds 5 presence patterns (computed; product order):
`(0,1,1,1,1,1,1)` = f2x2 + f3x4, `(1,0,0,1,1,1,1)` = f1 + f3x4, `(1,1,1,0,0,0,0)` =
f1 + f2x2 — each is **two disjoint 4-cycles**; `(1,0,1,1,1,0,0)` and `(1,1,0,0,0,1,1)`
are **8-cycles** (vertex-labels around the cycle x, z1, x, y, x, z2, x, y with x = the f1
label, y = the f2 label, z1, z2 = the two f3 labels; the two patterns are mirror images
under a=1 <-> a=2 and give identical labelled cycles).

Claim: no two-4-cycle object scores <= 67/40 for any T0 with t <= 2.

*Proof.* The module of a disconnected graph is the direct sum of the component modules
(every generator row is supported inside one component), and a witness for v projects to a
witness inside v's component. So the union forces iff each component forces with its own
R_i, T_i, and the score is the mediant
`(m_1+r_1 + m_2+r_2)/((n_1-t_1)+(n_2-t_2)) >= min_i (m_i+r_i)/(n_i-t_i)` (a component with
t_i = 4 contributes 4 to the numerator and 0 to the denominator, which only raises the
score). Each component is a 4-cycle whose opposite edges share one label (the bundle
structure: labels x, z, x, y around the cycle) — exactly the labelled graphs enumerated by
the **complete** scan `n4_p6_t1` (`d=[2,2]`, all 343 POOL6 label triples, |T| <= 1, target
7/4, `logs/n4_p6_t1.log`): best 7/4, i.e. r >= 3 at t=0 and r >= 2 at t=1 for every
4-cycle; t >= 2 gives (4+r)/2 >= 2 outright. Hence each component scores >= 7/4 and so
does the union. The cycles8 budgets (r <= 5 at t=0, <= 3 at t=1, <= 2 at t=2) all sit
strictly below the 7/4 line ((8+6)/8 = 7/4 needs r = 6), so `min_generators` returns None
on every one of these pairs. []

This relies on the correctness of the Python `min_generators` in that complete scan
(exhaustive DFS within budget, prunes P1/P4/P6 all proved in the workbench); it is the
same code the port replicates, so it is a shared assumption. Coverage: these three
patterns are 54,648 of the 57,240 labelled graphs and 1,823,760 of the 1,905,420 tested
pairs (95.7%).

### 2.3 cycles8: the 8-cycle patterns — partial settlement by side computation

Lemma C with c = x already does most of the work. Removing the four x-edges leaves the
four non-x edges as components (when y, z1, z2 are not parallel to x): `{2,3},{4,5},
{6,7},{8,1}` in cycle numbering. So `4 <= t + r_{-x}`. If y is parallel to x the
non-x graph has 6 components (`6 <= t + r`, impossible under every budget); if exactly one
of z1, z2 is parallel to x there are 5 (`5 <= t + r`: only t=0, r=5 survives, with one
non-x generator in each component). So within budget the only live cases are:
generic labels with (t=0, r in {4,5}), (t=1, r=3), (t=2, r=2), and one-z-parallel labels
with (t=0, r=5).

`cycle8_check.py` enumerates every generator set satisfying Lemma C for all six POOL6
slopes plus P4, for all 6^4 = 1296 label tuples, and calls `fastcore.force`. Phase
"cheap" covers (t=2, r<=2), (t=1, r<=3), (t=0, r<=4); phase "r5" covers (t=0, r=5).
Results are appended in section 6 as they land. Prediction for both phases: **zero
successes**. Reasoning: on a generic cycle (adjacent labels non-parallel) an unforced
vertex without a generator blocks any witness passing through it, a generator parallel to
one incident edge can only absorb, and only a generator non-parallel to both edges
transmits. With T0 empty the first vertex therefore costs two generators (P7), and every
later vertex needs a second direction that is either its own generator or a chain of
paid-for generators; the only free vertex is the last one, whose two neighbours are both
forced. That heuristic gives r >= n-2 = 6 unless a global cancellation of the trapezoid
kind exists; the cheap phase tests whether one exists with r <= 4, the r5 phase with
r = 5. I could not turn the heuristic into a proof (the trapezoid itself is the example
of a full-loop cancellation that beats the local count), which is why it is computed.

### 2.4 g2_tall 2x5 and 2x6: not settled; what Lemma C gives and why it is not enough

The family is the 2 x R ladder: all R rungs labelled h = (1,0) (the level-1 bundle), and
the 2(R-1) verticals each labelled h, v = (0,1), d = (1,1) or absent; m = R + #verticals.
Apply Lemma C for c = h, v, d and add:

* c = h: G_{-h} is the verticals labelled v or d, a forest inside the two columns:
  `comp = 2R - a_v - a_d`.
* c = v: G_{-v} = rungs + verticals labelled h or d: `comp = R - g_{hd}`, where g_{hd} is
  the number of gaps with at least one h/d vertical.
* c = d: `comp = R - g_{hv}`.

Summing `comp <= t + r_{-c}` over the three slopes gives `2r + 3t >= 4R - a_v - a_d -
g_{hd} - g_{hv}`, and with m = R + a_h + a_v + a_d, minimising per gap (the cheapest gap is
one d-vertical and one empty slot, contributing -1/2):

    m + r >= (5R + 1)/2 - 3t/2      (proved)

For R=5, t=0 that is 13 (score 1.3); for R=6, 16 (1.33). The record's own box R=3 gives 8
against the true minimum 11. So Lemma C — like P3 and P4 — is far too weak here: it
only sees which components are "live", and the three-slope module can cascade (the 11/6
object forces g5 first through a witness spread over the whole box). Settling 2x5/2x6 by
proof needs a bound that charges the cascade, which is the 3/2-barrier question the
workbench lists as open (item 6.4.1). **Blocked**; the prediction below is by analogy, not
by proof.

Why I still expect nothing below 11/6:
* R=3 is complete (`g2_23_t1`, 1024 graphs, t<=1): nothing below 9/5, so the record's
  m+r = 11 is the minimum at q=6 and 5 (t=1 needs m+r <= 9 at q=5: not found).
* Stacking two R=3 records gives m+r = 22 at q=12 — exactly 11/6, never strictly below
  (Chain remark). The extra denominator from t=1 (q=11, cap 20) would require saving two
  numerator units for one denominator unit; P6 says T beats a *double* generator, i.e. the
  swap is worth exactly one generator plus the vertex's own, never two extra.
* The gentlest cutoffs are 18/10 = 1.8 (R=5, t=0) and 20/11 = 1.818 (R=6, t=1); the
  record family has to give up 0.033 or 0.015 with only one new slope relation available
  (the kernel of {h,v,d} is one-dimensional).
* Every incomplete Goal-2 run at n=8..12 found nothing (all prefixes, so weak evidence).

### 2.5 stacked POOL4 / POOL6 — settled by the completed Python runs

Both runs completed (625 and 2401 label tuples). The all-ZERO interface is two disjoint
trapezoids: score 7/4 exactly by the mediant argument of 2.2 (each trapezoid needs r=3),
and it is the first tuple, so it is the printed witness. The port must reproduce
`best = 7/4`, witness `labels=((0,0),(0,0),(0,0),(0,0)) m=8 r=6 t=0 T0=[]`, hits 0. A
different witness with the same score means an ordering/update-rule difference; a hit
means a port bug until proven otherwise (re-verify any hit with `kakeya.score(...,
backend="exact")`).

## 3. Outer-iteration counts (computed with `count_pairs.py`, no DFS)

"pairs" = (labelled graph, T0) pairs that reach `min_generators` after the budget, rank
(P3) and P4 prunes — the unit of DFS work. `tested` in cycles8 is exactly this count.

| run | label tuples | T0 choices | pairs into `min_generators` |
|---|---|---|---|
| g2_tall 2x4 | 4^6 = 4,096 | 1 + 8 | 31,718 |
| g2_tall 2x5 | 4^8 = 65,536 | 1 + 10 | 672,719 |
| g2_tall 2x6 | 4^10 = 1,048,576 | 1 + 12 | see section 6 (≈13M, running) |
| cycles8 POOL6 | 57,240 (216 + 7,776 + 46,656 + 1,296 + 1,296 over the 5 patterns) | 1 + 8 + 28 | **1,905,420** (per pattern in product order: 1,557,900 / 259,650 / 40,830 / 40,830 / 6,210) |
| stacked POOL4 | 5^4 = 625 | 37 | 8,789 |
| stacked POOL6 | 7^4 = 2,401 | 37 | 28,357 |

The Python cycles8 run tested 526 pairs in 2400 s (4.6 s per pair) — all inside the first
pattern `(0,1,1,1,1,1,1)`, i.e. about the first 14 of its 46,656 label tuples. Its
"tested" is a prefix count, not evidence.

Free-budget histogram for g2_tall (t, budget minus mandatory generators) is in
`count_pairs.out`; the DFS depth is that free budget, and the candidate list is
(unforced vertices without a mandatory generator) x 3 slopes.

## 4. Runtime estimates for the port

Measured Python costs (`time_sample.out`; `force` is called ~50 µs per call on these
warm-started matrices, far below the workbench's 1.3 ms figure, which was for cold
closures at larger n):

| family | per graph, product-order prefix | per graph, random labels | force calls per graph |
|---|---|---|---|
| 2x4 | 0.2–1.0 s | 0.01–0.33 s | 0.3k–13k |
| 2x5 | 1.8–3.1 s (first 4) | 0.04–4.7 s | 0.6k–140k |
| 2x6 | (see section 6) | 0–55 s in 3 samples | up to 1.05M |

Python-equivalent totals: 2x4 ≈ 4096 x 0.3 s ≈ 20 min (the logged run was ~56% through
at 700 s); 2x5 ≈ 65,536 x ~3 s ≈ 55 h; 2x6 ≈ 1.05M x ~20 s ≈ 250 days (high variance,
dominated by graphs with m in the low teens where the free budget is 5–7).

A faithful Rust port of `force` + the DFS should be 30–100x faster on this workload (the
matrices are tiny, so allocation and the DFS bookkeeping matter as much as arithmetic).
So:

* 2x4: seconds to a minute. Should complete; expect `complete: true`, best null, hits 0.
* 2x5: **0.5–2 hours**. Completes only if the port's time limit is raised well above the
  Python 700–900 s; at a 900 s limit it will report `complete: false` again and will have
  walked 20–60% of the tuples. If it reports completion in under ~10 minutes with a
  Python-faithful DFS, either the machine is much faster than my scaling or the DFS is
  pruning differently — check `pairs` against 672,719.
* 2x6: **days**. Will not complete under any limit measured in hours. A port that claims
  `complete: true` for 2x6 in an hour has changed the search (or skipped pairs).
* cycles8 POOL6: 1.9M pairs; Python cost is 4.6 s per pair on the first pattern (budget
  5, 48 candidates) → Python-equivalent ≈ 100 days; Rust 1–4 days. Will not complete under
  an hour-scale limit; `tested` will be a prefix count of the first pattern, and hits 0.
  Note 95.7% of the pairs are in the three patterns settled in 2.2, so a smarter driver
  could skip them by argument and spend everything on the 81,660 8-cycle pairs.
* stacked: Python 8268 s and 16959 s → Rust roughly 2–8 minutes each. Both complete.

Sanity rule for the reader: elapsed time should be roughly (pairs walked) x (per-pair
cost); a run whose pairs-per-second is 1000x Python's is not running the same DFS.

## 5. Driver-level traps for the port (beyond fastcore)

* `int(target * den)` with `Fraction` is exact floor; a float port gets
  `int(1.675*7) = 11` right but must not use `round`. For 11/6 the cutoff is strict (2.1
  above).
* `local_requirement` counts P4 needs against **incident edge labels only**, both endpoints
  of every edge, ignoring generators; `indep_dirs` caps at 2 and treats ZERO as absent.
* `_dir_choices(k>=2)` returns `[]`, so any (graph, T0) with a vertex needing two
  generators is *skipped* (P6), not searched. Reproduce exactly or `tested`/pair counts
  drift.
* The DFS `extend` warm-starts from the closure `T2`, skips candidates at vertices in
  `T2` (P1) and at vertices already carrying a generator (P6), iterates candidates in the
  fixed order `(vertex asc, pool order)` from `start`, and prunes with
  `len(gens) + 1 >= len(best)`. The *set* returned is the first minimum-size set found in
  that order; a port with a different candidate order returns a different (equally valid)
  set, which changes `HITOBJ`/witness lines but not `best`/`hits`.
* `min_generators` iterates `itertools.product` over the mandatory-slot direction choices;
  the mandatory generators are added in slot order (vertex ascending).
* g2_tall's `hits` list records every in-budget (score, labels, m, gens, T0) — not only
  strict improvements — so `hits` can exceed the number of distinct scores.
* stacked prints `float(b)`; `best` is a `Fraction`. cycles8 prints `HITOBJ` with
  `default=str`, so tuples of tuples appear as strings.
* Python's `time.time() - t0 > tlimit` is checked once per label tuple *before* the work,
  so a run always finishes the tuple it is on; `seconds` can exceed `tlimit` by one tuple's
  cost (867 s for a 700 s limit in the 2x6 log).

## 6. Computed results (appended 2026-09-06 after the closing audit; written before the Rust 8-cycle cross-check returned)

* `cycle8_cheap` (t=2 r<=2, t=1 r<=3, t=0 r<=4; every generator set satisfying Lemma C for all six POOL6 slopes plus P4; all 1296 label tuples of the 8-cycle patterns): **0 successes**, 10,062,000 `force` calls, 2973 s (`cycle8_cheap.out`).
* `cycle8_r5` (t=0, r=5, same prune): **0 successes**, 91,993,680 `force` calls, 13,369 s (`cycle8_r5.out`).
  Together with 2.2 (the three two-4-cycle patterns, settled by the mediant argument on the complete `n4_p6_t1` scan) this exhausts cycles8 POOL6 under the stated budgets: no object scores <= 67/40 with t <= 2 — modulo the correctness of Lemma C (2.1) and P6 as prunes. Prediction row 3 of section 0: CONFIRMED by side computation.
* g2_tall 2x6 pair count: **13,183,980** pairs into `min_generators` (`count_pairs.out`; the section-3 table said "running"). Free-budget histogram is in `count_pairs.out`.
* Rust long runs (`rust/RESULTS-RUST.json`): stacked POOL4 (23.8 s) and POOL6 (293.5 s) reproduce the Python exactly — rows 4 and 5 CONFIRMED; g2_tall 2x5 (7207 s) and 2x6 (14,558 s) hit their caps with 0 hits — rows 1 and 2 CONSISTENT only; the 6-hour cycles8 POOL6 run tested 98,973 pairs, all inside pattern 0 (an exact prefix ending at label tuple #3008 of 46,656), i.e. inside the region 2.2 already settles — it added nothing about the 8-cycles. The runtime estimate for 2x5 (implied by section 3) was wrong by more than 10x.
* A direct Rust enumeration of the two 8-cycle patterns only (`kakeya-search cycles8 --patterns 8cycle`, 81,660 pairs, no Lemma C prune — the Python prune order reproduced exactly) was started 2026-09-06 as an independent cross-check of the two bullets above.
