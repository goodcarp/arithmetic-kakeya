# r5 — EXTERNAL lens, decorrelated. 2026-09-06

Artifacts under test (unchanged by this pass; nothing outside
`rust/refute/external/r5/` was written):

    rust/target/release/kakeya-search
      sha256 add554183aaa3d7cf1f2d468ba11e39926aea035853809811af4e6c40010fcf9  (re-measured here)
    src/fastcore_rs.abi3.so
    /usr/bin/python3 3.9.6, cwd src, KAKEYA_PURE_PY=1 for every Python driver run below

Machine contended throughout: pid 12158 (`ks8run cycles8 --pool 6 --patterns 8cycle
--threads 10`) and pid 13369 (pure-Python `oracle_drivers.py cycles8 3`) were both
live and both were still live at the end of this pass. All wall-clock numbers here
are contended and are not comparable to the bench table in PROGRESS.md.

Both external sockets were asked, both answered, and every claim either
reproduced or is listed under "refuted external claims".

  - antigravity-cli (Gemini 3.8 Flash): 15 kernel claims (`prompt_kernel.txt` ->
    `anti_kernel.out`), 12 engine/determinism claims (`prompt_engine.txt` ->
    `anti_engine.out`).
  - grok-cli: 15 kernel claims (`grok_kernel.out`, 490 s). A second, shorter kernel prompt to grok
    was retried once and failed with `socket-failure grok-cli -- timeout 590s`
    (`grok_short.out`); grok was therefore not asked the engine question.

---

## FINDINGS

### F1 (CONFIRMED, from grok-cli claim 11 + own follow-up). `fastcore_rs.force` reads a row by ITERATION where the Python reads it by SUBSCRIPT — silent wrong value, no exception

The Python `force` does `a = r[2*j] % p` / `b = r[2*j+1] % p`: it **subscripts**
each row. The PyO3 boundary's `fill_row` (fastcore-rs/src/lib.rs) casts to
`PyList`/`PyTuple` and otherwise calls `try_iter()`: it **iterates**. For any row
object whose iteration order is not its `__getitem__` order the two build
different matrices, and both return normally with different answers.

Repro (`t_grok_claims.py`, case G11 / R5; `t_rev2.py` for the list witness):

    cd src && /usr/bin/python3 ../rust/refute/external/r5/t_grok_claims.py

    DIFF G11 force([dict row], 1, [], P)   py=('ok', True, [0])   rs=('ok', False, [])
         # rows = [{0: 1, 1: 2147483646}], n=1, T0=[], p=2147483647
         # Python: r[0]=1, r[1]=p-1  -> the row IS delta_0 (x) (1,-1) -> forces
         # Rust:   iterates the dict's KEYS -> row (0,1) -> does not force
    SAME M1  rank([dict row], P)           py=('ok', 1)           rs=('ok', 1)
         # rank is NOT affected: Python's rank also iterates ([x % p for x in r])

Second witness, this one an object for which `isinstance(row, list)` is `True`,
i.e. inside the boundary's own declared tolerance ("any sequence of sequences
for rows", fastcore-rs/src/lib.rs module doc):

    cd src && /usr/bin/python3 ../rust/refute/external/r5/t_rev2.py
    row (raw storage) = [1, 2147483646, 0, 0]  isinstance(row, list) = True
    py: ('ok', False, [1])
    rs: ('ok', False, [0])
    -> *** DIFF ***

Severity: **minor**. No call site in the tree can reach it — `build_rows`
(src/kakeya.py) returns a `list` of `list`s of plain `int`s, and search.py passes
`rows + [gen_row(...)]`, so every row that any driver hands to `force` is a plain
list. Nothing in the record needs retracting. What is wrong is the *scope* of the
bit-exactness claim and of the module docstring: `force` is bit-exact for plain
lists/tuples of ints, not for "any sequence of sequences", and the failure mode on
the wider domain is a silent wrong boolean rather than an exception. The one-line
fix, if it is wanted, is for `fill_row` to use the mapping/sequence `__getitem__`
protocol in `force` (leaving `rank` on iteration, which is what Python does).

### F2 (CONFIRMED, from antigravity-cli claims 1-4, all four exactly as predicted). One-shot iterables as `rows`

Python's `force` re-iterates `rows` once per forcing round (the `for r in rows`
inside `while len(T) < n`); the Rust boundary materialises `rows` once. Python's
`rank` evaluates `len(B[0])` on an empty extraction. Repro `t_iter_claims.py`:

    cd src && /usr/bin/python3 ../rust/refute/external/r5/t_iter_claims.py

    A1 rank((r for r in []), 5)                       py=IndexError        rs=0
    A2 rank(iter([]), 5)                              py=IndexError        rs=0
    A3 force(gen [[1,2,0,0],[0,0,1,2]], 2, [], 3)     py=(False,{0})       rs=(True,{0,1})
    A4 force(iter [[1,-1,0,0],[0,0,1,-1]], 2, [], 5)  py=(False,{0})       rs=(True,{0,1})
    C3/C4 (same data as plain lists)                  SAME
    X1 force([<generator row>], 1, [], 5)   py=TypeError('generator' object is not
                                            subscriptable)  rs=(True,{0})   [own probe]

Severity: **note**. Same class as F1 and same driver-level unreachability. A3/A4
are the value-vs-value cases; A1/A2/X1 are exception-vs-value.

### F3 (CONFIRMED, own finding, no external claim). `kakeya-search scan --tlimit 0` stops after one item; `scan1.py` with tlimit 0 runs to completion

`search.scan_dims` line 209 guards with `if tlimit and time.time() - t0 > tlimit`.
`0` is falsy in Python, so `tlimit=0` means *no limit*. The Rust parses `--tlimit 0`
into `Some(0.0)` and `Stop::should_stop` treats it as an already-expired deadline.

    cd src && KAKEYA_PURE_PY=1 /usr/bin/python3 scan1.py tl0 2 3 1 2 - 0
    RESULT {"tag":"tl0", ... "scanned": 4, "total": 4, "best": "2", "hits": 6, "complete": true, ...}

    rust/target/release/kakeya-search scan --tag tl0 --d 2 --pool 3 --max-t 1 \
        --target 2 --tlimit 0 --threads 1
    RESULT {"tag":"tl0", ... "scanned": 1, "total": 4, "best": null, "hits": 0, "complete": false, ...}

    (control) same Rust command without --tlimit  -> matches Python exactly.
    (control) --tlimit -1 / tlimit=-1: BOTH scanned 1, complete false -> SAME.

Files: `tl0.py.txt`, `tl0.rs.txt`. This is **scan-only**: `rzero.sweep`,
`cycles8.main`, `g2_tall.run` and `stacked.run` all use a bare
`if time.time() - t0 > tlimit`, so for those drivers `tlimit = 0` stops immediately
on both sides and the Rust is right.

Severity: **minor**. It is an in-contract CLI input (`--tlimit` is documented in the
usage text with no stated lower bound) on which the binary does not reproduce the
Python driver. Not a shim artefact: `tlimit` is a real positional argument of
`scan1.py` (argv[7]) — nothing was parameterised.

---

## REFUTED EXTERNAL CLAIMS (tested, did not hold)

| claim | source | verdict |
|---|---|---|
| Merged::absorb keeps a stale `bestobj` when a better score arrives with `witness: None` | anti-engine 4 | **REFUTED as live.** Every driver is uniform: scan.rs:118, rzero.rs:92, cycles8.rs:269 always push `witness: None`; g2_tall.rs:135 and stacked.rs:112 always push `Some`. No driver mixes them, so the `if imp.witness.is_some()` guard never fires on a mixed stream. Latent only. |
| `Frac::mul_int_floor` uses `div_euclid` (floor) where Python `int()` truncates toward zero, so negative targets diverge | anti-engine 6 | **Arithmetic difference real, effect REFUTED.** `int(Fraction(-1,3)*4) = -1` vs `(-1*4).div_euclid(3) = -2`. But every negative `budget` is pruned by `if budget < 0: continue` and `m >= 0 > int(target*n)` prunes every label either way. Measured: `--target -1/3` and `--target 0` on `2x2 pool 3 max-t 1`, Python vs Rust RESULT lines **identical**. |
| SipHash / `RandomState` iteration order leaks into tie-breaks or `gens` ordering | anti-engine 12 | **REFUTED.** `grep -rn "HashMap\|HashSet\|RandomState"` over `crates/{kakeya-core,fastcore-rs,kakeya-search}/src` returns exactly three lines, all `main.rs` CLI-option parsing; the map is only ever `get`, never iterated (`grep "opts\.\(iter\|keys\|values\|into_iter\)"` -> none). |
| Empty alphabet -> `randbelow(0)` infinite loop / `decode` divide-by-zero | anti-engine 7, 9 | **REFUTED (unreachable).** `alphabet_of` is `[ZERO] + pool`, length >= 1 for every pool. |
| `((ci+1)*cs)` overflows u64 near `total = u64::MAX` and silently skips the last chunk | anti-engine 5 | **REFUTED (unreachable).** `total = |alphabet|^nslots` and `checked_pow` (audit C6) refuses anything exceeding u64; the largest reachable totals (e.g. 9^20 = 1.216e19) are ~6e18 below `u64::MAX - 4096`. `--limit` is a `usize` count. |
| n >= 64 -> `1u64 << j` corrupts the vertex mask | anti-engine 3 | Not new: already recorded as `refute/search/shift/shift.rs` in COMMANDS.md sec 7. Also unreachable through the CLI now — any box with 65+ vertices has `|alphabet|^nslots` over u64 and is refused by the C6 `checked_pow`. |
| `--tlimit` makes thread counts disagree; progress lines buffer under `--tlimit`; decimal `--target` rejected; `max_t = n` panics | anti-engine 1, 10, 8, 2 | Restatements of already-documented limits (PROGRESS.md "Known limits"; COMMANDS.md sec 7 `py/rs_maxt_eq_n.txt`). Confirmed present, not new. Rust `max_t = n` message re-measured: `zero denominator` panic vs Python `ZeroDivisionError: Fraction(0, 0)`. |
| `p < 0`, `p >= 2^32`, entries/`p`/`T0` outside i64, non-integers, `n > 2^20` | grok 1-8, 10, 12-15; anti-kernel 5-15 | All inside the four divergences already declared in `kakeya-core/src/lib.rs`. Measured anyway (`t_grok_claims.py`): G8 float entry -> py 0 / rs TypeError; G10 `rank([[1,'x']], 0)` -> py ZeroDivisionError / rs TypeError (ordering inside the documented type class); G12 `force([[1]],1,[],-5)` -> py IndexError / rs ValueError (ordering inside the documented p<0 class); G13 float `p=2.5` -> py 0 / rs TypeError; G14 `T0="0"` -> py (True,{'0'}) / rs TypeError; G15 `p=2**63` -> py 1 / rs OverflowError. None of these is new. |
| grok 11 restated for `rank` | own follow-up | `rank([{0:1,1:P-1}], P)` -> **SAME** (both 1). The mapping divergence is `force`-only. |

Other own probes that came back SAME and are worth recording as negative results:
`force`/`rank` with `range(2)` rows, `bytearray` rows, tuple-of-tuples rows, a
`dict` as the outer `rows` container (both TypeError), a `str` row (both TypeError),
a `dict` as `T0` (both iterate keys -> same), and an old-style getitem-only
sequence class (both SAME, because PyO3's `try_iter` uses the same legacy
sequence protocol Python's `for` loop does).

---

## POSITIVE EVIDENCE ADDED BY THIS PASS

### 1. Independent wide kernel sweep — 557,055 comparisons, 0 mismatches

`sweep_wide.py`, pure-Python `fastcore._force_py`/`_rank_py` vs
`fastcore_rs.force`/`rank` in one process, `fastcore._INV.clear()` before EVERY
call so the documented cross-`p` cache quirk never fires. Widens r2's sweep on the
two axes it left narrow (r2 used entries `{0,1}` and `p` in `{0,1,2}`):

    cd src && /usr/bin/python3 ../rust/refute/external/r5/sweep_wide.py
    block1 rank ragged/wide-entry:   cases=3528    mismatches=0
    block2 force ragged/n-vs-width:  cases=8064    mismatches=0
    block3 force exhaustive-small:   cases=396384  mismatches=0
    block4 rank exhaustive-tiny:     cases=149079  mismatches=0
    TOTAL cases=557055  mismatches=0

Entry alphabet included `0, +-1, +-2, 3, 6, 2^32-1, 2^32, 2^32+1, +-2^62,
2^63-1, -2^63, True, False`; moduli `0,1,2,3,4,5,7,9,257, 2^31-1, 2^32-1, 2^32,
2^32+1, -5`; ragged row shapes up to 3 rows x lengths 0..3; `n` both smaller and
larger than the row width; `T0` with duplicates, negatives, out-of-range members
and `True`. Mismatches at `p < 0` and `p >= 2^32` are excluded by the `DOC(p)`
predicate in the script and are the only ones that occur (the first, unfiltered
run produced mismatches exclusively at `p = 2^32`). This is ~10x `difftest.py`'s
54,406 checks and covers entry magnitudes `difftest.py` does not.

Note the u64 arithmetic was checked by hand as well as by test: with
`p <= 2^32 - 1` every product in `fermat_inv` and in the two elimination inner
loops is bounded by `(2^32-1)^2 = 2^64 - 2^33 + 1 < u64::MAX`, so nothing wraps.

### 2. MT19937 port: seeds far beyond the two that were oracled

The record only ever compared the sampled path at `--seed 11` (scan; `scan1.py`
hardcodes `seed=11`) and `--seed 0` (rzero). Two sweeps here, both with a real
Python oracle and no constant edited:

  (a) `rzero_one.py <d> <pool> <limit> <seed>` — seed is already a positional
      argument. `2x2 pool 6 limit 300`, seeds
      `0 1 7 11 4294967295 4294967296 4294967297 12345678901234567890
      18446744073709551615`, Python vs Rust `--threads 1` and `--threads 2`:
      **9/9 PASS** (`seeds/`). Weak on its own: every run reports
      `forcing_objects: 0`, so the RESULT line does not depend on which labels
      were drawn.

  (b) `scan_seed.py` — a copy of `scan1.py` with `seed` taken from argv instead
      of the literal `11`. SHIM RULE check performed and recorded: `seed` is a
      real parameter of `search.scan_dims` (default 0) and occurs in exactly ONE
      place inside it (`rng = random.Random(seed)`); no other constant refers to
      it. Self-check run first and PASSED: `scan_seed.py ... 11` is byte-identical
      to `scan1.py ...` (149 lines). Config `2x2 pool 6 max-t 1 target 7/4
      limit 200` — 129 lines with 64 HITOBJ per run, so the drawn labels DO
      determine the output. Same nine seeds, Python vs Rust `--threads 1` and
      `--threads 2`:

      PASS seed=0                     129 lines, 64 HITOBJ
      PASS seed=1                     153 lines, 76 HITOBJ
      PASS seed=11                    149 lines, 74 HITOBJ
      PASS seed=123                   157 lines, 78 HITOBJ
      PASS seed=4294967295            155 lines, 77 HITOBJ
      PASS seed=4294967296            139 lines, 69 HITOBJ
      PASS seed=4294967297            127 lines, 63 HITOBJ
      PASS seed=12345678901234567890  139 lines, 69 HITOBJ
      PASS seed=18446744073709551615  151 lines, 75 HITOBJ
      SCAN-SEED SWEEP pass=9 fail=0

      Every line of every stream compared verbatim (only "seconds" masked):
      HIT lines, RESULT, and every HITOBJ witness. So the CPython
      `init_by_array` port in pyrandom.rs is correct for seeds spanning one
      limb, the 2^32 boundary, and two limbs up to 2^64-1 -- not just for the
      seed 11 / seed 0 the record had.


### 3. Re-measured, unchanged

`shasum -a 256 rust/target/release/kakeya-search` =
`add554183aaa3d7cf1f2d468ba11e39926aea035853809811af4e6c40010fcf9`, matching the
claim.

**Process note, reported because it matters to the record.** This pass issued no
`kill`, `pkill`, `killall` or signal of any kind to any process. pid 13369 (the
pure-Python cycles8 POOL3 oracle) was alive at the start and at the end
(`01:51:47` elapsed at the close). pid 12158 (`ks8run cycles8 --pool 6 --patterns
8cycle --threads 10 --tlimit 36000`) was alive and confirmed by `ps` at `01:39:57`
elapsed and was **no longer in the process table** roughly 12 minutes later. It
was launched with a 36000 s limit and had run ~1 h 40 m, so it did not reach its
own deadline, and it left no new file in the tree (nothing under `rust/` outside
`refute/external/r5/` was modified in the preceding 40 minutes). Its stdout went
to another session's shell, so its exit status is not visible from here. Other
agent sessions were concurrently active on this machine during this pass -- `ps`
at the close showed an `improve/perf` lens running `kperf` builds plus
`kakeya-search scan --d 2x2x2x2 --pool 4 --max-t 0 --target 7/4 --tlimit 5
--threads 2` at 99% CPU for 9+ minutes (itself an instance of the documented
"--tlimit is not a wall-clock bound" limit). Whoever reconciles the lenses should
find out what happened to 12158; it was not this one.

---

## COVERAGE OBSERVATION (not a finding)

`scan1.py` hardcodes `seed=11`, so before this pass `kakeya-search scan --seed`
had **no Python oracle at any value but 11**. That is exactly the hole r3 fell
into and self-retracted over. Item 2(b) above closes it for nine seeds using the
driver function's own parameter rather than a rewritten constant; the
`scan_seed.py` self-check against `scan1.py` at seed 11 is the guard that makes
the comparison trustworthy, and it is included in the file.

Second, smaller: `--seed` is parsed as `u64`, so negative seeds — which
`random.Random(-1)` accepts and `rzero_one.py` will pass — cannot be expressed:

    rzero_one.py 2x2 6 20 -1  -> RESULT {... "scanned": 20 ...}
    kakeya-search rzero --d 2x2 --pool 6 --limit 20 --seed -1
      -> kakeya-search: bad --seed "-1": invalid digit found in string

Same class as the already-documented `--target` decimal narrowing; recorded, not
claimed as new.

## FILES WRITTEN (all under rust/refute/external/r5/)

    prompt_kernel.txt prompt_engine.txt prompt_grok_short.txt
    anti_kernel.out anti_engine.out grok_kernel.out (+ .err)
    sweep_wide.py            557,055-case kernel sweep
    t_iter_claims.py         antigravity claims 1-4 + own iterable probes
    t_grok_claims.py         grok claims 8,10-15 + own mapping/sequence probes
    t_getitem.py t_rev2.py   the getitem-vs-iterate witnesses
    scan_seed.py             scan1.py with seed from argv (self-checked at 11)
    tl0.py.txt tl0.rs.txt    the --tlimit 0 divergence
    seeds/ scanseeds/        the two seed sweeps, .py/.rs1/.rs2 + .norm
