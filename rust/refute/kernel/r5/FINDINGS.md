# refute/kernel/r5 — re-run of every existing kernel lens against the current artifacts, plus new cases

Verdict: **NOT REFUTED.** No in-contract failing input was found. 1,536,000+
differential comparisons over the shipped `.so`, zero value-level divergences on
any input both sides accept. Every divergence reproduced falls in a class that
is already on the disclosed list or already written up in
`rust/refute/search/r3/FINDINGS.md`.

Three reportable items, none of which refute the claim: a stale FAIL assertion
in the boundary suite (F1), no verdict/summary artifact for control or boundary
and no on-disk copy of the contract the lenses classify against (F2), and the
shipped `.so` predating the current `kakeya-core` source with nothing in the
tree recording that (F3).

All wall-clock numbers below are **contended** — pid 12158 (`ks8run`) held ~5 of
6 physical cores throughout, and pid 13369 (pure-Python `cycles8 3`) was live.
Neither was signalled. All Python runs used `/usr/bin/python3` (3.9.6).

---

## 0. Artifacts under test — recorded before anything ran

    $ shasum -a 256 src/fastcore_rs.abi3.so rust/target/release/kakeya-search
    03db7ae995fdda76eed5d7d72474f5b27141bc9b15814e89827250e35d21ed4b  src/fastcore_rs.abi3.so
    add554183aaa3d7cf1f2d468ba11e39926aea035853809811af4e6c40010fcf9  rust/target/release/kakeya-search

    $ stat -f "%N %Sm %z" src/fastcore_rs.abi3.so rust/target/release/kakeya-search
    src/fastcore_rs.abi3.so             Sep  4 16:10:50 2026   441904
    rust/target/release/kakeya-search   Sep  6 15:33:37 2026   844992

`kakeya-search` matches the sha in the task statement. The `.so` sha
(`03db7ae9…`) was not stated in the task; it is recorded here as the baseline.

A second `.so` exists in-tree and was used as a control (see F3):

    rust/refute/boundary/fresh/fastcore_rs.abi3.so
    04d848f8acec4716cafcf3479591cf6ffcd006534276407841c71a26d3193189   Sep 5 17:43:42 2026
    rust/refute/modular/fresh/fastcore_rs/fastcore_rs.abi3.so          (byte-identical to it)

**Kernel disclosure.** Every comparison in this report has pure Python on the
reference side: the reference is always `fastcore._force_py` / `fastcore._rank_py`
with `fastcore._INV.clear()` immediately before the call, verified live by
`boundary/t_wiring.py` ("py3.9 default: _force_py/_rank_py stay pure Python
PASS"). No comparison here ran the PyO3 kernel on both sides. Which `.so` each
process loaded was verified by printing `fastcore_rs.__file__` and hashing it
(scratchpad `whichso.py`), not assumed — see F3 for the two hashes it printed.

---

## 1. Inventory of the three existing kernel lenses

| dir | how it is run | verdict/summary file on disk? |
|---|---|---|
| `refute/modular/` | `README.md` lists 9 entry points, each `<script> shipped\|fresh [count] [seed]`; shared `harness.py` with a `classify()` contract filter | **partial** — 8 stored stdout baselines (`hand_shipped.txt`, `types_shipped.txt`, `fuzz_*.txt`, `ragged_shipped.txt`, `deep_*.txt`, `exhaustive.txt`, `threads.txt`) + a totals line in `README.md` ("633,484 comparisons, zero value-level divergences"). No FINDINGS.md. |
| `refute/control/` | `run_all.sh` (4 test scripts + 11 fuzz invocations); shared `harness.py` with **no** contract filter | **none** — no baselines, no summary, no FINDINGS.md. Its 19 `DIVERGE` lines are undifferentiated: in-contract and out-of-contract are printed identically. |
| `refute/boundary/` | no runner; 5 scripts run individually, `run_with_so.py <so> <script>` to retarget the `.so`; oracle is `orig_fastcore.py` (bytes 0:2976 of `src/fastcore.py`) | **none** — no baselines, no summary, no FINDINGS.md. |

None of the three ever wrote a verdict. That is F2 below.

---

## 2. modular — re-run against the shipped `.so`

    cd rust/refute/modular
    /usr/bin/python3 run_hand.py          shipped
    /usr/bin/python3 run_types.py         shipped
    /usr/bin/python3 exhaustive_small.py  shipped
    /usr/bin/python3 threads_check.py     shipped
    /usr/bin/python3 fuzz.py              shipped 50000 20260905      # stored seed
    /usr/bin/python3 fuzz.py              shipped 50000 5051977       # FRESH seed
    /usr/bin/python3 ragged_fuzz.py       shipped 25000 5051977       # FRESH seed
    /usr/bin/python3 deep_fuzz.py         shipped 25000 5051977       # FRESH seed

| script | cases | NEW divergences | vs stored baseline |
|---|---:|---:|---|
| `run_hand.py` | 1,447 | 0 value-level (48 known, all `p=0` + entry outside i64) | byte-identical except the timing column |
| `run_types.py` | 25 | 0 value-level | byte-identical except `<object at 0x…>` addresses |
| `exhaustive_small.py` | 297,919 | 0 | `[shipped/exhaustive-small] cases=297919  NEW divergences=0  known={}` — identical |
| `threads_check.py` | 64,000 | 0 | `threads=8 reps=20 items=400 calls=64000 mismatches=0` — identical |
| `fuzz.py` seed 20260905 | 50,000 | 0 | identical |
| `fuzz.py` seed 5051977 (new) | 50,000 | 0 | — |
| `ragged_fuzz.py` seed 5051977 (new) | 25,000 | 0 | — |
| `deep_fuzz.py` seed 5051977 (new) | 28,571 | 0 | — |

**modular total this run: 516,962 comparisons, 0 NEW value-level divergences.**
Raw output: `modular_rerun.txt`.

Note on `run_hand.py`'s exit code: it exits 1 and prints `NEW rank(...)` lines.
Every one is the same shape —

    rank([[2**63, 1], [1, 1]], p=0)   python: ZeroDivisionError   rust: OverflowError

i.e. two disclosed divergences colliding (`p` outside `1..2^32` **and** an entry
outside i64), so `classify()` cannot attribute it to a single class and files it
as NEW. `modular/minimal_repros.py` documents this as its case R6. Not a defect.

---

## 3. control — re-run against the shipped `.so`

    cd rust/refute/control
    /usr/bin/python3 -u test_control.py ; test_state.py ; test_dfs_aliasing.py ; test_threads.py
    for s in 20260905 1 2 7 4242 90210 ; do /usr/bin/python3 -u fuzz_control.py $s 25000 ; done
    for s in 11 12 13 5051977        ; do /usr/bin/python3 -u fuzz_ragged.py  $s 30000 ; done
    for s in 5 6 77 5051977          ; do /usr/bin/python3 -u fuzz_pivot.py   $s 12000 ; done

| script | checks | divergences reported |
|---|---:|---:|
| `test_control.py` | 103 | 11 |
| `test_state.py` | 6,022 | 0 |
| `test_dfs_aliasing.py` | 805 | 1 |
| `test_threads.py` | 192,008 | 7 |
| `fuzz_control.py` × 6 seeds (3 already stored, `90210` fresh) | 300,000 | 0 |
| `fuzz_ragged.py` × 4 seeds (`5051977` fresh) | 240,000 | 0 |
| `fuzz_pivot.py` × 4 seeds (`5051977` fresh) | 144,000 | 0 |

**control total this run: 882,938 checks, 19 divergences, 0 of them in-contract.**
Raw output: `control_tests.txt`, `control_fuzz1.txt`, `control_fuzz2.txt`.

The 19, classified (control's own harness does not classify — F2):

* 3 × rows passed as a **generator / `iter(list)`** to `force`: Python consumes it
  in round 1 and sees an empty `rows` in round 2, so it returns `(False, {0})`;
  Rust materialises once and returns `(True, {0,1})`. Both succeed, different
  answers. Already written up in `search/r3/FINDINGS.md` lines 26–27.
* 9 × **`rank` on an empty non-list iterable** (`iter([])`, a genexp, `zip([],[])`,
  `filter`, `map`, `reversed`, a truthy-but-empty object): Python's
  `if not rows` is False for an iterator, so it reaches `len(B[0])` and raises
  `IndexError`; Rust returns `0`. Same r3 write-up.
* 5 × **non-int or out-of-i64 entry in a column Python never reads** (trailing
  `str`, `float`, `None`, `1<<70`): Python's per-round column selection never
  touches it and succeeds; Rust coerces the whole row up front and raises
  `TypeError` / `OverflowError`. Disclosed class D5/D6 and D1.
* 1 × `force([], n=2**20+1, T0=range(n))`: Python short-circuits on
  `len(set(T0)) >= n` and returns an 8.3 MB set; Rust raises `ValueError`.
  Disclosed class D4 (`n > 2**20`).
* 1 × `force: bad entry in a row, IndexError comes first in py`: both raise,
  different type (`IndexError` vs `OverflowError`) — eager-vs-lazy coercion
  order, disclosed class D1.

No driver in `src/` passes rows as anything but a list of lists of small ints
(`t_wiring.py`'s call-site census: the only tests that reach `fastcore` at all
are `test_cut_lemma.py` 30,000 calls, `test_p6_swap.py` 60,419,
`test_two_slope_theorem.py` 4,000, all via `build_rows`).

---

## 4. boundary — re-run against the shipped `.so`

    cd rust/refute/boundary
    /usr/bin/python3 -u t_wiring.py ; t_coerce.py ; t_msgs.py ; t_thread.py
    SEED=424242 N=20000 /usr/bin/python3 -u t_scratch.py
    SEED=5051977 N=20000 /usr/bin/python3 -u t_scratch.py     # FRESH seed

| script | result |
|---|---|
| `t_wiring.py` | 8 PASS, **1 FAIL** (stale — see F1), 10 INFO, exit 1 |
| `t_coerce.py` | 82 cases, 47 agree, 35 diverge, exit 1 — all 35 are float/`__index__`/numpy entries, `p` outside `1..2^32`, entries outside i64, `n=2**63`, generator rows. Disclosed classes D1/D2/D3/D4/D5/D6. |
| `t_msgs.py` | diff-count 3 (`T0` float, `T0` str, and one TYPE-ONLY message difference on a `str` entry); the 4 exception **messages** that matter (`IndexError` "list index out of range", `ZeroDivisionError` "integer division or modulo by zero", both for `force` and `rank`) are byte-identical. exit 0 |
| `t_thread.py` | **22 PASS, 0 FAIL**, exit 0 — 4,000 single-thread instances, 8 threads × 6,000 force+rank, re-entrancy, no input mutation, fresh returned set, real `int`/`bool`/`set` types, keyword binding, arity errors |
| `t_scratch.py` seed 424242 | 40,000 checks, **0 mismatches** |
| `t_scratch.py` seed 5051977 (new) | 40,000 checks, **0 mismatches** |

Raw output: `boundary_run.txt`, `boundary_thread.txt`, `boundary_scratch.txt`.

One `t_coerce` line is worth naming because it *reads* as a divergence and is
not one: `force T0={True}` → `py=(True, {True, 0})`, `rs=(True, {0, 1})`. In
Python `{True, 0} == {1, 0}`; the difference is which object is in the set, not
its value. Both my new harnesses and `modular/harness.py` normalise with
`int(x)`; `t_coerce` compares reprs and so flags it.

---

## 5. difftest, the 119 traps, the 16 VERIFIED cases

    $ cd rust && /usr/bin/python3 -u difftest.py
    edge cases:                57 checks, 0 mismatches so far
    random sweep:           44349 checks (20000 instances)
    ragged/short rows:       4000 checks
    real build_rows:         6000 checks
    total checks:           54406
    mismatches:                 0
    expected divergences:       1 (i64 boundary, S1 sec 5.4)
    elapsed:               84.0s

Matches the claimed 54,406 / 0 exactly. Raw: `difftest.txt`.

    $ cd rust/refute/search/r3 && /usr/bin/python3 -u run_traps.py ../../../../adversary-fable/traps.json
    PASS=91 FAIL=18 SKIP=10 TOTAL=119

Raw: `traps119.txt`. All 18 FAILs are disclosed classes — 10 × `p` outside
`1..2^32` (Mersenne-61, `2^32+15`, negative `p`), 3 × entry outside i64,
1 × float entries, 1 × `rows=None` short-circuit, 1 × generator rows,
1 × `rank(iter([]))`, 1 × `force([],1,[True])` (`{True}` vs `{1}` — equal as
sets of ints), and `c02_cache_poison_force`, which "fails" only because the
runner clears `_INV` and so gets the *unpoisoned* Python answer that the trap's
`expected_repr` deliberately does not record. The 10 SKIPs are the `_inv`
traps: `fastcore_rs` exposes no `_inv`.

The 16 cases in `adversary-external/VERIFIED.md` were transcribed into
`verified16.json` and run through the same runner:

    $ /usr/bin/python3 -u .../run_traps.py verified16.json
    PASS=16 FAIL=0 SKIP=1 TOTAL=17

(The SKIP is `_inv(0,5)`, which has no Rust counterpart.) Raw:
`verified16_out.txt`. All 16 agree with `VERIFIED.md`'s stated Python result
**and** with the Rust — including the two that most reviewers get wrong,
`rank([[2,0]], p=4) == 1` (zero Fermat inverse advances `rk` anyway) and
`rank([[2147483647]]) == 0`.

---

## 6. NEW: 77 hand cases the three lenses did not target

`k5_hand.py` (53 cases) and `k5_short_rows.py` (24 cases). Both compare on
**value** (`int(x)`, sorted), so `{True}` and `{1}` are the same answer.

    $ cd rust/refute/kernel/r5
    $ /usr/bin/python3 -u k5_hand.py        # cases=53  divergences=0
    $ /usr/bin/python3 -u k5_short_rows.py  # cases=24  divergences=0

What each block attacks, and why the existing lenses missed it:

* **A (9) — greedy-choice ordering across rounds.** `force` takes the *smallest*
  `j` in `U` whose `delta_v` lies in the span, then redoes the whole reduction
  with that `j` removed. A port that picked a different qualifying `j` would
  still return `ok=True` but a different `T`, and a different **partial** `T` on
  failure. The suites fuzz random rows, which rarely produce two qualifying `j`
  in one round; these are constructed so the choice is load-bearing.
  Agreed on all 9, including the three-round cascade `A6` → `(False, {0,1,3})`
  and `A9` (a row that goes zero only on the *unforced* coordinates in round 2
  and is therefore dropped) → `(False, {0})`.
* **B (8) — composite `p` with a zero Fermat inverse.** `_inv(2,4)=pow(2,2,4)=0`,
  so the pivot row is multiplied to all zeros, `rk` still increments and the
  column is still appended to `piv`, leaving rows below with a live nonzero in a
  consumed pivot column. `p ∈ {4,6,8,9}` in both `rank` and `force`. Agreed on
  all 8.
* **C (9) — `p=1` and `p=2`.** Under `p=1` every entry reduces to 0 so no pivot
  is ever taken and `_inv` is never reached; under `p=2`, `p-1 == 1` so the test
  vector is `e_a + e_b`, not `e_a - e_b`. `modular/fuzz.py`'s modulus list
  contains 1 and 2 but its entry distribution rarely lands on the shapes where
  those two collapse. Agreed on all 9.
* **D (10) — degenerate `rank` rows.** `[[]]`, `[[],[]]`, `[[],[1,2]]` (width is
  taken from row 0 only), `[[1,2],[]]`, `[]`, all-zero 5×5, `rk >= nB` early
  exit, `[[P,P]]`, duplicate rows, 9×2. Agreed on all 10.
* **E (7) — out-of-range and negative `T0`.** `T = set(T0)` and the loop guard is
  `len(T) < n`, so negatives and values `>= n` inflate the count and can
  short-circuit with a `T` that does not contain `0..n-1`. `force([], 3, [-1,-2,-3])`
  → `(True, {-3,-2,-1})` on both sides. Agreed on all 7.
* **F (6) — warm-start monotonicity.** Cold, warm from `{0}`, `{0,1}`, full, and
  re-feeding the partial `T` from a *failed* call. Agreed on all 6.
* **G (4) — `n` at the Rust `2**20` clamp.** `n = 2**20` and `2**20 - 1` with
  `T0 = range(n)` both short-circuit identically on both sides (the disclosed D4
  ValueError starts at `2**20 + 1`, which `control/test_dfs_aliasing.py`
  already covers); plus a 4096-wide oversized row. Agreed on all 4.
* **H (12) — short rows masked by `T0`.** This is the sharpest new probe. `force`
  builds `U` from the *unforced* coordinates only and indexes `r[2*j]`,
  `r[2*j+1]` for `j ∈ U`, so a row shorter than `2n` is perfectly legal provided
  `T0` covers the tail. A port that validated `len(row) >= 2*n` up front would
  raise where Python succeeds. It does not:
  `force([[1,-1]], 2, [1])` → `(True, {0,1})` both sides;
  `force([[1,-1]], 2, [0])` → `IndexError` both sides;
  `force([[]], 1, [0])` → `(True, {0})` both sides;
  `force([[0,0,1,-1],[9,9]], 2, [1])` → `(False, {1})` both sides.
  All 12 agree, including the round-2 case `H11` where the short tail only
  becomes visible after the first coordinate is forced.
* **J (12) — `rank`'s `zip` truncation.** The elimination is
  `[(a - fac*b) % p for a, b in zip(B[i], pr)]`, and `zip` **truncates**: a short
  trailing row silently shrinks to its own length instead of raising, and only
  raises later if a pivot column past that length is reached. So
  `rank([[1,2,3],[1,2]])` raises `IndexError` but `rank([[1,2,3],[1,3]])`
  returns `2`, and `rank([[1,1],[2,2,2],[0,0,5]])` returns `1`. All 12 agree,
  including the `p=4` and `p=7` variants.

Raw output: `k5_hand_out.txt` (truncated to 160 columns — case G1 prints a
2^20-element tuple), `k5_short_rows_out.txt`.

---

## 7. NEW: fuzz with fresh seeds, and a warm-start chain

### 7a. `k5_fuzz.py` — 20,000 instances × 3 fresh seeds

Bias: 22 composite moduli each of which has a residue with `pow(a,p-2,p) == 0`;
entries concentrated on multiples of the small factors of `p` and on
`{0, ±1, p-1, p, p+1}`; `T0` drawn out of range 45% of the time.

    $ /usr/bin/python3 -u k5_fuzz.py 20000 51977
    k5_fuzz seed=51977 instances=20000 checks=40000 divergences=0
    $ /usr/bin/python3 -u k5_fuzz.py 20000 887788
    k5_fuzz seed=887788 instances=20000 checks=40000 divergences=0
    $ /usr/bin/python3 -u k5_fuzz.py 20000 20260906
    k5_fuzz seed=20260906 instances=20000 checks=40000 divergences=0

**120,000 checks, 0 divergences.** Raw: `k5_fuzz_out.txt`, `k5_fuzz_more.txt`.

### 7b. `k5_warmchain.py` — the production call pattern, compared step by step

Gap closed: every prior lens compares **single** `force` calls. The drivers call
`force` repeatedly on a growing `rows`, feeding the previous `T` back in. Here
each side is fed **its own** previous `T`, so a single-step drift compounds
instead of being reset, and a `rank` on the same rows is interleaved between
every pair of `force` calls to force reuse of the shared `thread_local` row
buffer between the two entry points.

    $ /usr/bin/python3 -u k5_warmchain.py 1500 51977
    k5_warmchain seed=51977 chains=1500 steps=11992 mismatches=0

Instances are real `ConstructibleGraph` / `build_rows` objects over the 8-element
slope pool, dimension vectors up to `[2,2,2,2]`. Raw: `k5_warmchain_out.txt`.

---

## 8. The other half of the claim: the search binary

    $ cd rust && ./target/release/kakeya-search check --threads 1
    ... 14 PASS lines ...
    SKIP ladder: pure sympy, no force/rank call -- not ported (contract sec 2.8)
    SKIP schemes: pure sympy, no force/rank call -- not ported (contract sec 2.8)
    CHECK PASS (0 failed)
    real 1m17.683s   (contended)

14 PASS / 2 SKIP / 0 FAIL at `--threads 1`, as claimed. Raw: `search_check_t1.txt`.
I did not re-run the `--threads 12` variant, `cargo test`, or the search-level
driver comparisons — those are the `search` lens's ground, and re-running them
under contention would only have produced worse wall-clock numbers than r3/r4
already recorded.

---

## Findings

### F1 (minor, housekeeping) — `boundary/t_wiring.py` exits 1 on an assertion that documents a *fixed* defect

    $ cd rust/refute/boundary && /usr/bin/python3 -u t_wiring.py ; echo $?
    ...
    FAIL  a broken fastcore_rs degrades to pure Python with NO warning and exit 0
          rc=0 stderr='fastcore: Rust kernel unavailable (simulated broken .so); using pure Python'
    FAILS: ['a broken fastcore_rs degrades to pure Python with NO warning and exit 0']
    1

`t_wiring.py:96-98` asserts `r.stderr.strip() == ""`. That predicate encoded the
*old* silent-fallback behaviour as the expected one. `src/fastcore.py` was since
repaired (its own comment: "Audit C6 (2026-09-06): never fall back silently — a
run labelled Rust must not quietly be Python"), so the warning is now emitted and
the assertion inverts. The boundary suite therefore reports FAIL and exits 1 for
a defect that no longer exists, and would keep doing so on every future run.

Report, do not patch (per the ground rules): the fix is to flip that predicate to
`"Rust kernel unavailable" in r.stderr`. **This does not affect the claim** — the
artifact is right and the test is stale. It matters because a future orchestrator
reading `exit=1` from the boundary suite will read it as a live failure.

### F2 (minor) — control and boundary produce no verdict, and the contract they classify against is not on disk

`refute/control/` and `refute/boundary/` have no baseline files, no summary, no
FINDINGS.md. `control/harness.py` has no contract filter at all, so its 19
`DIVERGE` lines print identically whether the input is a list of small ints or a
generator of numpy floats — the suite cannot say "0 in-contract failures", which
is presumably why it never returned a verdict. Only `modular/` has both a
`classify()` filter and stored baselines.

Relatedly: the D1–D6 sanctioned-divergence list that all three suites cite as
"S1 contract sec 5.4" exists nowhere in the target tree. `grep -rn "5.4"` over
`*.md` finds only lenses citing it, never the document. The nearest on-disk
enumeration is the `classify()` function in `modular/harness.py:80-100` plus
`modular/README.md`. A reader who has only the repository cannot check any
lens's KNOWN/NEW split against a written contract.

### F3 (minor) — the shipped `.so` is older than the `kakeya-core` source it is built from; no drift found, nothing records this

    src/fastcore_rs.abi3.so           Sep  4 16:10:50 2026   sha 03db7ae9…
    rust/crates/fastcore-rs/src/lib.rs Sep  4 16:10:26 2026
    rust/crates/kakeya-core/src/lib.rs Sep  5 17:32:04 2026   <-- 25 h newer than the .so
    rust/crates/kakeya-core/src/tests.rs Sep  5 17:32:04 2026

`fastcore-rs` depends on `kakeya-core` (`use kakeya_core::{self as core, ForceScratch, KErr}`),
so the shipped `.so` is not a build of the current crate tree. Nothing in
`PROGRESS.md` or the refute tree records the `.so`'s sha or that gap; the task
statement pins the `kakeya-search` sha but not the `.so`'s.

I tested for behavioural drift rather than assuming it. `refute/boundary/fresh/fastcore_rs.abi3.so`
(`04d848f8…`, built 2026-09-05 17:43, i.e. **after** the `kakeya-core` edit) was
loaded via `boundary/run_with_so.py` and re-run against my new material:

    $ /usr/bin/python3 -u ../../boundary/run_with_so.py ../../boundary/fresh/fastcore_rs.abi3.so k5_hand.py
    cases=53  divergences=0
    $ /usr/bin/python3 -u ../../boundary/run_with_so.py ../../boundary/fresh/fastcore_rs.abi3.so k5_fuzz.py
    k5_fuzz seed=51977 instances=20000 checks=40000 divergences=0

Shim check (required by the ground rules, since `run_with_so.py` preloads
`sys.modules["fastcore_rs"]` and my scripts then `import fastcore_rs`): I printed
`fastcore_rs.__file__` and hashed it under both invocations, and got
`03db7ae9…` for the plain run and `04d848f8…` for the retargeted run. The
retarget is real, not a no-op.

So: **no behavioural drift between the shipped `.so` and a build of the current
source, over 40,053 checks.** The finding is bookkeeping only — the `.so`'s
provenance is not written down anywhere and its sha is not pinned.

---

## Totals for this run

| lens | comparisons | value-level divergences on inputs both sides accept |
|---|---:|---:|
| modular (8 scripts, 3 fresh seeds) | 516,962 | 0 |
| control (4 tests + 14 fuzz runs, 3 fresh seeds) | 882,938 | 0 in-contract (19 out-of-contract, all disclosed) |
| boundary (5 scripts, 1 fresh seed) | ~80,200 | 0 in-contract (38 out-of-contract, all disclosed) |
| `rust/difftest.py` | 54,406 | 0 |
| `adversary-fable/traps.json` | 119 | 0 in-contract (18 out-of-contract, all disclosed) |
| `adversary-external/VERIFIED.md` | 16 | 0 |
| **new** `k5_hand.py` + `k5_short_rows.py` | 77 | 0 |
| **new** `k5_fuzz.py` × 3 fresh seeds | 120,000 | 0 |
| **new** `k5_warmchain.py` | 11,992 chain steps | 0 |
| `kakeya-search check --threads 1` | 16 fixtures | 14 PASS / 2 SKIP / 0 FAIL |
| | **≈1,666,700** | **0** |

`refuted = false`. No in-contract failing input was produced. The three
divergence directions I looked hardest for and did not find — a different greedy
`j` in a multi-round `force`, a mishandled zero Fermat inverse under composite
`p`, and eager row-length validation breaking the `T0`-masked short-row case —
are all reproduced correctly by the shipped `.so`.

## Files in this directory

| file | what it is |
|---|---|
| `FINDINGS.md` | this report |
| `k5_hand.py` / `k5_hand_out.txt` | 53 new hand cases (blocks A–G) |
| `k5_short_rows.py` / `k5_short_rows_out.txt` | 24 new hand cases (blocks H, J) |
| `k5_fuzz.py` / `k5_fuzz_out.txt` / `k5_fuzz_more.txt` | 20k fuzz, seeds 51977 / 887788 / 20260906, plus the fresh-`.so` control |
| `k5_warmchain.py` / `k5_warmchain_out.txt` | warm-start chain on real `build_rows` instances |
| `verified16.json` / `verified16_out.txt` | the 16 `VERIFIED.md` cases as trap JSON, and the run |
| `traps119.txt` | the 119-trap run |
| `difftest.txt` | `rust/difftest.py` |
| `modular_rerun.txt` | modular fuzz re-runs |
| `control_tests.txt`, `control_fuzz1.txt`, `control_fuzz2.txt` | control suite |
| `boundary_run.txt`, `boundary_thread.txt`, `boundary_scratch.txt` | boundary suite |
| `search_check_t1.txt` | `kakeya-search check --threads 1` |

---

## Appendix — process-hygiene note (2026-09-06 16:56)

I ran no `kill`, `pkill`, `killall` or any signal-sending command at any point.

At 16:56, after all my work was done, I checked the two protected jobs:

    $ ps -p 13369 -o pid,etime,comm=
    13369 01:45:46 .../Python   (oracle_drivers.py cycles8 3 — ALIVE)

    $ ps -p 12158 -o pid,etime,comm=
      PID ELAPSED                (no row)

    $ ps aux | grep ks8run | grep -v grep
      (no match)

pid 12158 (`ks8run`) was **not present** at that check. I have no evidence about
when or why it left — the only command I ever aimed at it was `ps -p`. Recording
it here because the task named it as top priority and a later reader will want
to know it was already gone by 16:56 rather than assume this lens ended it.

The same `ps aux` shows nine other kakeya jobs running concurrently under sibling
refuter/improve lenses (`cycles8 --pool 3 --threads 2`, `g2-tall --rows 4`, two
`scan`s, a `stacked`, a `check`, `moduli_check.py`, `scan_seed.py`, plus a
`cargo build` in `improve/perf`). Every wall-clock number in this report was
measured against that load and is an upper bound, not a benchmark.
