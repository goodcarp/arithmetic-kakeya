  » order                          
  ⇢ route           antigravity-cli — kind=code; ranked 1 ready; chose antigravity-cli (cost_class 1)
  → invoke          antigravity-cli 
  ▣ deposit         antigravity-cli (3850 chars, 30.67s, sha 592ba1b1ad)

────────────────────────────────────────────────────────────────────────
### 1. Negative Entries and `%` Semantics
* **Issue**: Python's `%` operator uses floored division (`(-1) % 5 == 4`), whereas Rust's `%` operator is remainder (`-1 % 5 == -1`). Subtractions `(a - fac * b) % p` and inputs with negative values always result in non-negative residues in `[0, p - 1]`.
* **Python Call**: `rank([[-1, 2]], p=5)`
* **Exact Return**: `1`

---

### 2. Non-Prime `p`
* **Issue**: If `p` is composite, `pow(a, p - 2, p)` is not the modular inverse for `gcd(a, p) != 1`. Python computes it without error, potentially scaling pivot rows to zero (e.g., `pow(2, 2, 4) == 0`), but `rk` is still incremented.
* **Python Call**: `rank([[2, 0]], p=4)`
* **Exact Return**: `1`

---

### 3. Modular Inverse of Zero via `pow(a, p - 2, p)`
* **Issue**: `_inv(0, p)` computes `pow(0, p - 2, p)`. For `p > 2`, this evaluates to `0` (and for `p = 2`, `pow(0, 0, 2) == 1`). A Rust port using extended GCD or checked division would panic or return an error on `0`.
* **Python Call**: `_inv(0, p=5)`
* **Exact Return**: `0`

---

### 4. Arithmetic Overflow of `a * b` near $2^{62}$
* **Issue**: For `p = P = 2^31 - 1`, intermediate products `fac * b` reach $(P - 1)^2 \approx 4.61 \times 10^{18} < 2^{62}$, overflowing 32-bit integers. If `p` or entries exceed $2^{31}$, expressions like `(a - fac * b) % p` overflow signed 64-bit integer (`i64`) arithmetic, while Python handles arbitrary precision.
* **Python Call**: `rank([[1 << 62, 1]], p=5)`
* **Exact Return**: `1`

---

### 5. Entries $\ge p$
* **Issue**: Entries are reduced modulo $p$ upon loading into `B` (`r[2 * j] % p`). Any entry that is a non-zero multiple of $p$ becomes `0` and can cause a row to be treated as all-zero and skipped.
* **Python Call**: `force([[7, 7]], 1, [], p=7)`
* **Exact Return**: `(False, set())`

---

### 6. Pivot and Found-Vertex Scan Order
* **Issue**: 
  - Pivot selection searches rows in increasing index order `rk..nB` and selects the first row with a non-zero entry at column `c` (no maximum-pivot search).
  - Vertex testing checks `j in U` in increasing index order. When multiple unforced vertices are simultaneously forced, the lowest index $j$ is picked first, added to `T`, and the search restarts.
* **Python Call**: `force([[1, P - 1, 0, 0], [0, 0, 1, P - 1]], 2, [])`
* **Exact Return**: `(True, {0, 1})`

---

### 7. `T0` with Out-of-Range or Duplicate Indices
* **Issue**: `T = set(T0)` deduplicates elements. The loop termination condition is `while len(T) < n:`. If `T0` contains duplicate indices, negative indices, or indices $\ge n$, `len(T)` includes them. If `len(set(T0)) >= n`, the loop exits immediately and returns `(True, T)` without forcing vertices in `0..n-1`.
* **Python Call**: `force([], 1, [99])`
* **Exact Return**: `(True, {99})`

---

### 8. Empty, All-Zero, or Ragged Rows
* **Issue**:
  - `rank([], p=P)` returns `0`.
  - All-zero rows in `force` (`nz == False`) are omitted from `B`.
  - In `force`, extra columns in `rows` beyond $2n$ are ignored because indexing is strictly bounded by `2 * pos[j] + 1`. Short rows raise `IndexError`.
* **Python Call**: `force([[1, P - 1, 999, 888]], 1, [])`
* **Exact Return**: `(True, {0})`

---

### 9. Mutation of Inputs and Global Cache State
* **Issue**:
  - `force` and `rank` do not mutate `rows` or `T0` (`T = set(T0)` creates a new set).
  - `_INV` is a global module-level dictionary keyed only by `a` (ignoring `p`). Calling `_inv(a, p2)` after `_inv(a, p1)` returns the cached value computed under `p1`.
* **Python Call**:
```python
_INV.clear()
_inv(2, p=5)
_inv(2, p=7)
```
* **Exact Return**: `3`

---

### 10. Return Types
* **Issue**: `force` returns a 2-tuple of `(bool, set[int])` (a native Python set, not a list, vector, or boolean array). `rank` returns a native Python `int`.
* **Python Call**: `force([], 1, [])`
* **Exact Return**: `(False, set())`
────────────────────────────────────────────────────────────────────────
  1 deposit(s) · 0 molt(s) · 30.8s · verify: ✔ · head 938b0ee58668
EXIT=0
