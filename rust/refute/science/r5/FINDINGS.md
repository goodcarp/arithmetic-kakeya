# refute / science / r5 — "what did we miss": does the computation bear on the question?

Lens: **science** (research-level, not code).  Date 2026-09-06, ~16:35–17:10 EDT.
Write scope: this directory only.  Nothing under `crates/`, `src/`, `logs/`,
`tests/`, `results.json`, `RESULTS-RUST.json`, `KAKEYA-WORKBENCH.md`,
`PROGRESS.md` was touched.

**Machine disclosure.** Every timing here is contended: pid 13369 (the pure-Python
cycles8 POOL3 oracle) was live throughout, and at least four other agents' jobs
were on the box (`ps` at 17:00 showed `improve/perf/kperf`, `refute/external/r5`,
`refute/search/r5-hitpaths`).  Wall-clock figures are therefore useless; **CPU
time (`user`) is the number to read**, and even that is a mild over-estimate.

**Kernel disclosure.** Every Python run below was launched with `KAKEYA_PURE_PY=1`
from `src/`, i.e. the **pure-Python** `fastcore`, not the PyO3 kernel.  Verified
at launch (`fastcore.force.__module__ == 'fastcore'`).  The Rust runs used the
audited binary `rust/target/release/kakeya-search`
(sha256 `add554183aaa3d7cf1f2d468ba11e39926aea035853809811af4e6c40010fcf9`).

**Verdict: `refuted = true`.**  One stated closure claim is, as written, false —
not because the mathematics is wrong, but because the family it claims to close
contains a phase (`t = 3`) that neither the driver nor any side computation ever
visited.  I closed that phase myself (0 hits), so the claim is now *true*; it was
not true when it was written.  Everything else below is scoping, feasibility and
"what to run next".

---

## 0. Headline results

| # | finding | kind | severity |
|---|---|---|---|
| F1 | `cycles8` never searches `t = 3`, where the budget is 0 and the score would be **8/5 = 1.600 ≤ 67/40**.  Both `src/cycles8.py` (`for t in (0,1,2)`) and `drivers/cycles8.rs:195` (`(0..=2)`) hardcode it.  "cycles8 POOL6 is closed" was therefore false as written. **Closed here: 0 hits.** | divergence | major |
| F2 | Every negative in the campaign is conditional on the **matching-suffix** reading of Operation 1.  The workbench's justification ("the weaker operation set, so any object valid under it is valid under either reading") is sound for a *hit* and vacuous for a *negative*, and all results to date are negatives.  `permissive=True` exists in Python and is used by **no** driver and is **absent from the Rust crates entirely** (`grep -c permissive rust/crates` = 0). | science | major |
| F3 | `rzero` cannot find anything, by a theorem in the same document.  `src/rzero.py` calls `force(rows, n, set())` — `T0` is **always empty** — and P7 says an object with `r = 0` and `T` empty can never force one vertex.  The six rzero rows in workbench §7 (four marked complete, up to 78,125 labellings) are a P7 regression test, not search coverage. | record | minor |
| F4 | "Complete" sweeps are complete in the *labellings* and a single point in the *slope moduli*.  The group fixing tau is **sharply** 2-transitive, so exactly two slopes normalise and a k-slope alphabet carries k−2 real moduli.  POOL3 pins the one Goal-1 modulus at slope 1, POOL4 at (1,2), POOL6 at (1,2,3,1/2).  **No run in the record varies a modulus.** | science | major |
| F5 | For Goal 2 the alphabet is pinned, and the usable label symmetry group has order **2** (measured, §5A).  `g2_tall` pins `f_1((1,)) = (1,0)`, which by that group covers `f1 ∈ {(1,0),(0,1)}` only — **half** the level-1 alphabet.  A *complete* 2×5 / 2×6 run would still leave `f1 = (1,1)` and `f1 = ZERO` unsearched. | science | major |
| F6 | 2×6 to completion is **~1,030 CPU-hours** at the measured rate (§2.1) — not feasible.  2×5 is **~12 CPU-hours** — feasible tonight.  The "6.3 GB RSS" premise is stale: that was the `row_pool` leak, fixed 2026-09-06 (1,634,877,440 → 995,328 bytes at the same `scanned`).  Memory is no longer a constraint; CPU is. | record | minor |
| F7 | `--deg` on `cycles8` is vacuous for every value but 2: the driver requires `G.m == n` *first*, and `sum(deg) = 2m = 2n` forces `deg = 2` for an all-equal-degree graph.  `--deg 1` / `--deg 3` select zero patterns. | record | note |
| F8 | The **3/2 barrier** is load-bearing for the whole framing (it is what makes the findable window at `q ≤ 12` the single interval `(3/2, 5/3]`) and is unverified: Katz, *Elementary proofs and the sums differences problem*, Collectanea Math. 57 (2006) is **not in `papers/`** (checked: the folder holds kt / newbounds / Green–Ruzsa / Tao 2025 / epoch-ak and nothing else). | science | major |

---

## 1. Q1 — is "cycles8 POOL6 closed" true?

### 1.1 What each piece actually settles

`cycles8` searches a much smaller family than its name suggests.  `main()` keeps a
presence pattern only if **`G.m == n = 8` AND every vertex has degree exactly 2**.
That is 5 presence patterns and 57,240 labelled graphs out of the
**823,543** POOL6 labellings of the `2x2x2` box — **6.95%**.  Everything with
`m ≠ 8`, or with an irregular degree sequence, is outside the driver.  So
"cycles8 POOL6 closed" must never be read as "n = 8 POOL6 closed"; at `m = 7` the
`t = 0` budget is 6 and at `m = 6` it is 7, and none of that has been searched.

Within that family:

* **PREDICTIONS §2.2** settles the three two-4-cycle patterns (indices 0, 1, 4 —
  54,648 graphs, 1,823,760 of 1,905,420 pairs, 95.7%) by the mediant argument over
  the complete `n4_p6_t1` scan.  Independently re-derived here without a budget in
  the way (§5B): over all 216 all-present POOL6 4-cycles on `d=[2,2]`,
  **min |R| = 3 at t = 0** (score 7/4) and **min |R| = 2 at t = 1** (score 2);
  6 label triples never force at all with |R| ≤ 5 at t = 0.  So every component
  scores ≥ 7/4 > 67/40 at *every* `t`, and the mediant of the two components does
  too.  §2.2 holds, and holds for all `t`, not just `t ≤ 2`.
* **PREDICTIONS §2.3 + `cycle8_cheap` / `cycle8_r5`** settle the two 8-cycle
  patterns at `t ≤ 2` (0 successes, 102M `force` calls) **modulo Lemma C as a
  prune**.
* **The Rust cross-check finished while this lens was running** and is
  Lemma-C-free:
  `logs/rust-targets.log` at 2026-09-06T20:46:00Z, `exit=0`,
  `RESULT {"tag": "cycles8", "pool": 6, "best": null, "hits": 0, "tested": 81660, "patterns": [2, 3]}`.
  `tested = 81660` is the predicted complete count, so this is a **complete**
  independent exhaustion of the 8-cycle patterns at `t ≤ 2`.

### 1.2 F1 — the residual: `t = 3`

Both implementations hardcode the phase loop:

    src/cycles8.py:            for t in (0, 1, 2):
    drivers/cycles8.rs:195:    let combos: ... = (0..=2).map(|t| combinations(n, t)).collect();

At `t = 3` the denominator is `n − t = 5` and the budget is
`int(67/40 · 5) − m = 8 − 8 = 0`, so `r = 0` and the score is **8/5 = 1.600**,
which is ≤ 67/40 = 1.675 — a hit, and an object that would beat `gamma` by
0.075.  At `t = 4` the budget is `int(6.7) − 8 = −2 < 0`, so **`t = 3` is the one
and only uncovered phase**, and it is inside the target.  Nothing in
`PREDICTIONS.md`, `PROGRESS.md`, `RESULTS-RUST.json` or the 09-05 handoff mentions
`t = 3`; every closure sentence is silently scoped to the driver's own `t ≤ 2`.

**Closed here.**  `t3_check.py` enumerates the phase directly (r = 0, so no DFS —
just `force`), with the proved P4 prune (at `r = 0` every vertex outside `T0`
needs two non-parallel incident edge labels, so the failing vertices must all lie
in `T0`):

```
cd src && KAKEYA_PURE_PY=1 /usr/bin/python3 ../rust/refute/science/r5/t3_check.py 8cycle
RESULT {"tag": "cycles8_t3_r0", "pool": 6, "which": "8cycle", "t": 3, "r": 0,
        "score_if_hit": "8/5", "graphs": 2592, "skipped_by_P4": 492,
        "pairs": 87600, "hits": 0, "seconds": 42.4}

cd src && KAKEYA_PURE_PY=1 /usr/bin/python3 ../rust/refute/science/r5/t3_check.py idx:1,4
RESULT {"tag": "cycles8_t3_r0", "pool": 6, "which": "idx:1,4", "t": 3, "r": 0,
        "score_if_hit": "8/5", "graphs": 7992, "skipped_by_P4": 1092,
        "pairs": 236400, "hits": 0, "seconds": 96.9}
```

The script's own component count independently reproduces the record's pattern
table (`indices 0, 1, 4 = two 4-cycles; 2, 3 = single 8-cycles`).

The remaining pattern (index 0, 46,656 graphs, ~21 min pure Python) is closed by
argument from §5B rather than by CPU: a two-4-cycle object at `t = 3, r = 0`
needs **both** components to force with `r_i = 0`, and any split of `t = 3` over
two components leaves one with `t_i ≤ 1`, where the measured minimum is
`|R| = 3` (t=0) resp. `2` (t=1).  Impossible.  If you want it computed anyway:
`t3_check.py idx:0`.

**Net on Q1.** The residual is now empty: the two-4-cycle patterns are settled at
every `t` by the mediant argument on a re-measured 4-cycle floor; the 8-cycle
patterns are settled at `t ≤ 2` twice (Lemma-C side computation, and the
Lemma-C-free complete Rust run that landed at 20:46Z) and at `t = 3` by the
exhaustive run above.  `t ≥ 4` is budget-infeasible.  So the sentence
"cycles8 POOL6 closed" is now true — **and it was not true, as written, before
this lens ran.**  What it does *not* mean is "n = 8 closed": 93% of the box's
POOL6 labellings are outside the driver.

---

## 2. Q2 — g2_tall 2×5 and 2×6: feasible? and does it matter?

### 2.1 Measured rates (contended; read the CPU column)

| run | threads | walked / total tuples | pairs | CPU s | pairs / CPU-s | s / pair |
|---|---|---|---|---|---|---|
| 2×3 **complete** | 2 | 256 / 256 | 1,587 | 2.99 | 531 | 0.0019 |
| 2×4 prefix (tlimit 280) | 2 | 1,667 / 4,096 | 11,682 | 353.6 | 33.0 | 0.030 |
| 2×4 **complete** (tlimit 1200) | 2 | 4,096 / 4,096 | **31,718** | 791.9 | 40.1 | 0.0250 |
| 2×5 prefix (tlimit 60) | 1 | 34 / 65,536 | 353 | 26.8 | 13.2 | 0.076 |
| 2×6 prefix (tlimit 55) | 1 | 8 / 1,048,576 | 91 | 30.8 | 2.95 | 0.339 |

Complete pair counts (Fable's `count_pairs.py`, gated against the Rust `pairs`
key): 2×4 = 31,718; **2×5 = 672,719**; **2×6 = 13,183,980**.

All prefixes are biased *pessimistic*: `itertools.product` order puts the
ZERO-heavy tuples first, and ZERO-heavy means small `m`, large budget, deep DFS.
The 2×4 row measures that bias directly — prefix 0.030 s/pair vs complete
0.0250 s/pair, a factor of **1.2**.  Its `pairs = 31718` also matches Fable's
independent `count_pairs.py` exactly, so the enumeration and prune order are
still the Python one.

Applying the same 1.2 correction:

* **2×5: 672,719 × (0.076/1.2 ≈ 0.063) s ≈ 42,000 CPU-s ≈ 12 CPU-hours**
  (0.076 s/pair uncorrected gives 14).  On 5 free cores that is 2–3 wall-hours.
  **Feasible tonight.**
* **2×6: 13,183,980 × (0.339/1.2 ≈ 0.28) s ≈ 3.7 × 10⁶ CPU-s ≈ 1,030 CPU-hours
  ≈ 43 core-days** (uncorrected 1,240).  Even a further 4× optimism leaves
  250 CPU-hours.  **Not feasible here.**

Memory is a non-issue now (F6): the 6.3 GB figure was the `row_pool` free-list
leak, fixed 2026-09-06 — the same refuter memory config went
1,634,877,440 → 995,328 bytes at identical `scanned`.  The 09-05/09-06 production
2×6 run predates that fix.

### 2.2 Would a complete 0-hit change anything?

**About the Epoch 1.675 target: no.**  `g2_tall`'s cutoff is `< 11/6 = 1.8333`; it
is a Goal-2 instrument.  Its hit region *does* contain scores ≤ 1.675 (a hit at
14/8 = 1.75 or 16/10 = 1.6 would be recorded, since `hits` logs every in-budget
score), so a **hit** could bear on Goal 1 — but a 0-hit says only "nothing below
11/6 in this family", a Goal-2 negative.

**About Goal 2: it would not close the box either (F5).**  `g2_tall` pins
`f_1((1,)) = (1,0)`.  For Goal 2 the alphabet is pinned by the problem to slopes
`{0, ∞, 1}`, and the only symmetries available are the Möbius maps that permute
`{0, ∞, 1}` **and** fix `−1`.  Measured (§5A): of the six permutations, exactly
**two** are realised — the identity and `0 ↔ ∞`.  So `g2_tall` covers
`f1 ∈ {(1,0), (0,1)}`, i.e. 2 of the 4 values in `[ZERO] + POOL3`.
`f1 = (1,1)` and `f1 = ZERO` are unsearched at R = 5, 6, and the `(1,1)` half is
the same `4^{2(R−1)}` again.

**And it is not settled analytically.**  Both the workbench (§6.4.1) and
PREDICTIONS §2.4 say so explicitly: Lemma C gives only
`m + r ≥ (5R+1)/2 − 3t/2`, i.e. score ≥ 1.30 at R = 5 against a true minimum of
1.83 — "far too weak", "**Blocked**; the prediction below is by analogy, not by
proof".  There is no "11/6 cap" theorem.  The record is honest about this; the
task framing is not.

---

## 3. Q3 — can any driver find an object outside the published family?

**"Outside the published family" is not the binding constraint.**  All five
drivers enumerate arbitrary labelled constructible graphs within their shape
restriction; none is confined to the corner/segment ladder.  In fact the ladder's
depth-≥2 objects have `q = 101, 60,652, 2.16 × 10^10` and are outside *every*
driver's reach, so the drivers search **only** outside the published family,
except that they rediscover the depth-1 trapezoid (n = 4) and the 11/6 object
(n = 6).

The binding constraints are (a) the denominator arithmetic and (b) the shape
restriction per driver.

**(a) Denominator arithmetic.**  Enumerating every `p/q ∈ (3/2, 67/40]` (the whole
window if the 3/2 barrier binds — F8):

| q | admissible scores in (3/2, 1.675] |
|---|---|
| 3 | 5/3 |
| 4 | **none** |
| 5 | 8/5 |
| 6 | 5/3 |
| 7 | 11/7 |
| 8 | 13/8 |
| 9 | 14/9, 5/3 |
| 10 | 8/5 |
| 11 | 17/11, 18/11 |
| 12 | 19/12, 5/3 |

So the window is non-empty at every `q ≥ 5`, but the object has to beat `gamma` by
0.0085 (best case, `q ≡ 0 mod 3`) to 0.075 — 65× to 570× the 1.31e-4 target gap.
`q = 40` is the first denominator at which 1.675 is *attained*.

**(b) Per-driver space.**

| driver | what it enumerates | reachable `q` | in-window scores it could report |
|---|---|---|---|
| `scan` | every labelling of a given box over a fixed pool, all `T0` with `\|T\| ≤ max_t`, min-`\|R\|` DFS | `n − t`, any box | anything ≤ target |
| `cycles8` | **only** `m = n = 8` with every degree exactly 2 on `2x2x2`; 6.95% of the box | 8, 7, 6 (+5 at `t=3`) | 13/8 (t0 r5), 11/7 (t1 r3), 5/3 (t2 r2), 8/5 (t3 r0) |
| `g2_tall` | `d=[2,R]`, `f1` pinned to (1,0), 3 slopes, `\|T\| ≤ 1`, cutoff `< 11/6` | 2R, 2R−1 | would log any hit ≤ 1.675 |
| `stacked` | `d=[2,2,2]` with `f1`,`f2` pinned to the 7/4 trapezoid; only the 4 interface labels free (5⁴ / 7⁴) | 8, 7, 6 | 13/8 at t=0 (needs r ≤ 5 on m = 8) |
| `rzero` | `r = 0` **and `T0 = ∅`** | — | **none — provably empty (F3)** |

**F3 in detail.**  `src/rzero.py:sweep` does `ok, _ = force(rows, n, set())`.  The
`max_r=0` parameter is never used and `T0` is never anything but empty.  P7 (cut
lemma at `A = V`, proved in the workbench and machine-checked on 515 objects) says
an object with `T` empty and no generators **cannot force a single vertex**.  So
the rzero search space contains no forcing object at all, by construction.  The
six rzero rows in workbench §7 — four of them marked "**yes**" complete, over
343 / 3,125 / 3,125 / 78,125 labellings — are a P7 regression test.  They should not be read as
coverage of anything.

**F4 in detail — the moduli.**  The stabiliser of a point in `PGL_2` is *sharply*
2-transitive on the rest, so exactly two slopes can be normalised and no more.  A
k-slope alphabet therefore has `k − 2` genuine moduli.  Every complete sweep in
the record fixes them:

| pool | slopes | moduli after normalisation | value tested |
|---|---|---|---|
| POOL3 | 0, ∞, 1 | 1 | 1 |
| POOL4 | + 2 | 2 | (1, 2) |
| POOL6 | + 3, 1/2 | 4 | (1, 2, 3, 1/2) |

For **Goal 2** this is not a limitation — the problem pins `X`.  For **Goal 1**,
`X` is free, so "no object on `d=[2,2,2]` over POOL4" is a statement about one
point of a 2-parameter family, not about 4-slope objects.  Nothing in the record
says this.  §5C measures whether the answer actually moves when a modulus moves.

---

## 4. Q4 — the next three computations, by information per CPU-hour

Ordered by (information gained) / (CPU-hours), with rates measured on this box.

### 4.1 The first *complete* Goal-1 sweep at n = 8  — ~6.3 CPU-hours

    cd rust && ./target/release/kakeya-search scan --tag n8_p4_t1 \
        --d 2x2x2 --pool 4 --max-t 1 --target 67/40 --threads 5

Measured cost, from a **uniform** MT19937 sample (not a product-order prefix):

    ./target/release/kakeya-search scan --tag n8_sample --d 2x2x2 --pool 4 \
        --max-t 1 --target 67/40 --limit 500 --seed 7 --threads 1
    RESULT {"tag": "n8_sample", ..., "scanned": 500, "total": 500,
            "best": null, "hits": 0, "seconds": 352.5}     [user 2m24.067s]

144 CPU-s / 500 tuples = **0.288 CPU-s per tuple**; the full space is
`5^7 = 78,125` tuples → **22,500 CPU-s = 6.25 CPU-hours**.  On 5 threads that is
a bit over an hour once the box is free.

Why it is worth the most: the record has **no** complete Goal-1 sweep at n = 8.
The two logged rows are product-order prefixes of 207/40,000 and 173/15,000, and
workbench §7 says of them "essentially untouched".  A 0-hit is the first real
n = 8 negative — and by the §3(a) table it means no 4-slope object on the
`2x2x2` box with `|T| ≤ 1` scores **13/8 or better**, which is a much stronger
statement than "≤ 1.675".  A hit is an Epoch answer outright.
(The 500-tuple sample above is already 0 hits over 0.64% of the space, uniformly
sampled — the first non-prefix evidence at n = 8.)

### 4.2 Complete `d=[2,4]` for Goal 2 over **all** `f1`  — ~1–2 CPU-hours

    cd rust && ./target/release/kakeya-search scan --tag g2_24_full \
        --d 2x4 --pool 3 --max-t 1 --target 20/11 --threads 4

`4^7 = 16,384` tuples, exactly 4× the `g2_tall 2x4` space (which pins `f1`).  The
budgets coincide: `floor(20·8/11) = 14 = floor(11·8/6)` at q = 8 and
`floor(20·7/11) = 12` at q = 7, so this is `g2_tall 2x4` generalised to every
level-1 label.  Cost anchor: a complete `g2_tall 2x4` measured here is 791.9 CPU-s
(4,096 tuples, 31,718 pairs), so the four-fold space is ~0.9 CPU-hours plus
whatever the non-`(1,0)` level-1 labels cost — call it 1–2 CPU-hours.
This is the smallest box where F5's pinning actually costs coverage *and* the box
is completable.  0 hits → **Goal 2 closed at n = 8 over three slopes with
|T| ≤ 1**, the first Goal-2 negative past the record's own n = 6.  A hit → an
improvement on 11/6, which Epoch calls "at least moderately interesting".

### 4.3 `g2_tall 2x5` to completion  — ≤ 14 CPU-hours (likely 4–10)

    cd rust && ./target/release/kakeya-search g2-tall --rows 5 --max-t 1 \
        --tlimit 86400 --threads 5

A complete run prints `"complete": true` with `walked = 65536` and
`pairs = 672719` (Fable's independent count; a different `pairs` means the prune
order drifted).  This finishes the one incomplete production run that is actually
finishable.  0 hits → the `f1 = (1,0)` half of the 2×5 ladder is clean, and the
natural follow-on is the `f1 = (1,1)` half (F5), obtainable as
`scan --d 2x5 --pool 3 --max-t 1 --target 20/11`, four times the cost.

**What NOT to run:** `g2_tall 2x6` to completion (~1,240 CPU-hours, §2.1) and any
further `cycles8 POOL6` work at `t ≤ 2` — that region is now settled twice, once
with Lemma C and once without.

**Zero-CPU item worth more than any of the three:** Route B, the symbolic gadget
sweep (`src/schemes.py`).  199 counting skeletons with `c ≤ 8` already have fixed
point in `(3/2, 1.675]`; the open half is *realisability*, which is reading and
algebra, not compute.  Every published improvement in this area came from that
route, not from object search.

---

## 5. Small computations run to settle the above

Scripts are in this directory.  All Python ran with `KAKEYA_PURE_PY=1` from `src/`.

### 5A. The Goal-2 label symmetry group (`lemmas_check.py`, part A)

Möbius maps realising each permutation of `{0, ∞, 1}`, tested for fixing `−1`:

```
  0 oo 1 ->   0 oo 1   -1 |->    -1   fixes -1: True
  0 oo 1 ->   0 1 oo   -1 |->   1/2   fixes -1: False
  0 oo 1 ->   oo 0 1   -1 |->    -1   fixes -1: True
  0 oo 1 ->   oo 1 0   -1 |->     2   fixes -1: False
  0 oo 1 ->   1 0 oo   -1 |->   1/2   fixes -1: False
  0 oo 1 ->   1 oo 0   -1 |->     2   fixes -1: False
  => usable Goal-2 label symmetry group has order 2
```

This is what makes F5 sharp: pinning `f1 = (1,0)` is WLOG only up to `0 ↔ ∞`.

### 5B. The 4-cycle floor PREDICTIONS §2.2 imports (`lemmas_check.py`, part B)

§2.2 cites the `n4_p6_t1` scan for "r ≥ 3 at t = 0 and r ≥ 2 at t = 1 for every
4-cycle".  That scan ran under a target budget of 3 (t = 0) and **1** (t = 1), so
it could never have *observed* |R| = 4 or 5 — the inference is correct but tightly
scoped.  Recomputed here with the budget opened to 5, over all 216 all-present
POOL6 label triples on `d=[2,2]`:

```
  t=0: |R| histogram {'>5': 6, 3: 120, 4: 90}   MINIMUM |R| = 3 -> 7/4 = 1.7500
  t=1: |R| histogram {2: 840, 3: 24}            MINIMUM |R| = 2 -> 6/3 = 2.0000
```

§2.2 confirmed, unbudgeted, and now good at every `t` — which is exactly what the
`t = 3` argument in §1.2 needed.

### 5C. Do the slope moduli matter? (`moduli_check.py`)

`moduli_check.py` re-runs two of the record's *complete* sweeps with the moduli
moved (`d=[2,2]` target 7/4 over four 6-slope alphabets; `d=[2,3]` target 9/5 over
`{0, ∞, s}` for eight values of the single Goal-1 modulus `s`).  **It did not
return inside this lens's CPU budget** — 13 min elapsed / 9.5 min CPU at ~55% of a
core on a six-way-contended box, with output buffered behind a pipe; it is left
running.  Do not treat its absence as a result.

A cheap, decisive slice of the same question *did* return.  At `n = 4` the
optimum is 7/4, i.e. no 4-cycle reaches `|R| ≤ 2` at `t = 0` (score 3/2).  Asking
exactly that question over all 216 all-present label triples, for POOL6 and for
four random 6-slope alphabets:

```
pool -> number of all-present triples achieving |R| <= 2 at t=0 (score <= 3/2)
  POOL6 (record)      [(1,0),(0,1),(1,1),(1,2),(1,3),(2,1)]     hits=0  [9.5s]
  random 6-slope #1   [(1,0),(0,1),(1,2),(4,5),(4,3),(1,-4)]    hits=0  [11.3s]
  random 6-slope #2   [(1,0),(0,1),(4,-5),(5,2),(1,1),(3,4)]    hits=0  [11.3s]
  random 6-slope #3   [(1,0),(0,1),(4,-5),(5,2),(2,-1),(1,-3)]  hits=0  [11.1s]
  random 6-slope #4   [(1,0),(0,1),(1,-2),(2,-1),(3,2),(1,-3)]  hits=0  [12.8s]
```

So the `n = 4` floor is **stable** under moving the moduli — which is reassuring
but is exactly the case where the kernel `K = ker(Q^{X'} → Q^2)` has the least
room to do anything.  It says nothing about `n = 8, 10, 12`, where the whole
mechanism (§1 of the workbench: "the gain comes entirely from the linear relations
among three or more slopes") lives.  **F4 stands: no run in the record varies a
modulus at any `n > 4`.**

---

## 6. Q5 — load-bearing but never verified

1. **The 3/2 barrier (F8).**  Workbench §6.4.1 names it —
   Katz, *Elementary proofs and the sums differences problem*, Collectanea Math.
   **57** (2006) 275–280, reference [5] of the Epoch write-up — and says "Not
   fetched this seat".  It still is not: `papers/` contains kt (math/0010069),
   newbounds (math/0102135), 1712.02108, 2011.07056, 2411.13395, 2511.15135 and
   `epoch-ak`, and nothing by Katz 2006.  Everything about how hard the search is
   rests on it: it is what turns "beat 1.675" at `q ≤ 12` into "land inside
   `(3/2, 5/3]`", and workbench §6.2 uses it to *reject* the naive corner scheme
   `(3,2,1,2)` whose fixed point is 1.4343.  In the formalism itself, all that is
   proved is `S ≥ 1` (P3) and `S ≥ 2` for two slopes (Theorem 2).  **Reading that
   paper is worth more than any CPU-hour listed in §4.**
2. **The Operation-1 suffix ambiguity (F2).**  Workbench §1 flags it and §6.4.5
   defers it: "Resolve … if a candidate ever depends on it.  Nothing here does."
   That is right for a *hit* — the matching-suffix reading is the weaker operation
   set, so an object valid under it is valid under either.  It is **wrong for a
   negative**: the permissive reading gives `(d_{i+1}…d_k)^2` edges per bundle for
   the same `m(G)`, i.e. strictly more objects at the same cost, so "no object
   found" under matching-suffix says nothing about the permissive space.  Every
   result the campaign has produced is a negative.  And the Rust binary cannot
   test the other reading at all: `grep -rc permissive rust/crates` = **0**.
3. **PREDICTIONS §2.3's case reduction** ("within budget the only live cases are
   t=0 r∈{4,5}, t=1 r=3, t=2 r=2, plus one-z-parallel t=0 r=5") is correct
   arithmetic **for the driver's `t ≤ 2`**, and carries the same silent `t = 3`
   gap as the driver (F1).
4. **PREDICTIONS §2.2's imported 4-cycle floor** — load-bearing for 95.7% of the
   cycles8 pairs, imported from a budgeted scan.  Now independently measured
   (§5B): it holds.
5. **The Chain remark** (workbench §4) is the one piece of design guidance the
   campaign produced, and `stacked` is its only test — over an interface of 4
   labels on a *single* skeleton (the 7/4 trapezoid doubled).  Confirming it there
   does not test the general claim, and no driver searches interleaved-forcing
   designs on any other block.
6. **`min_generators` correctness is a shared assumption**, and PREDICTIONS §2.2
   says so in as many words ("it is the same code the port replicates, so it is a
   shared assumption").  Every negative in the campaign — Python and Rust — is
   conditional on that one DFS being complete within its budget.  The port is
   bit-exact with it, which is a check of the port, not of the DFS.

---

## 7. Appendix — results that landed after the body was written

### 7.1 The 8-cycle cross-check finished (2026-09-06T20:46:00Z)

`logs/rust-targets.log`:

```
=== cycles8_8cycle RESTART 2026-09-06T19:02:26Z cmd: ks8run cycles8 --pool 6 \
    --target 67/40 --deg 2 --patterns 8cycle --threads 10 --tlimit 36000
=== cycles8_8cycle exit=0 2026-09-06T20:46:00Z
RESULT {"tag": "cycles8", "pool": 6, "best": null, "hits": 0, "tested": 81660, "patterns": [2, 3]}
=== 8CYCLE DONE (restart)
```

`tested = 81660` is the full predicted count, so this is a **complete**,
Lemma-C-free exhaustion of the two 8-cycle patterns at `t ≤ 2`, 0 hits.  It
independently confirms Fable's `cycle8_cheap` + `cycle8_r5` side computation
(which needed Lemma C as a prune).  It does **not** touch `t = 3` — see F1.
Note the binary that produced it, `ks8run`, is the 15:02 copy, which predates the
`checked_pow` rebuild; that fix is irrelevant to this run (81,660 pairs, no
overflow path), but the copy is not the audited `add55418…`.

### 7.2 `--deg` is vacuous except at 2 (F7)

```
$ kakeya-search cycles8 --pool 3 --target 67/40 --deg 1 --threads 1
0 presence patterns are 1-regular with m = 8
RESULT {"tag": "cycles8", "pool": 3, "best": null, "hits": 0, "tested": 0}
   (same for --deg 3 and --deg 4)
```

`G.m == n` is required before the degree test, and `sum(deg) = 2m = 2n`, so an
all-equal-degree graph must have `deg = 2`.  The flag cannot widen the search.

### 7.3 `g2_tall 2x4` completed here — the timing anchor

```
$ kakeya-search g2-tall --rows 4 --max-t 1 --tlimit 1200 --threads 2
RESULT {"tag": "g2_tall_2x4", "d": [2, 4], "pool": 3, "max_t": 1,
        "target": "<11/6", "best": null, "hits": 0, "complete": true,
        "seconds": 942.5, "walked": 4096, "total": 4096, "pairs": 31718}
real 15m42.569s   user 13m11.904s   sys 0m10.936s
```

`pairs = 31718` matches Fable's independent `count_pairs.py` figure exactly.
791.9 CPU-s / 31,718 pairs = **0.0250 CPU-s per pair** — the anchor used in §2.1
and §4.

---

## 8. Housekeeping

* No process was killed or signalled.  pid 13369 (the pure-Python cycles8 POOL3
  oracle) was alive at the start and at the end of this lens (51+ min CPU, still
  running, still writing to `refute/search/r3/out/C8.py.txt`).  pid 12158
  (`ks8run`) **finished on its own** at 20:46:00Z with exit 0 — see §7.1; it was
  not touched.
* Files written, all inside `rust/refute/science/r5/`: `FINDINGS.md`,
  `t3_check.py`, `lemmas_check.py`, `moduli_check.py`.  Nothing else on disk was
  modified.
* Left running deliberately: `moduli_check.py` (pid 92295).  Its output is
  buffered behind a pipe, so read it from the process's own stdout capture when
  it lands, or re-run it redirected to a file.


---
**Appended 2026-09-06 18:40 EDT (by the triaging session, not the lens):** `t3_check.py idx:0` was run in pure Python after this report was written: 46,656 graphs, 6,156 skipped by P4, **1,368,000 pairs, 0 hits**, 567.1 s (`t3_idx0_purepy.txt`). Section 1.2's component-split argument for pattern 0 is therefore confirmed by computation and no longer load-bearing. Both other t3_check runs were reproduced independently (13.6 s / 33.2 s, same counts).
