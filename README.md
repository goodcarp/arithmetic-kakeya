# arithmetic-kakeya

A workbench for Epoch AI's **arithmetic Kakeya** open problem (Katz–Tao formalism):
find a finite `X`-constructible graph whose exact rational **score** is ≤ 1.675.
The published record γ = 1.6751309… (largest root of x³ − 4x + 2) is a *limit* that no
finite object attains, so the target lies strictly outside the published family —
see `KAKEYA-WORKBENCH.md` §0. Every search in this tree has returned **0 hits**;
those negatives, their scope, and the machinery that produced them are the content.

Two implementations of the same searches, differentially verified against each other:

* `src/` — the original pure-Python engine and five search drivers (`scan`, `g2_tall`,
  `cycles8`, `stacked`, `rzero`), exact `Fraction` arithmetic, mod-p elimination in
  `fastcore.py`.
* `rust/` — a bit-exact Rust port: `kakeya-core` (the `force`/`rank` kernel),
  `fastcore-rs` (PyO3 abi3 drop-in for `fastcore.py`), `kakeya-search` (a rayon
  binary reproducing the five drivers' stdout byte for byte). 20–350× faster.

## Layout

```
KAKEYA-WORKBENCH.md   the formalism, both published objects rebuilt, ten lemmas   (start here)
REPORT.md             seat report
results.json, logs/   the original Python campaign results (Aug 2026)
src/                  Python engine + drivers; fastcore.py loads the Rust kernel when present
tests/                Python unit tests (pytest)
papers/               the sources
adversary-fable/      pre-registered PREDICTIONS.md (+ errata §7), traps.json (119), PORT-TRAPS.md
adversary-external/   Gemini/Grok review traps, VERIFIED.md (16)
rust/
  crates/kakeya-core, fastcore-rs, kakeya-search
  crates/kakeya-search/PROGRESS.md   ★ coverage map + known limits + every correction, dated
  RESULTS-RUST.json     the six long runs, with prediction status
  difftest.py           54,406-case kernel differential (pure Python vs Rust)
  oracle_drivers.py     runs the unmodified Python drivers as oracles
  refute/               every refuter pass: modular, control, boundary, external, search (r3, r4, r5), record, kernel, science
  refute/SWEEP-2026-09-06.md   ★ the latest triage: what was confirmed, dropped, still open
  improve/              perf (4.7× kernel prototype) and robustness (streaming --tlimit) — built and gated in COPIES, not adopted
```

## Build

Prerequisites: rustc/cargo ≥ 1.73 (built with 1.98), `maturin` ≥ 1.15, and
`/usr/bin/python3` 3.9 with `sympy` (two fixtures are pure sympy). No other deps.

```bash
# the search binary
cd rust && cargo build --release -p kakeya-search
# the kernel as a Python extension (abi3), then drop it beside fastcore.py
cd rust/crates/fastcore-rs && maturin build --release
unzip -o -j ../../../target/wheels/fastcore_rs-*.whl 'fastcore_rs/*.so' -d ../../../src/   # or copy the .so from the wheel
```

`src/fastcore.py` uses the `.so` when present. **`KAKEYA_PURE_PY=1` forces the pure-Python
kernel** — every oracle run in this tree that claims "pure Python" was run with it, and
without it a "Python" comparison is a driver-level check with the Rust kernel on both
sides. The record discloses which is which, row by row (`PROGRESS.md` coverage map).

Record the sha256 of what you built before quoting any result from it:
audited binary `add554183aaa3d7cf1f2d468ba11e39926aea035853809811af4e6c40010fcf9`,
shipped `.so` `03db7ae995fdda76eed5d7d72474f5b27141bc9b15814e89827250e35d21ed4b`.
**The build is reproducible:** a clean clone of this repository at `83fd36c` (the crates are unchanged in every later commit), built with
`cargo build --release -p kakeya-search` (rustc 1.98, LTO, codegen-units = 1), produced a
binary with exactly the audited sha256 and `check` = 14 PASS / 2 SKIP / 0 FAIL (2026-09-06).

## Gates (all must be green before a result is quoted)

```bash
cd rust
./target/release/kakeya-search check --threads 1     # 14 PASS / 2 SKIP / 0 FAIL over 16 fixtures
./target/release/kakeya-search check --threads 12    # identical modulo the [Ns] brackets
cargo test --release --workspace                     # 62 + 16 + 0 = 78
cargo clippy --release --all-targets --workspace -- -D warnings
cd ../src && KAKEYA_PURE_PY=1 /usr/bin/python3 ../rust/difftest.py      # 54,406 checks, 0 mismatches, 1 expected divergence
cd ../rust/refute/record/r5 && KAKEYA_PURE_PY=1 /usr/bin/python3 verify_traps.py         # 119/119 traps + 16/16 VERIFIED, 0 mismatches
cd ../../../../ && /usr/bin/python3 -m pytest tests/                    # Python engine tests
```

## Reproduce the results

| result | command | expected |
|---|---|---|
| stacked POOL4 / POOL6 | `kakeya-search stacked --pool 4 --max-t 2 --target 7/4` (and `--pool 6`) | best 7/4, 0 strict hits, all-ZERO witness; matches pure-Python `logs/stacked.log` |
| cycles8 POOL6, 8-cycle patterns | `kakeya-search cycles8 --pool 6 --target 67/40 --deg 2 --patterns 8cycle --threads 10` | `tested: 81660`, 0 hits (~1.7 h on 10 threads) |
| cycles8 t = 3 residual | `cd src && KAKEYA_PURE_PY=1 /usr/bin/python3 ../rust/refute/science/r5/t3_check.py all` | 1,692,000 (graph, T0) pairs, 0 hits (~11 min pure Python) |
| cycles8 POOL3 pure-Python oracle vs Rust | `oracle_drivers.py cycles8 3` (KAKEYA_PURE_PY=1, ~93 CPU-min) vs `kakeya-search cycles8 --pool 3 --target 67/40 --deg 2` | byte-identical, `tested: 29004` |
| scan n4_p6_t1 | `kakeya-search scan --tag n4_p6_t1 --d 2x2 --pool 6 --max-t 1 --target 7/4` vs `src/scan1.py` | 241/241 lines identical exc. seconds, 120 witnesses |

Every other comparison, with its oracle and its exact scope, is in the coverage map in
`rust/crates/kakeya-search/PROGRESS.md`; the long runs are in `rust/RESULTS-RUST.json`.

## What is settled, and what is not

* **cycles8 POOL6 is closed at every t** (0 hits): 8-cycle patterns at t ≤ 2 by two
  independent routes, at t = 3 exhaustively; two-4-cycle patterns by the mediant argument
  plus t = 3 enumeration. It covers 6.95 % of the 2×2×2 POOL6 label space — it is **not**
  "n = 8 closed".
* stacked POOL4/POOL6 complete, 0 hits. g2_tall 2×5 / 2×6 incomplete (time-limited).
* Every negative is conditional on the matching-suffix reading of Operation 1
  (`KAKEYA-WORKBENCH.md` §1 flags the ambiguity); the Rust binary cannot test the other reading.
* Known limits of the port (`--tlimit` on huge index spaces, `--tlimit 0`, the three
  Rust-only g2_tall keys, driver-unreachable input shapes): `PROGRESS.md` "Known limits".

## Rules this tree is kept under

* A refuter attacks every claim before it is banked; corrections are appended, dated, never
  silently edited into pre-registered text (`PREDICTIONS.md` §7, `PORT-TRAPS.md` errata).
* Kernel disclosure: say which kernel was under the Python side, in the claim itself.
* Shim rule: if a harness makes a constant settable, change every reference to it — two
  refuters manufactured false divergences by parameterising `tlimit` while copying `(el < 700)`.
* Do not extrapolate Python runtime across pool sizes (POOL3 is 24× cheaper per pair than POOL6).
* Never `pkill -f kakeya-search`; run long jobs under a distinct binary name.
