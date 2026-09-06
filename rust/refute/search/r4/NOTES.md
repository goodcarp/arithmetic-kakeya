# r4 — closing pass over r3's report, 2026-09-06 ~15:40–16:10 EDT

Not a new refutation attempt.  This pass read r3's `FINDINGS.md`, re-measured
every claim in it that touched the record, and corrected the record where the
measurement disagreed.  Corrections are appended to r3's own `FINDINGS.md`
(section "Corrections", C1–C5) rather than edited into its text.

Everything here was run from the CLI against the 15:33 binary
(sha256 `add554183aaa3d7cf1f2d468ba11e39926aea035853809811af4e6c40010fcf9`)
on a machine also running the 8-cycle job at ~470% CPU, so wall-clock numbers
are contended.

## What changed in the record
`crates/kakeya-search/PROGRESS.md`:
- lines 7, 8, 36: `12/12` -> `16/16`, `11 PASS` -> `14 PASS, 2 SKIP, 0 FAIL`
  (r3 Finding D, confirmed by independent re-measurement).
- the g2_tall `complete` bullet: added scope showing r3's Finding B is a shim
  artefact and the original wording stands.
- the C6 OPEN bullet on the allocation abort: re-scoped to the post-fix
  boundary, with the smallest live repro (`--pool 3`, not `--pool 8`).
- the cycles8 POOL3 bullet and its coverage-map row: kernel disclosure — the
  Python side ran the PyO3 kernel, so the row checks the driver port with the
  kernel held fixed.

`~/Desktop/.claude/workflows/kakeya-verify-only.js` and
`kakeya-verify-remaining.js`: the CLAIM string carried the stale `12/12`, which
would have sent a future refuter to rediscover Finding D.  Replaced with the
measured figures plus a do-not-re-report list (the three known disclosed
limits) and a warning about the 700-constant shim trap.

## Files here
- `rate_c8.py` — measures the pure-Python cycles8 rate by running
  `cycles8.main` under a short tlimit and reporting `tested`/second.
  Measured POOL3: **5.22 pairs/s** (779 pairs in 149 s).  So a full
  pure-Python POOL3 oracle is ~93 min of CPU, not the ~36 h that
  extrapolating the POOL6 rate (0.22 pairs/s) suggests.  POOL6 pairs are much
  more expensive than POOL3 pairs; do not extrapolate across pool sizes.

## Left running deliberately
`py_drv.sh C8 cycles8 3` (pid 13369), orphaned by the account switch, is the
pure-Python POOL3 oracle that would close the kernel-disclosure gap outright.
At 16:00 EDT it had 25 of the ~93 min of CPU it needs and was getting ~21% of
a core.  Result lands in `../r3/out/C8.py.txt`.  Killing it would have thrown
away 25 minutes of CPU for nothing.

## Verdicts on r3
| r3 item | verdict |
|---|---|
| A  g2-tall RESULT has 3 Rust-only keys | stands; already documented |
| B  `complete` disagrees under 700 s | **RETRACTED** — shim artefact (its own Finding E class) |
| C  `--target` rejects decimals | stands; input-domain narrowing |
| D  `check` miscount 12/12 | **CONFIRMED**; record fixed |
| E  seed 123 divergence | already self-retracted by r3 |
| F  allocation abort under `--tlimit` | **CONFIRMED, still live**, narrower than stated |
| G  `--tlimit` not a wall-clock bound | stands; already OPEN in the record |
| §6 heading "re-verified against a PURE-PYTHON oracle" | **unsupported** — Python side never returned |
| §7 "shipped binary does not contain that string" | **stale by one minute**; the rebuild landed 15:33 |

Net: of r3's seven findings, one retracted, one confirmed-and-fixed, one
confirmed-and-live, four already-known.  Its most valuable contribution was
the opening sentence of section 6 — the kernel substitution in the cycles8
row — which its own section then overclaimed as closed.
