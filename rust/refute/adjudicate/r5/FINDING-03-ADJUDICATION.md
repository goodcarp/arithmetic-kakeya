# Adjudication of finding 3/10 (lens `hitpaths`)

Finding: "stacked's `for x in h[:5]` hit block cannot fire for POOL3/4/5/6;
only POOL8 is not excluded."  kind=record, severity=major.

**VERDICT: real = true.**  The finding is substantively correct and I could not
break it.  Two corrections to its wording, one of which STRENGTHENS it.

Artifact tested: `rust/target/release/kakeya-search`, sha256
`add554183aaa3d7cf1f2d468ba11e39926aea035853809811af4e6c40010fcf9`
(re-verified at 22:42 EDT this session).  All timings CONTENDED: load average
was 358 at 22:41 and 250 at 22:53 on 6 physical cores.

--------------------------------------------------------------------------
## 1. The repro reproduces, byte-for-byte on the content lines

    cd rust && ./target/release/kakeya-search stacked --pool 3 --max-t 0 --threads 4
    POOL3: best score over all interfaces = 7/4 (1.75)
       witness: interface labels=((0, 0), (0, 0), (0, 0), (0, 0)) m=8 r=6 t=0 T0=[]
       strictly-better-than-7/4 hits: 0   [43.1s]

(43.1 s at `--threads 4`; the lens reported 95.2 s at `--threads 1`.  Both
contended, neither is a benchmark.)  Saved: `st_p3_mt0.rs.txt`.

## 2. The hardcoded threshold: confirmed on both sides

    src/stacked.py:45                    if sc < Fraction(7, 4):
    src/stacked.py:46                        hits.append((sc, labs, m, gens, sorted(T0)))
    drivers/stacked.rs:121               if sc < Frac::new(7, 4) {

`--target` reaches only the budget (`src/stacked.py:29`
`budget = int(target*den) - m`; `stacked.rs:87` `cfg.target.mul_int_floor(den) - m`).
Confirmed.  NOTE the finding's line citations are stale by a few lines
(it says `stacked.py:47` and `stacked.rs:135`; the actual literals are at
`stacked.py:45` and `stacked.rs:121`).  Cosmetic, not substantive.

## 3. The pools do nest, on both sides, as a prefix chain

    src/search.py:35-39            POOL4 = POOL3 + [(1,2)] (written out)
                                   POOL5 = POOL4 + [(1,3)]
                                   POOL6 = POOL5 + [(2,1)]
                                   POOL8 = POOL6 + [(1,-2),(3,1)]
    graph.rs:14-18                 same five constants, same order

Prefix order matters: `min_generators`' DFS walks `cand` by increasing index, so
a prefix extension keeps every smaller-pool generator set enumerable in the
larger-pool run.  Both sides are prefix extensions.

## 4. The monotonicity lemma: audited site by site, holds

`pool` reaches `stacked.run` at exactly four places, and none of them can make a
bigger pool score worse:

| site | effect of growing the pool |
|---|---|
| `alphabet = [ZERO] + list(pool)` (interface labels) | strict superset of label tuples |
| `X = [ZERO] + list(pool)` -> `ConstructibleGraph(X, ...)` | **no effect on the score at all.**  `G.m` (kakeya.py:86-93) sums over `self.f` only; `edges()` (125-150) and `build_rows` read `f` and `d` only.  `X` is used only by `validate()`, which `stacked.run` never calls. |
| `local_requirement(G, idx, n, T0, pool)` | **`pool` is unused in the body** — it appears only in the signature (search.py:97-116).  Rust mirrors this: `w.local_req(n, *mask)` takes no pool. |
| `min_generators(..., pool, budget, mand)` | `cand` and `_dir_choices(existing, pool, 1)` grow monotonically; `_dir_choices(.., k>=2)` returns `[]` for every pool (P6); the branch-and-bound prunes on cardinality only.  So min r is non-increasing. |

Hence for a fixed `labs` (over the small alphabet), fixed `t`, fixed `T0`:
same `m`, same `den`, same `budget`, and r can only drop.  Score is monotone
non-increasing in the pool.  The complete POOL4 run therefore lower-bounds
POOL3, and the complete POOL6 run lower-bounds POOL5.

## 5. The recorded POOL4/POOL6 runs are complete BY CONSTRUCTION

`src/stacked.py` has **no `tlimit` parameter and no time check anywhere**
(`grep -n tlimit src/stacked.py` -> nothing).  `stacked.run` enumerates
`itertools.product(alphabet, repeat=4)` to exhaustion.  So `logs/stacked.log`
(POOL4 8268.5 s, POOL6 16959.8 s, both `best = 7/4`, `hits: 0`) cannot be a
truncated run.  And

    diff <(sed 's/\[[0-9.]*s\]/[Xs]/' logs/stacked.log) \
         <(cat logs/rust-stacked_pool4.log logs/rust-stacked_pool6.log | sed 's/\[[0-9.]*s\]/[Xs]/')
    -> IDENTICAL after masking elapsed

## 6. I tried to break it with `--target`.  It holds, and the arithmetic is tight

The finding says raising the target "can only admit solutions with MORE
generators".  That is right, and here is the exact statement, since `min_generators`
returns the MINIMUM r (so a bigger budget never lowers a score, it only lets
previously-`None` configurations report a higher one).  Any hit needs
`m + r < 7/4*den`; the 7/4 budget is `floor(7/4*den) - m`; for the three
reachable denominators:

    den=8:  hit <=> m+r <= 13 ;  budget = 14-m  -> r <= 13-m < budget   OK
    den=7:  hit <=> m+r <= 12 ;  budget = 12-m  -> r <= budget          OK
    den=6:  hit <=> m+r <= 10 ;  budget = 10-m  -> r <= budget          OK

So every sub-7/4 solution is already inside the shipped 7/4 budget: **no target
can expose a hit that the recorded runs missed.**  Measured, this session:

    stacked --pool 3 --max-t 0 --target 3/2 --threads 4
      -> best None (None) / "no witness found (the Python driver raises TypeError here)"
    stacked --pool 3 --max-t 0 --target 15/8 --threads 4
      -> best 7/4 (1.75), same all-ZERO witness, hits 0   [51.7s]

Files `st_p3_mt0_t32.rs.txt`, `st_p3_mt0_t158.rs.txt`.

## 7. CORRECTION THAT STRENGTHENS THE FINDING: the `max_t <= 2` caveat is removable

The finding scopes itself to `max_t <= 2` (the recorded runs' value), and both
CLIs accept a larger one (`main.rs` `--max-t` is a free integer;
`oracle_drivers.py stacked <pool> <max_t>`), so the scope looked necessary.
It is not.  For `d=[2,2,2]`, `G.m = 8 + (#nonzero level-3 labels) >= 8`
(kakeya.py:86-93: level 1 mult 4 x 1 pinned label, level 2 mult 2 x 2 pinned
labels, level 3 mult 1).  A hit needs `m + r < 7/4*(8-t)`:

    t = 3   -> m+r <= 8   -> m = 8 (all-ZERO interface) AND r = 0
    t >= 4  -> m+r < 7 <= m -> impossible, every pool, every target
    t = 8   -> den = 0, out of contract

`r = 0` means no generators, so the pool drops out entirely and ONE check
settles every pool.  `refute/adjudicate/r5/t3.py` (pure Python,
`KAKEYA_PURE_PY=1`) runs it:

    POOL3: all-ZERO interface m=8 rank(base_rows)=8; 3-subsets T0 that force with r=0: 0 / 56  -> no t=3 hit
    POOL4: ... 0 / 56  -> no t=3 hit
    POOL5: ... 0 / 56  -> no t=3 hit
    POOL6: ... 0 / 56  -> no t=3 hit
    POOL8: ... 0 / 56  -> no t=3 hit

So: **`hits` is empty for POOL3/4/5/6 at EVERY `max_t`, not just `max_t <= 2`**,
and POOL8 is open only at `t <= 2` (its `t >= 3` slice is closed by the same
check).  This makes the unqualified wording now on disk in PROGRESS.md correct.

## 8. Is the correction now on disk right?

`crates/kakeya-search/PROGRESS.md:147` reads:

    stacked: empty for POOL3-6 by pool monotonicity on the complete POOL4/6 runs

Accurate, and (per sec 7) its omission of the `max_t <= 2` qualifier is
justified — though it was justified by luck, not by an argument in the record.
The surrounding sentence "No configuration of these four drivers produces
hits > 0" is a shade broader than what is proved (stacked POOL8 at `t <= 2`
and g2_tall at `r >= 5` are open), but the parenthetical that follows it
scopes each driver explicitly, so a reader is not misled.  Suggested one-line
amendment: add "(all t: t>=3 forces m=8, r=0, and no 3-subset forces on the
edge rows alone; t>=4 needs m+r<7<=m); POOL8 open only at t<=2".

## 9. Severity

The lens filed this as `major`/`record`.  The substance is right, but the
consequence is a **coverage** statement, not a defect: Python and Rust agree,
and both are correct.  What it establishes is that the `hits > 0` branch of
`stacked` is not merely unexercised but unreachable over the whole pool range
the record runs, so `hits: 0` agreement is zero-information for that branch and
the branch can only ever be pinned at the formatter level (which r5-hitpaths
sec 4 then does).  That is worth recording; it is not a bug.  I would file it
**minor**, kind `record`.

## Files written (nothing outside `refute/adjudicate/r5/`)

    FINDING-03-ADJUDICATION.md   this file
    st_p3_mt0.rs.txt             the repro
    st_p3_mt0_t32.rs.txt         --target 3/2 (below threshold)
    st_p3_mt0_t158.rs.txt        --target 15/8 (above threshold)
    t3.py, t3.out.txt            the max_t caveat closure
    mono.py                      sampled per-config monotonicity test (pure Python)

No process was signalled at any point (no kill/pkill/killall/signal in this
session's command history).

## 10. Soundness note on the sec-7 closure

`t3.py` calls `force(base_rows, 8, set(T0))` with NO generator rows — exactly
`min_generators`' `extend(rows=base_rows, gens=[], start=0, T=set(T0), ...)`
entry point at r=0.  It is if anything MORE permissive than the driver: if
`local_requirement` returns `mt > 0` at that `(G, T0)` the driver would force
`r >= 1` and skip the r=0 branch entirely.  So 0/56 is an upper bound on what
the driver could find.  `rank(base_rows) = 8 >= den` at every `t`, so the P3
prune `den - rk > budget` never fires here and cannot be masking the case.

## 11. Artifact hashes as tested (this session)

    rust/target/release/kakeya-search   add554183aaa3d7cf1f2d468ba11e39926aea035853809811af4e6c40010fcf9
    src/fastcore_rs.abi3.so             03db7ae995fdda76eed5d7d72474f5b27141bc9b15814e89827250e35d21ed4b

    kakeya-search check --threads 2  ->  CHECK PASS (0 failed)   (14 PASS / 2 SKIP)

## 12. Status of `mono.py` (the sampled per-config monotonicity test)

`mono.py 0 32` (8 of the 256 POOL3 interfaces, t=0, POOL3 vs POOL4 vs POOL5 vs
POOL6, `KAKEYA_PURE_PY=1`) was launched at 22:43 EDT and had not finished after
14 min of a heavily contended machine (~30% of one core; pure-Python
`min_generators` over POOL6's 48 candidates is the cost).  It had printed **no
`BREAK-R` / `BREAK-OK` line** at that point -- it prints a break the moment it
finds one -- so the partial evidence is consistent with monotonicity, but it is
NOT a completed run and I am not claiming it as one.

The verdict does not rest on it.  Sec 4 settles the lemma by exhausting the
four places `pool` reaches the score, and sec 1/6/7 settle the conclusion
empirically from the audited binary and the complete recorded runs.
