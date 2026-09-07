# Adjudication r5 — finding 5/10 (lens `perf`): "prototype kernel 4.7x faster, byte-identical"

Verdict: **real = true. Not refuted.** Every gate re-ran clean on my own runs, including on a
corpus I generated myself with a fresh seed. Three overstatements found, none of which touch
the headline; listed in section 6.

## 0. Artifacts tested (sha256)

| file | sha256 |
|---|---|
| `rust/target/release/kakeya-search` (audited) | `add554183aaa3d7cf1f2d468ba11e39926aea035853809811af4e6c40010fcf9` (matches the brief) |
| `rust/improve/perf/kperf/target/release/kakeya-search` (prototype) | `c9ade8f06d9f51d070a83e6d04f2378c4aaab1ec6a0aab2a0f80eee2d1675bb4` |
| `rust/improve/perf/kperf/target/release/xdiff` | `cc41fe65e7c60706af4eaf2fb9634543d363098c3b1b72fc90ed06180bffd463` |
| `rust/improve/perf/diff/cases_big.txt` | `c236424a725cc0fb9da2014b70ab223bef3e53e111d1a755608e9ff57edcdc11` |

Binaries were NOT rebuilt (target/ present). Staleness check: `crates/kakeya-core/src/lib.rs`
17:09:33 -> `libkakeya_core.rlib` 17:09:36 -> `xdiff` 17:09:58 -> `kakeya-search` 17:10:51.
Every binary post-dates every source file, so this is not the "fix missing from a binary
rebuilt a minute earlier" failure mode.

**Contention disclosure.** My load averages were 246-365 (the lens reported 16-56). Absolute
seconds below are much worse than the lens's; the *ratios* are the result.

## 1. Prototype's own differential gate, re-run on the lens's corpus

```
cd rust/improve/perf
./kperf/target/release/xdiff diff/cases_big.txt
  xdiff: 27951 cases | base!=py 0 | fast!=py 0 | base!=fast 0     (real 7.44 user 2.05)
KAKEYA_KERNEL=fastcache ./kperf/target/release/xdiff diff/cases_big.txt
  xdiff: 27951 cases | base!=py 0 | fast!=py 0 | base!=fast 0     (real 7.52 user 1.93)
```

## 2. Independent corpus (my seed, not the lens's) — the stronger check

I regenerated a corpus from scratch rather than trusting `cases_big.txt`:

```
cd rust/improve/perf/diff
/usr/bin/python3 gen_cases.py <r5>/cases_r5.txt 3000 1500 1500 771131
  cases written: 7990          (real 50.8s)
moduli: 1000000007 x1010 | 2147483647 x3845 | 7 x959 | 91 x1068 | 97 x1108
```

`gen_cases.py` sets `os.environ["KAKEYA_PURE_PY"]="1"` before `import fastcore` and asserts
`fastcore.force is fastcore._force_py`; it also clears `fastcore._INV` before every case, so
the known cross-p inverse-cache quirk is handled. I verified the env switch independently:

```
KAKEYA_PURE_PY=1 python3 -c "import fastcore; print(fastcore.force is fastcore._force_py)"  -> True
              python3 -c "import fastcore; print(fastcore.force is fastcore._force_py)"  -> False
```

So this IS a Rust-vs-pure-Python differential, not a PyO3-on-both-sides driver check.

All five kernel modes on the fresh corpus:

```
unset     : xdiff: 7990 cases | base!=py 0 | fast!=py 0 | base!=fast 0
mersenne  : xdiff: 7990 cases | base!=py 0 | fast!=py 0 | base!=fast 0
memb      : xdiff: 7990 cases | base!=py 0 | fast!=py 0 | base!=fast 0
fast      : xdiff: 7990 cases | base!=py 0 | fast!=py 0 | base!=fast 0
fastcache : xdiff: 7990 cases | base!=py 0 | fast!=py 0 | base!=fast 0
```

`base!=py 0` on my own corpus also re-confirms the copied audited kernel, so the harness is
not self-fulfilling. 1068 of these cases are the composite modulus p=91 — the case that broke
two earlier versions of lever B — and the pivot-1 fallback held.

## 3. The byte-identity run the brief asked for (cycles8 pool 3, threads 2)

```
( /usr/bin/time -p ./target/release/kakeya-search cycles8 --pool 3 --target 67/40 --deg 2 \
    --patterns 8cycle --threads 2 > c8p3_t2_audited.txt ) 2>&1
  real 115.51  user 49.83  sys 1.26
( KAKEYA_KERNEL=fastcache /usr/bin/time -p \
  ./improve/perf/kperf/target/release/kakeya-search cycles8 --pool 3 --target 67/40 --deg 2 \
    --patterns 8cycle --threads 2 > c8p3_t2_proto.txt ) 2>&1
  real 23.84   user 10.81  sys 0.27
diff c8p3_t2_audited.txt c8p3_t2_proto.txt   -> (no output)
md5 both = b3782439d36f2a5676d99e9cc305f135
```

8 lines, no masking of any kind. Tail line:
`RESULT {"tag": "cycles8", "pool": 3, "best": null, "hits": 0, "tested": 3948, "patterns": [2, 3]}`

**user-CPU ratio 49.83 / 10.81 = 4.61x** (lens claimed 4.76x at threads 1). Wall 4.84x, but
wall at load 300 is meaningless.

## 4. Second workload + the `check` gate

`scan n4_p6_t1` (`scan --tag n4_p6_t1 --d 2x2 --pool 6 --max-t 1 --target 7/4 --threads 1`),
two reps back to back:

| rep | audited user s | prototype `fastcache` user s | ratio |
|---|---|---|---|
| 1 | 2.96 | 0.59 | 5.02x |
| 2 | 3.12 | 0.62 | 5.03x |

241 lines, identical after masking `"seconds"` only (the sole differing line is RESULT's
`"seconds": 9.5` vs `1.9`). Ratio came in *above* the claimed 4.67x under my heavier load.

Attribution control (rules out "the prototype binary is faster for an unrelated reason"):
prototype with `KAKEYA_KERNEL` **unset** = 3.19 user s, i.e. slightly *slower* than the
audited 2.96/3.12, and its output is masked-identical. The 5x is the kernel selection.

`check --threads 2`: both binaries `CHECK PASS (0 failed)`, 14 PASS / 2 SKIP / 0 FAIL,
outputs identical after masking `[Ns]` only.

## 5. Mersenne guard (the brief's specific ask) — safe

Dispatch, `perf::force_fast`:
```rust
let pu: u64 = if first_read_happens { validate_p(p)? } else { 1 };
let r = if pu == P31 && md != 3 { round::<M31>(M31, ..., cache, ...) }
        else                    { round::<MGen>(MGen(pu), ..., false, ...) };
```
* `P31 = (1u64 << 31) - 1 = 2147483647`. The Mersenne path is taken on **exact equality**
  with 2^31-1, nothing else. Every other modulus in the corpus (7, 91, 97, 1000000007) takes
  `MGen`, i.e. the hardware-division path.
* `validate_p` (audited, unchanged) rejects `p == 0` (ZeroDivision), `p < 0` (Value), and
  `p >= 2^32` (Value), so `pu in [1, 2^32)`. `MGen::mul` is `(a*b) % p` with `a,b < p < 2^32`
  -> `a*b < 2^64`, no overflow. `M31::mul` has `a,b < 2^31` -> `t < 2^62`, and the two
  fold-and-add steps land in `[0, P31)`.
* The pivot-inverse memo is reached **only** inside the `M31` branch: the `MGen` call site
  passes `cache = false` literally. So the 8192-entry table can never be populated at one
  modulus and read at another — it is not the `fastcore._INV` bug reimported. The entry is
  tagged (`(a << 32) | v`, checked as `(e >> 32) == a`), and `a != 0` always because the
  pivot is selected on `bmat != 0`, so the all-zero initial state cannot false-hit.
* Lever B's validity guard is recorded **at each pivot's own step** (`if bmat[rk*w+c] != 1
  { genuine = false }`), not on the final array — which is the correct fix for the p=91
  counterexample the lens documents. `!genuine` falls back to `round_slow`, the reference
  scan. Prime p always passes, so the drivers (P = 2^31-1) always take the fast path.

## 6. Overstatements found (none overturn the finding)

1. **REPORT.md sec 8 claims `crates/kakeya-core/src/lib.rs` "lines 1-368 byte-identical to
   the audited crate (verified by diff)". That is false.** Two lines are *inserted* into
   `ForceScratch` at kperf lines 78-79:
   ```
   /// perf lens only: direct-mapped memo for `fermat_inv` at p = 2^31-1.
   invc: Vec<u64>,
   ```
   so the audited 368 lines map to kperf lines 1-370, and `#[cfg(test)] mod tests;` was
   dropped. `diff <(head -368 kperf/.../lib.rs) crates/.../lib.rs` -> `78,79d77` + `368a367,368`.
   The added field is unused by `force` itself, and `base!=py 0` on two independent corpora
   confirms the copied kernel still reproduces pure Python — so this is a wrong provenance
   sentence, not a defect. It should read "the audited crate verbatim plus one unused
   `ForceScratch` field".
2. **The finding card's "No API change, no change to search.rs or any driver" is wrong about
   the prototype as built** (it is true of the *recommended* port in REPORT sec 9). The
   prototype does change `search.rs` — `use kakeya_core::{force, ForceScratch}` becomes
   `use kakeya_core::perf::force_sel as force;` — and `main.rs` gains a STATS hook. REPORT
   sec 8 discloses both; the card lost the caveat. The rest of `search.rs` is byte-identical
   (`diff` shows only that import), so the DFS really is untouched.
3. **`rzero` is in the "eight further driver streams ... all diff-clean" list, but the rzero
   driver was never rerouted to the fast kernel**, so its diff-clean is vacuous:
   `drivers/rzero.rs:5 use kakeya_core::force;` is byte-identical between the two trees
   (`diff crates/kakeya-search/src/drivers/rzero.rs improve/perf/kperf/.../rzero.rs` -> empty).
   Only `search.rs:142` (the DFS `extend` path) goes through `force_sel`. Consequence for the
   campaign: **rzero gets 0x speedup from this prototype**, and the two rzero streams supply
   no evidence about the fast kernel. The scan/cycles8 headline is unaffected — those do run
   through `extend`.
4. Not an error, but worth recording: the extrapolation in REPORT sec 7 (POOL6 ~4.3x
   whole-run, "24 min instead of 104") remains an extrapolation. I measured POOL3 only.

## 7. What I did not test

`rank` (untouched by the prototype); POOL4/POOL6 timings; the `--threads 12` path; adoption
into the audited tree. The 8-cycle POOL6 job had already finished; I started, killed and
signalled nothing.

Files written (all under this directory): `cases_r5.txt`, `c8p3_t2_{audited,proto}.txt`,
`scan_{aud,pro,pro_unset}.txt`, `check_{aud,pro}.txt`, `{a,b,ca,cb}.m`, this file.
