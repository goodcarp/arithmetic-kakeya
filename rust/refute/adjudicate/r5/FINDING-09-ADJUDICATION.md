# Adjudication of lens finding 9/10 (record lens R3)

FINDING: "Two coverage-map rows ('scan k=1 box --d 6', 'scan 3-level sampled
--d 2x2x2') have no artifact anywhere in the tree"

VERDICT: real = true.  Substantively correct as of when the lens ran, and the
correction now on disk is correct (with one residual stale sentence, below).
Suggested reclassify: severity major, not critical -- which is also what the
lens itself wrote (`r5/FINDINGS.md:95` reads "R3 -- MAJOR"); the "critical"
label came from the finding card, not the lens.

Artifacts tested (sha256, 2026-09-06):
  rust/target/release/kakeya-search
    add554183aaa3d7cf1f2d468ba11e39926aea035853809811af4e6c40010fcf9  (matches the pinned hash)
  src/fastcore_rs.abi3.so
    03db7ae995fdda76eed5d7d72474f5b27141bc9b15814e89827250e35d21ed4b
All wall-clock numbers below are CONTENDED (shared machine).

## 1. The repro reproduces verbatim

    $ grep -rh '"max_t"' . | grep -E '"d": \[2, 2, 2\]|"d": \[6\]' | sort -u
    RESULT {"tag": "g2_222_t1", "d": [2, 2, 2], "pool": 3, "max_t": 1, "target": "9/5", "scanned": 864, "total": 16384, "best": null, "hits": 0, "complete": false, "seconds": 3305.6}
    RESULT {"tag": "n6c2_6_t1", "d": [6], "pool": 4, "max_t": 1, "target": "67/40", "scanned": 1619, "total": 3125, "best": null, "hits": 0, "complete": false, "seconds": 2400.8}
    RESULT {"tag": "n6c_6_t1", "d": [6], "pool": 4, "max_t": 1, "target": "67/40", "scanned": 1700, "total": 3125, "best": null, "hits": 0, "complete": false, "seconds": 3005.8}
    RESULT {"tag": "n8a_222_t0", "d": [2, 2, 2], "pool": 4, "max_t": 0, "target": "67/40", "scanned": 207, "total": 40000, "best": null, "hits": 0, "complete": false, "seconds": 3059.9}
    RESULT {"tag": "n8b_222_t1", "d": [2, 2, 2], "pool": 4, "max_t": 1, "target": "67/40", "scanned": 173, "total": 15000, "best": null, "hits": 0, "complete": false, "seconds": 3060.3}

    $ ls -l rust/refute/search/sweep/c12.py.txt
    -rw-r--r--@ 1 spaceman  staff  0 Sep  5 18:45 rust/refute/search/sweep/c12.py.txt

Provenance of the five lines (`grep -rl` on the tags): `results.json` (Aug 24
14:13) and `logs/{g2_222_t1,n6c_6_t1,n6c2_6_t1,n8a_222_t0,n8b_222_t1}.log`
(Aug 24 13:30-14:12), plus the lens's own FINDINGS.md.  All Python-side, all
`complete: false`, all with different `scanned` -- not byte-reproducible even
in principle, and with no Rust counterpart.

## 2. The obvious way the lens could have been wrong: it wasn't

The one real risk was a grep-pattern miss (Rust emitting compact JSON that
`"d": \[6\]` would not match).  Checked: the Rust RESULT line uses identical
spacing to the Python one --

    sweep/c09.rs1.txt: RESULT {"tag": "c09", "d": [1, 3], "pool": 4, ...
    sweep/c09.py.txt : RESULT {"tag": "c09", "d": [1, 3], "pool": 4, ...

A spacing-agnostic, binary-inclusive re-grep finds nothing the lens missed:

    $ grep -ra --binary-files=text -hE 'RESULT \{"tag": "[^"]*", "d": \[(6|2, 2, 2)\], "pool"' . \
        | grep -v '"forcing_objects"' | sort -u
    -> exactly the same five Aug-24 Python lines, nothing else.

The `d=[2,2,2]` lines that do exist under `rust/refute/` all carry
`"forcing_objects"`/`"best_score"` -- the `rzero` driver, i.e. a different
coverage row, exactly as the lens said.  `crates/kakeya-search/src/check.rs`
likewise has `rzero_2x2x2_pool4` / `rzero_2x2x2_pool6_lim60000` fixtures --
rzero, not scan.

## 3. s17b/s18/s19 and c12: no artifacts

`ls rust/refute/search/sweep/` ends at `s16b.py.txt` (itself Python-only, no
`.rs*`) then jumps to `c01`; there is no `s17b*`, `s18*` or `s19*` file
anywhere in the tree (the only `find -name 's1[789]*'` hits are
`external/r5/seeds/s18446744073709551615.*`, a u64-max seed fixture).
Neither `configs.txt` nor `configs2.txt` contains any other `2x2x2` scan
config, and `c12` is the only `--d 6` config.  Independent recount:

    $ ls rust/refute/search/sweep/*.py.txt | wc -l   -> 29
    $ for f in ...; do [ -s "$f" ] || echo EMPTY: $f; done
    EMPTY: rust/refute/search/sweep/c12.py.txt

i.e. 29 configs with artifacts, exactly one empty Python output -- matching
the "29 / 28 non-empty" figure the correction in COMMANDS.md now states.

## 4. Was the original claim really a positive one? Yes

`r5/FINDINGS.md:97-98` quotes the pre-correction map rows as

    | scan k=1 box `--d 6`             | scan1.py | identical |
    | scan 3-level sampled `--d 2x2x2` | scan1.py | identical |

flat "identical" verdicts against a `scan1.py` oracle, with zero artifact.

## 5. Is the on-disk correction right?

PROGRESS.md now marks both rows **UNSUPPORTED ON DISK** with the reason and a
"Re-run before citing" -- accurate and not overstated.  SWEEP-2026-09-06.md
item 6 states it correctly.  `rust/RESULTS-RUST.json` makes no `--d 6` /
`--d 2x2x2` coverage claim.

One residual stale sentence: `rust/refute/search/COMMANDS.md:43` still reads

    Covers d in {2,3,4,5,6,2x2,2x3,3x2,2x4,1x3,3x1,2x1x3,2x2x2,3x3,2x2x2x2},

The sweep does NOT cover `6` (c12's Python side is 0 bytes) and does not cover
`2x2x2` at all (s17b/s18/s19 never ran).  The correction paragraph four lines
above says so explicitly, so it is not a fresh overclaim, but the enumeration
line is literally wrong and should drop `6` and `2x2x2`.

## 6. Sizing note (why major, not critical)

No code defect is implied: the binary is fine, and the shapes are not wholly
unexercised elsewhere -- `2x2x2` is exercised by the rzero fixtures in
`check.rs` and by the whole `cycles8` driver (which is defined on the 2x2x2
box), and a 3-level scan config with artifacts does exist (`c11`, `2x1x3`,
100 KB of py/rs1/rs12 agreement).  What is false is the map's claim that these
two SCAN rows were checked against a Python oracle.

## 7. I filled the `--d 6` row weakly, and say so

    cd src && KAKEYA_PURE_PY=1 /usr/bin/python3 scan1.py adjd6 6 3 0 2 200 200
      -> RESULT {"tag": "adjd6", "d": [6], "pool": 3, "max_t": 0, "target": "2",
                 "scanned": 200, "total": 200, "best": null, "hits": 0,
                 "complete": false, "seconds": 70.5}     (73 s wall, contended)

    ./rust/target/release/kakeya-search scan --tag adjd6 --d 6 --pool 3 \
        --max-t 0 --target 2 --limit 200 --seed 11 --threads 2
      -> RESULT {... identical ..., "seconds": 2.5}       (2 s wall, contended)

    diff after masking "seconds" -> IDENTICAL

`scan1.py:15` hardcodes `seed=11`, so `--seed 11` on the Rust side is the
matching call -- no shim, no parameterised constant.  But this is a WEAK
comparison and does NOT fill the coverage row: the stream is a single RESULT
line with `hits: 0` and `best: null`, so it would match under any sampling
order.  Files: `d6_py.txt`, `d6_rs2.txt`, `d6_{py,rs2}.norm` in this directory.
It does establish that the row is cheap to fill honestly at small `--limit`;
the reason `c12` (d=6, pool 6, max_t 1, exhaustive = 46,656 labels) has a
0-byte output is that the pure-Python side at ~2.8 labels/s would need ~4.6 h.
