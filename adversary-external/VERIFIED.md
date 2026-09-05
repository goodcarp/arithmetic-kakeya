# External reviews of fastcore.py — what held up (verified 2026-09-04)

Sources: gemini-fastcore.md (Gemini 3.8 Flash via antigravity-cli, text-only retry), grok-fastcore.md (Grok 4.6 via grok-cli, 333 s). Both invoked through `supercli ask`, so both are on the supercli ledger. Every claim below was re-run against `/usr/bin/python3` with `KAKEYA_PURE_PY=1` and `fastcore._INV.clear()` before each call.

## Confirmed traps a Rust port must reproduce

| # | Call | Python result | Why it bites a port |
|---|---|---|---|
| 1 | `rank([[-1,2]], p=5)` | `1` | Python `%` is floored; Rust `%` keeps the sign. Use `rem_euclid`. |
| 2 | `rank([[2,0]], p=4)` | `1` | `pow(2,2,4)==0` zeroes the pivot row and `rk` still increments. Do not "fix" with ext-GCD. |
| 3 | `_inv(0,5)` | `0` | `pow(0,p-2,p)==0` for p>2. No panic, no error. |
| 4 | `rank([[1<<62, 1]], p=5)` | `1` | Python bigints; entries are reduced on load. Reduce before multiplying, use u128 or reduce operands to < p first. |
| 5 | `force([[7,7]],1,[],p=7)` | `(False, set())` | Multiples of p become zero rows and are dropped. |
| 6 | `force([[0,0,1,-1]],2,[])` | `(False, {1})` | Found-vertex scan is ascending j in U; partial T is returned on failure. |
| 7 | `force([],1,[99])` | `(True, {99})` | `len(set(T0)) >= n` short-circuits; out-of-range indices count. |
| 8 | `force([[1,-1]],1,[2,2])` | `(True, {2})` | Duplicates in T0 collapse via `set()`. |
| 9 | `force([],2,[0,0,7])` | `(True, {0, 7})` | Same. |
| 10 | `rank([[2147483647]])` | `0` | P % P == 0. `rank([[2147483648]])` is `1`. |
| 11 | `rank([[]])` | `0` | `w = len(B[0]) = 0`, loop never runs. |
| 12 | `rank([[1,2],[3]])` | raises `IndexError` | Ragged rows: the port must raise, not return. |
| 13 | `force([[1]],1,[])` | raises `IndexError` | Short row: `r[2*j+1]` out of range. |
| 14 | `rank([[2,1],[0,2]], p=4)` | `2` | Non-prime p, pivot order left-to-right, first non-zero row from rk. |
| 15 | `force([[2,2]],1,[],p=4)` | `(False, set())` | Non-prime p again. |
| 16 | `force([[1,-1]],1,s)` with `s=set()` | `(True, {0})`, `s` unchanged | Inputs are never mutated; returned set is fresh. |

## The one that matters for the differential test: `_INV` is keyed by `a` only

`_INV` is a module-global dict keyed on `a`, ignoring `p`. After `_inv(2,5)` (=3), `_inv(2,7)` returns 3 instead of 4. Demonstration:

```
fresh process:                 force([[2,0],[0,2]],1,[]) -> (True, {0})
after any earlier p=4 call:    force([[2,0],[0,2]],1,[]) -> (False, set())
```

Consequences:
- No driver ever passes a non-default `p` (grep of src/ finds none), so production results are unaffected.
- A differential test that varies `p` inside one Python process will report phantom mismatches that are the Python's fault, not the Rust's. Either clear `fastcore._INV` between calls, or run each `p` in its own process, or compare at the default `p` only.
- A Rust kernel that computes the correct inverse per `p` is "wrong" relative to the poisoned Python and right relative to the fresh Python. Reproducing the cache is not worth it; document the divergence instead.

## Not confirmed / not applicable
- Gemini's overflow framing ("i64 overflow if p or entries exceed 2^31") is right in spirit; entries are reduced mod p on load so operands are < p, and (p-1)^2 < 2^62 fits i64/u64 for the default P. Only a caller-supplied p >= 2^32 would need u128.
