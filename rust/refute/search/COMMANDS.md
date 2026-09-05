# Refutation attempt: does `kakeya-search` reproduce the Python drivers?

Everything below was run on 2026-09-05.  Python side is always
`/usr/bin/python3` (3.9.6) with `KAKEYA_PURE_PY=1` and cwd
`arithmetic-kakeya/src`, i.e. the pure-Python `fastcore`, not the PyO3 kernel.
Rust side is `rust/target/release/kakeya-search` (cargo 1.98.0 / rustc 1.98.0).

`norm.py` is the only normalisation applied to a stream before diffing: it
drops a trailing `EXIT=` marker, rewrites `"seconds": <x>` to `"seconds": X`
and `[<x>s]` to `[Xs]`.  Nothing else is masked -- every HIT, HITOBJ, witness,
score, tie-break and count is compared verbatim.

## 1. The three mandated cheap fixtures (scan1.py)

    cd src && KAKEYA_PURE_PY=1 /usr/bin/python3 scan1.py n4_p6_t1 2x2 6 1 7/4 - 900
    cd src && KAKEYA_PURE_PY=1 /usr/bin/python3 scan1.py g2_23_t1  2x3 3 1 9/5 - 3000
    cd src && KAKEYA_PURE_PY=1 /usr/bin/python3 scan1.py g2_32_t1  3x2 3 1 9/5 - 3000
    kakeya-search scan --tag <tag> --d <d> --pool <k> --max-t <t> --target <p/q> --threads {1,12}

  files: py_n4_p6_t1.txt rs_n4_p6_t1_t{1,12}.txt py_g2_23_t1.txt rs_g2_23_t1_t{1,12}.txt
         py_g2_32_t1.txt rs_g2_32_t1_t{1,12}.txt  (+ .norm)
  result: all three IDENTICAL py vs rs1 vs rs12 after normalisation.
          n4_p6_t1 = 241 lines (120 HIT + RESULT + 120 HITOBJ).

## 2. Thread-count independence

    for T in 0 2 3 5 7 13 64 500; do kakeya-search scan ... --threads $T; done
  files: tn_*.norm -- all 8 identical to the Python stream.

## 3. New configurations not in the fixture corpus

    scan1.py newA 2x2 3 2 2   -   (max_t = 2, 300 hits, 24 with "gens": [], 276 with non-empty T0)
    scan1.py newB 2x2 4 2 15/8 -
    scan1.py newC 3   3 1 2   -   (k = 1 box)
  files: py_new{A,B,C}.txt rs_new{A,B,C}_t{1,12}.txt -- all IDENTICAL.

## 4. Differential sweep over 37 scan configurations

    ./sweep.sh          # reads configs.txt, runs python + rust(1) + rust(12), diffs
  files: sweep1-out.txt (configs s01..s06), sweep2-out.txt (the rest), sweep/*.txt
  Covers d in {2,3,4,5,6,2x2,2x3,3x2,2x4,1x3,3x1,2x1x3,2x2x2,3x3,2x2x2x2},
  pools 3/4/5/6/8, max_t 0/1/2, targets 13/8 7/4 15/8 9/5 11/6 2 3,
  exhaustive and `--limit` (MT19937-sampled) enumeration.

## 5. rzero: 4 recorded fixtures + 6 new configurations

    rzero_one.py <d> <poolsize> [limit|-] [seed]      # oracle: calls rzero.sweep directly
    kakeya-search rzero --d <d> --pool <k> [--limit N] --seed S --threads {1,12}
  files: rz_{f1..f4,n1..n6}.{py,rs1,rs12}.txt -- 10/10 PASS.

## 6. g2-tall / cycles8 / stacked oracles

    oracle_drivers.py g2-tall <rows> <max_t>          # tlimit = 1e9
    g2tall_one.py <rows> <max_t> <tlimit>             # tlimit is settable -- exposes the `complete` bug
    oracle_drivers.py cycles8 <poolsize> [target]
    oracle_drivers.py stacked <poolsize> [max_t]

## 7. Edge probes

  probes.txt          -- decimal target, unnormalised target, d=1, --limit 0, negative target
  py/rs_maxt_eq_n.txt -- max_t = n: Python ZeroDivisionError (exit 1) vs Rust panic (exit 101)
  py/rs_stacked_lowtarget.txt -- no witness: Python TypeError (exit 1) vs Rust message (exit 1)
  shift/shift.rs      -- demonstrates that the u64 vertex bitmask aliases vertex 64 onto vertex 0
