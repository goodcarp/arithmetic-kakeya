# Adjudication, finding 10/10 (record lens R11) — REFUTED (real = false)

Finding under test: PREDICTIONS §6 "the runtime estimate for 2x5 was wrong by more
than 10x" is mis-cited and unsupported; **measured upper bound is ~2.5x**.

Artifacts tested (verified at start of run):
- `rust/target/release/kakeya-search` sha256 `add554183aaa3d7cf1f2d468ba11e39926aea035853809811af4e6c40010fcf9` (the audited sha)
- `src/fastcore_rs.abi3.so` sha256 `03db7ae995fdda76eed5d7d72474f5b27141bc9b15814e89827250e35d21ed4b`

**Machine was heavily loaded by another session throughout: load average 374 → 111
across my runs (6 physical / 12 logical cores). Every wall and CPU-second number
below is contended. Instruction counts are not.**

## Verdict

`real = false`. Reclassify: **minor, record typo**.

Two of the finding's three clauses survive and are nit-grade; the load-bearing
third — the "~2.5x", which is what makes it MAJOR and what the title asserts — is
produced by an inconsistent comparison, and a properly normalised measurement
**supports** §6's ">10x" rather than refuting it.

## 1. What survives (true, nit-grade)

* §6:273 says "(implied by section 3)". §3 is the pair-count table and carries no
  runtime estimate for 2x5. §4 carries it: **0.5–2 hours**. The pointer is wrong.
  This is a section-number typo.
* ">10x" was written with no completed 2x5 run behind it and no `walked` key in
  `logs/rust-g2_tall_2x5.log`. "Unsupported when written" is fair.

## 2. Clause that is false: "no factor is measurable from disk"

The finding says "no artifact records how far it got — no factor is measurable
from disk". The thread count is on disk:

    rust/run_targets.sh:5   B="..."; L="..."; T=8
    rust/run_targets.sh:8   run g2_tall_2x5  g2-tall --rows 5 --max-t 1 --tlimit 7200
    (run() appends --threads $T to every invocation)
    logs/rust-g2_tall_2x5.log: "complete": false, "seconds": 7207.0

8 threads x 7207 s = **57,656 thread-seconds = 16.0 thread-hours consumed without
completing**. That is a hard on-disk *floor* on the cost of a complete 2x5, and it
alone puts the overrun against §4's 2 h upper end at >8x before any new probe is
run. `RESULTS-RUST.json` also carries `"threads": 8` at top level.

## 3. Clause that is wrong: the "~2.5x", and why

§4 derives its 0.5–2 h like this (PREDICTIONS.md:203-236): Python-equivalent total
for 2x5 = 65,536 x ~3 s = ~55 h, then "a faithful Rust port ... should be 30-100x
faster". 55/100 = 0.55 h, 55/30 = 1.83 h. Both inputs are **single-core**: the
Python 55 h is sequential and the 30-100x is a per-core port speedup. §4's estimate
is therefore in sequential-equivalent CPU-hours, and pre-dates the port having
threads at all.

The finding takes its own 41 CPU-hour figure, divides by 8 threads to get ~5 h
wall, and compares that against §4's 2 h. That is wall-on-8-threads versus a
sequentially-derived estimate: it discounts by the thread factor on one side only.
In §4's own currency the finding's own number gives **41/2 = 20x to 41/0.55 = 75x**
— i.e. the lens's measurement confirms ">10x". Its headline number is the same
measurement expressed in a unit the estimate was never in.

## 4. Clause that is wrong: the "UPPER bound" premise

The finding argues its 41 CPU-h is an upper bound "because the probe walks the
product-order prefix, which §4 itself calls the expensive region". Measured on 2x4,
where three nested prefixes are cheap to take, the cumulative cost per unit of work
**rises** with prefix depth:

| run | walked/total | pairs | CPU-s (user+sys) | instructions | instr/tuple | instr/pair |
|---|---|---|---|---|---|---|
| `--rows 4 --tlimit 22 --threads 2`  | 78/4096  | 617   | 17.34  | 17,937,810,347  | 0.230e9 | 29.1e6 |
| `--rows 4 --tlimit 90 --threads 2`  | 185/4096 | 1441  | 54.94  | 53,232,923,139  | 0.288e9 | 36.9e6 |
| `--rows 4 --tlimit 260 --threads 4` | 565/4096 | 4182  | 321.21 | 326,614,386,199 | 0.578e9 | 78.1e6 |

Cost per pair 2.7x and cost per tuple 2.5x over the first 14% of the run. A short
prefix probe is therefore a **lower** bound on the run average on this data, not an
upper one. Both lenses' "upper bound" language, and the errata now on disk, inherit
this error.

## 5. My third data point (the check that was asked for)

    $ cd "/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/rust"
    $ /usr/bin/time -l ./target/release/kakeya-search g2-tall --rows 5 --max-t 1 --tlimit 240 --threads 2
      [2x5] TIME LIMIT
    RESULT {"tag": "g2_tall_2x5", "d": [2, 5], "pool": 3, "max_t": 1, "target": "<11/6",
            "best": null, "hits": 0, "complete": false, "seconds": 242.0,
            "walked": 48, "total": 65536, "pairs": 507}
          242.03 real       118.00 user         2.70 sys
            124913242080  instructions retired
            235683176285  cycles elapsed
    (load average 374.80 before, 316.50 after)

* **walked 48/65536, pairs 507, 120.70 CPU-s** → 4.20 pairs/CPU-s. The record lens
  measured 4.57 pairs/s on the same prefix; mine reproduces it within 9%. So the
  lens's *measurement* is sound; its *interpretation* is not.
* IPC 0.530, 1.035e9 instructions/CPU-second — this box under this load. The
  science lens's complete 2x4 (`science/r5/FINDINGS.md:137,485`: 791.9 CPU-s,
  942.5 s wall, threads 2, 31,718 pairs) implies >=2.99e9 instr/CPU-s (see below),
  so contended CPU-seconds here are inflated ~2.9x. Any CPU-hour figure taken off
  this machine tonight, mine and the record lens's alike, is soft in that direction.

**Skip/start option: there is none.** `g2-tall` accepts only
`[--rows 4,5,6] [--max-t 1] [--tlimit S] [--threads N]`
(`crates/kakeya-search/src/main.rs:23`, and `--help` needs a value / prints the
top-level usage). Enumeration always starts at index 0; only `scan` has `--limit`,
and none of the drivers has a start offset. So the prefix cannot be skipped without
a code change, and no lens could have sampled later pairs of 2x5 directly.

## 6. My own CPU-hour estimate and its basis

Two routes, both anchored on instructions (contention-free work) and converted with
the one measured complete run in this family.

Anchor: complete 2x4 = 4,096 tuples / 31,718 pairs / 791.9 CPU-s (science lens).
From probe C, complete-2x4 instructions >= 4096 x 0.578e9 = **2.37e12** (a floor —
the cumulative average was still climbing at 565 tuples). Hence the box delivered
**>=2.99e9 instr/CPU-s** on that run; call it ~3e9.

* **Route A (per pair, early-prefix rate):** 672,719 x 246.4e6 = 1.66e14 instr
  → 55,300 CPU-s = **15.4 CPU-h**.
* **Route B (per tuple, matched early prefix, scaled off the 2x4 anchor):**
  2x5 = 2.602e9 instr/tuple over its first 48 tuples; 2x4 = 0.230e9 over its first
  78. Ratio 11.31x per tuple, 16x more tuples → complete 2x5 ~= 181 x complete 2x4
  = 181 x 2.37e12 = 4.29e14 instr → 143,000 CPU-s = **39.7 CPU-h**.

Route A is **excluded by the disk**: the recorded run already burned 16.0
thread-hours without finishing, so the total cannot be 15 CPU-h. Route B stands.

**My estimate: a complete `g2_tall 2x5` costs ~25-40 CPU-hours, floor 16
thread-hours from the recorded run.** Adjudicating the two lenses: the record
lens's ~41 CPU-h is close to right (for the wrong stated reason — it is not an
upper bound); the science lens's ~12 CPU-h / "<=14, likely 4-10"
(`science/r5/FINDINGS.md:306`) is **too low, and is refuted by the recorded run's
own 16 thread-hours**.

Against §4's 0.5-2 sequential-equivalent hours that is a **12x-73x overrun.
"More than 10x" is correct.**

## 7. The correction now on disk is wrong and should be rewritten

`adversary-fable/PREDICTIONS.md` §7 errata bullet 2 currently says: "...<= ~41
CPU-hours ..., an upper bound; the science lens's rate on later pairs gives ~12
CPU-h. Against §4's 2 h upper end the overrun is between ~6x and ~20x by CPU-hours,
or ~2.5x by wall on 8 threads at the upper bound — not a clean 'more than 10x'.
Withdrawn as stated."

Four defects:
1. "~2.5x by wall on 8 threads" is the category error of §3 above and should not
   appear next to a sequentially-derived estimate.
2. "an upper bound" is false (§4 of this file): prefix rates under-state here.
3. "the science lens's rate on later pairs" mis-describes it — the science lens's
   anchor is a complete **2x4** run (791.9 CPU-s), not later 2x5 pairs; and its
   ~12 CPU-h is excluded by the recorded run's 16 thread-hours.
4. It omits the strongest datum on disk (`run_targets.sh` T=8 x 7207 s incomplete)
   and withdraws a statement that measurement supports.

Suggested replacement text:

> §6 cites §3; the 2x5 runtime estimate is §4's (0.5-2 h, sequential-equivalent,
> from 55 Python-hours / a 30-100x single-core port speedup). The ">10x" was
> unsupported when written — no completed run, and the log predates `walked`. It is
> nonetheless roughly right: `run_targets.sh` ran 2x5 at `--threads 8` for 7,207 s
> without completing (16.0 thread-hours), and instruction-anchored probes
> (`refute/adjudicate/r5/`) put a complete 2x5 at ~25-40 CPU-hours, i.e. a 12-73x
> overrun in §4's own currency (~2x by wall at 8 threads). Re-cite to §4, keep the
> claim, and give the number instead of the adjective.

## 8. Ground rules

No process signalled. Nothing written outside `rust/refute/adjudicate/r5/`. No git,
no cargo, no rebuild; the audited binary was only executed. Four runs, all
foreground with `--tlimit`, longest 261 s wall; total ~514 CPU-s of my own.
