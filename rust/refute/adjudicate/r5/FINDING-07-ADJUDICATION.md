# Adjudication — finding 7/10 (record lens R1): "kernel disclosure names one coverage-map row; at least two rows had the PyO3 kernel under the Python side"

Adjudicator: 1 of 1. Task = refute the FINDING, not the code.
Artifacts tested (sha256 recorded, nothing rebuilt, nothing outside this directory written):

    rust/target/release/kakeya-search  add554183aaa3d7cf1f2d468ba11e39926aea035853809811af4e6c40010fcf9   (matches the pinned sha)
    src/fastcore_rs.abi3.so            03db7ae995fdda76eed5d7d72474f5b27141bc9b15814e89827250e35d21ed4b

Machine contended by another session (a `g2-tall 3 1` run that costs 7.3 s user took 36 s wall);
every wall-clock number below is contended.

## VERDICT: real = true. The finding is substantively correct and I could not refute any part of its core.

## 1. Repro, verbatim

    $ ls -l "…/rust/refute/search"/*rskernel*
    -rw-r--r--@ 1 spaceman  staff  124 Sep  5 18:22 …/py_cycles8_p3_rskernel.txt
    -rw-r--r--@ 1 spaceman  staff  148 Sep  5 18:48 …/py_g2tall_2x4_rskernel.txt
    -rw-r--r--@ 1 spaceman  staff    0 Sep  5 18:07 …/py_stacked_p4_t1_rskernel.txt

    $ cat py_g2tall_2x4_rskernel.txt
    RESULT {"tag": "g2_tall_2x4", "d": [2, 4], "pool": 3, "max_t": 1, "target": "<11/6", "best": null, "hits": 0, "complete": false, "seconds": 1968.2}
    $ cat rs_g2tall_2x4.txt
    RESULT {"tag": "g2_tall_2x4", "d": [2, 4], "pool": 3, "max_t": 1, "target": "<11/6", "best": null, "hits": 0, "complete": true, "seconds": 319.0}

    $ sed -n '50,54p' crates/kakeya-search/PROGRESS.md
    ## In flight
    - Python oracles running (with the Rust fastcore kernel, which B1 proved
      bit-identical, so they finish in minutes not hours):
      g2-tall 4 1, cycles8 3, stacked 4 1.  Compare when they land, then embed
      the results as extra `check` fixtures.

File byte counts, contents and mtimes are exactly as the lens reported. All three `_rskernel`
artifacts became coverage-map rows ("Landed after the in-flight oracles came back": stacked
POOL4 max_t=1, cycles8 POOL3; plus the g2-tall 2x4 row).

## 2. The `_rskernel` tell is real, not a filename convention

    $ cd src && python3 -c "import fastcore; print(fastcore.force.__module__, fastcore.force is fastcore._force_py)"
    fastcore_rs False
    $ KAKEYA_PURE_PY=1 python3 -c "import fastcore; print(fastcore.force.__module__, fastcore.force is fastcore._force_py)"
    fastcore True

So any oracle run without `KAKEYA_PURE_PY=1` runs the PyO3 kernel — which is precisely what the
"In flight" paragraph says was done for all three.

## 3. Two independent on-disk admissions that the wording the lens quoted was really there

- `refute/search/r4/NOTES.md`, closing section: "two more of my own statements from this pass were
  wrong … the disclosure paragraph said 'unlike every other row' — two other rows had the PyO3
  kernel too".
- `refute/SWEEP-2026-09-06.md` A.4: "Record R1 — two more coverage rows had the PyO3 kernel on the
  Python side … My own disclosure paragraph from the afternoon said 'unlike every other row'.
  Wrong; fixed."
- The current `PROGRESS.md:68-72` itself: "it was NOT the only such row, as the first version of
  this paragraph wrongly said".

No git was used (ground rule); these three are sufficient to establish the pre-correction text.

## 4. Could the g2-tall 2x4 row be rescued by a pure-Python oracle elsewhere? No.

`grep -r g2_tall_2x4` over the whole tree returns exactly four RESULT variants. The only *complete*
Python 2x4 run on disk is the PyO3-kernel one (1968.2 s). The pure-Python-era run
(`logs/g2_tall.log`, Aug 24, predates the .so of Sep 4) reads:

      [2x4] TIME LIMIT
    RESULT {… "complete": false, "seconds": 703.3}

i.e. it tripped `g2_tall.py`'s hardcoded 700 s limit and never finished, and (being pre-`walked`/
`total`) does not even record how far it got. So the row labelled "g2-tall 2x4 (the Tier-3 target)"
had, and has, no pure-Python end-to-end oracle. The finding's central claim stands at full strength.

## 5. Is the correction now on disk right? Mostly yes; two notes.

CORRECT:
- The corrected paragraph and all three map rows now name the kernel. Verified row by row.
- cycles8 POOL3 is now a genuine pure-Python comparison:
  `md5 r3/out/C8.py.txt r3/out/C8.rs1.txt r3/out/C8.rs12.txt` → all `1d97097e70de4f0bb16fe50516f01ce8`
  (131 B, `tested: 29004`, `EXIT=0`). The abandoned pure-Python attempt `py_cycles8_p3.txt` is
  indeed 45 B (header only).
- The g2-tall row's stated `complete` divergence is arithmetically right: `rust/oracle_drivers.py`
  passes `tlimit = BIG = 1e9` but keeps `"complete": (el < 700)`, and el = 1968.2 → false, while the
  Rust run had no `--tlimit` and finished in 319.0 s → honest true.

NOTE A (neighbouring text now slightly overstated). PROGRESS's "Known limits" scope note says that
because `g2_tall.py.__main__` hardcodes 700 in both places, "for every run that driver can actually
perform, `el < 700` is a correct completeness test and the only disagreement is the `--tlimit > 700`
case above". The estate's own oracle harness (`rust/oracle_drivers.py`, BIG = 1e9) is exactly such a
case, and the single recorded 2x4 comparison IS an instance of the disagreement, not a hypothetical.
The note reads as if the case never occurs; it occurred, in the very row above it. Suggest one clause.

NOTE B (the finding's own parenthetical is mildly overstated). The finding cites a fourth artifact,
`refute/search/r5-hitpaths/out/st_p3_mt0.py_rskernel.txt`, as showing "the pattern is not confined to
these". That lens disclosed it in its own report (`r5-hitpaths/FINDINGS.md:215`: "One further
comparison, **driver-level only — the Python side ran the PyO3 kernel**"), and it was not a
coverage-map row when the lens ran. The residual is smaller than implied but nonzero: the map row
"15 new end-to-end driver comparisons … | 14 of 15 pure-Python" discloses the count without naming
which one is the exception (it is stacked POOL3 max_t=0, S3 in that report). One word would fix it.

NOTE C (unrelated, spotted while checking): PROGRESS's Bench section says "Python with the B1 PyO3
kernel took 1246.6 s" for g2_tall 2x4, while the recorded PyO3 artifact says 1968.2 s. Two different
runs on a busy machine is the benign reading, but no artifact on disk carries 1246.6.

## 6. Severity

Filed "critical". I would call it MAJOR-record, not critical: it is a documentation overstatement of
verification coverage, with no code defect and no recorded number changed. The substance of all
three affected rows survives (cycles8 POOL3 has since become a real pure-Python comparison; the
stacked substance is carried by the md5-equal max_t=2 pure-Python comparison; g2-tall 2x4 remains
driver-level only, now labelled as such). What made it worth catching is that the false universal
("unlike every other row") was written *in the act of disclosing*, which is the failure mode that
makes a reader stop checking.

## 7. Independent corroboration that the 1968.2 s artifact really is a PyO3 run (measured, contended)

Same driver, same machine, same contention, only the kernel changed (`cd src && python3
../rust/oracle_drivers.py g2-tall 3 1`, with and without `KAKEYA_PURE_PY=1`):

    PyO3 kernel : RESULT {… "tag": "g2_tall_2x3" … "seconds": 33.6}   real 0m36.1s  user 0m7.26s
    pure Python : RESULT {… "tag": "g2_tall_2x3" … "seconds": 267.3}  real 4m29.3s  user 1m12.60s

Kernel speedup on this driver ≈ 10.0x by user CPU (8.0x by the driver's own `seconds`). Scaling the
recorded 2x4 PyO3 time by that factor puts a pure-Python 2x4 at ≈ 5.5 CPU-hours, so 1968.2 s cannot
be a pure-Python run — the `_rskernel` label is not merely a filename claim, it is the only timing
consistent with the artifact. (Side effect: PROGRESS's Bench line quoting the S2 contract's
"~3073 s pure-Python estimate" for 2x4 is roughly 6x low on this measurement. Estimate, not a
recorded run; noted, not filed.)
