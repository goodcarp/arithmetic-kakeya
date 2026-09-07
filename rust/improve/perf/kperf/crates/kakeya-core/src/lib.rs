//! Bit-exact Rust reimplementation of `src/fastcore.py` (`force` and `rank`).
//!
//! Semantics are pinned by the S1 kernel contract.  Everything the Python does
//! by accident is reproduced, with the four documented divergences:
//!   * no global `_INV` memo (so no cross-`p` contamination),
//!   * `p < 0` and `p >= 2^32` are `ValueError` instead of "works by accident",
//!   * `n > 2^20` is a `ValueError` guard,
//!   * entries outside `i64` are rejected at the PyO3 boundary.

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum KErr {
    /// row shorter than the column being read
    Index,
    /// `x % 0`
    ZeroDivision,
    Value(String),
}

/// Largest `n` we will build a `U` vector for.  Every driver uses n <= 16.
pub const MAX_N: i64 = 1 << 20;

/// Validate the modulus at the point Python would first evaluate `x % p`.
#[inline]
fn validate_p(p: i64) -> Result<u64, KErr> {
    if p == 0 {
        return Err(KErr::ZeroDivision);
    }
    if p < 0 {
        return Err(KErr::Value(format!(
            "p must be positive (got {p}); the Python reference only works for p < 0 by accident"
        )));
    }
    if p >= (1i64 << 32) {
        return Err(KErr::Value(format!("p must be < 2^32 (got {p})")));
    }
    Ok(p as u64)
}

#[inline(always)]
fn reduce(x: i64, p: u64) -> u64 {
    // Python's `%` is floor-mod: the result is always in [0, p) for p > 0.
    x.rem_euclid(p as i64) as u64
}

/// `pow(a, p - 2, p)` -- exactly what `_inv` computes, including for composite
/// `p`, where the value is deterministic garbage rather than an inverse.
#[inline]
fn fermat_inv(a: u64, p: u64) -> u64 {
    debug_assert!(a != 0, "the reference never calls _inv(0, .)");
    debug_assert!(p >= 2, "no pivot can exist when p == 1");
    let mut base = a % p;
    let mut exp = p - 2;
    let mut acc: u64 = 1 % p;
    while exp > 0 {
        if exp & 1 == 1 {
            acc = (acc * base) % p;
        }
        base = (base * base) % p;
        exp >>= 1;
    }
    acc
}

// ---------------------------------------------------------------------------
// force
// ---------------------------------------------------------------------------

/// Reusable scratch space so a scan's inner loops never allocate.
#[derive(Default)]
pub struct ForceScratch {
    u: Vec<usize>,
    bmat: Vec<u64>,
    prow: Vec<u64>,
    vvec: Vec<u64>,
    piv: Vec<usize>,
    bits: Vec<u64>,
    extras: Vec<i64>,
    /// perf lens only: direct-mapped memo for `fermat_inv` at p = 2^31-1.
    invc: Vec<u64>,
}

impl ForceScratch {
    pub fn new() -> Self {
        Self::default()
    }
}

/// `force(rows, n, T0, p)`.
///
/// `rows` are the raw (unreduced, possibly ragged) integer rows.  The returned
/// vector is the contents of the result set: the in-range members ascending,
/// followed by any out-of-`range(n)` members of `T0` carried through verbatim.
pub fn force(
    rows: &[Vec<i64>],
    n: i64,
    t0: &[i64],
    p: i64,
    sc: &mut ForceScratch,
) -> Result<(bool, Vec<i64>), KErr> {
    if n > MAX_N {
        return Err(KErr::Value(format!("n too large: {n} (max {MAX_N})")));
    }
    let nn: usize = if n > 0 { n as usize } else { 0 };
    let words = nn.div_ceil(64);

    sc.bits.clear();
    sc.bits.resize(words, 0);
    sc.extras.clear();
    let mut count: usize = 0;
    for &e in t0 {
        if e >= 0 && e < n {
            let e = e as usize;
            if sc.bits[e >> 6] & (1u64 << (e & 63)) == 0 {
                sc.bits[e >> 6] |= 1u64 << (e & 63);
                count += 1;
            }
        } else if !sc.extras.contains(&e) {
            sc.extras.push(e);
        }
    }

    loop {
        if (count + sc.extras.len()) as i64 >= n {
            return Ok((true, collect(&sc.bits, nn, &sc.extras)));
        }

        // --- step 1: U (ascending), pos, w ---------------------------------
        sc.u.clear();
        for j in 0..nn {
            if sc.bits[j >> 6] & (1u64 << (j & 63)) == 0 {
                sc.u.push(j);
            }
        }
        let w = 2 * sc.u.len();
        debug_assert!(w > 0);

        // The reference evaluates its first `% p` iff there is a first row and
        // that row is long enough to reach column 2*U[0]; otherwise an
        // IndexError fires first.  Match that ordering.
        let mut pu: u64 = 1;
        let first_read_happens = match rows.first() {
            Some(r0) => 2 * sc.u[0] < r0.len(),
            None => false,
        };
        if first_read_happens {
            pu = validate_p(p)?;
        }

        // --- step 2: build B, dropping rows that are zero on the U-columns --
        sc.bmat.clear();
        sc.bmat.resize(rows.len() * w, 0);
        let mut nb: usize = 0;
        for r in rows {
            let base = nb * w;
            let mut nz = false;
            for (idx, &j) in sc.u.iter().enumerate() {
                let i = 2 * j;
                if i >= r.len() {
                    return Err(KErr::Index);
                }
                let a = reduce(r[i], pu);
                if i + 1 >= r.len() {
                    return Err(KErr::Index);
                }
                let b = reduce(r[i + 1], pu);
                if a != 0 || b != 0 {
                    nz = true;
                    sc.bmat[base + 2 * idx] = a;
                    sc.bmat[base + 2 * idx + 1] = b;
                }
            }
            if nz {
                nb += 1;
            }
            // If nz is false nothing was written, so the slot is still zero and
            // is reused by the next row.
        }

        // --- step 3: full RREF ---------------------------------------------
        sc.piv.clear();
        sc.prow.clear();
        sc.prow.resize(w, 0);
        let mut rk: usize = 0;
        for c in 0..w {
            if rk >= nb {
                break;
            }
            let mut sel = usize::MAX;
            for i in rk..nb {
                if sc.bmat[i * w + c] != 0 {
                    sel = i;
                    break;
                }
            }
            if sel == usize::MAX {
                continue;
            }
            if sel != rk {
                for k in 0..w {
                    sc.bmat.swap(rk * w + k, sel * w + k);
                }
            }
            let iv = fermat_inv(sc.bmat[rk * w + c], pu);
            for k in 0..w {
                let x = sc.bmat[rk * w + k];
                sc.bmat[rk * w + k] = if x == 0 { 0 } else { (x * iv) % pu };
            }
            sc.prow.copy_from_slice(&sc.bmat[rk * w..rk * w + w]);
            for i in 0..nb {
                if i == rk {
                    continue;
                }
                let fac = sc.bmat[i * w + c];
                if fac == 0 {
                    continue;
                }
                let base = i * w;
                for k in 0..w {
                    let b = sc.prow[k];
                    if b != 0 {
                        let a = sc.bmat[base + k];
                        let t = (fac * b) % pu;
                        sc.bmat[base + k] = (a + pu - t) % pu;
                    }
                }
            }
            sc.piv.push(c);
            rk += 1;
        }

        // --- step 4: membership scan, ascending over U ----------------------
        let mut found: Option<usize> = None;
        for (idx, &j) in sc.u.iter().enumerate() {
            let i2 = 2 * idx;
            sc.vvec.clear();
            sc.vvec.resize(w, 0);
            sc.vvec[i2] = 1;
            sc.vvec[i2 + 1] = pu - 1;
            for (q, &c) in sc.piv.iter().enumerate() {
                let fac = sc.vvec[c];
                if fac == 0 {
                    continue;
                }
                let base = q * w;
                for k in 0..w {
                    let b = sc.bmat[base + k];
                    if b != 0 {
                        let a = sc.vvec[k];
                        let t = (fac * b) % pu;
                        sc.vvec[k] = (a + pu - t) % pu;
                    }
                }
            }
            if !sc.vvec.iter().any(|&x| x != 0) {
                found = Some(j);
                break;
            }
        }

        match found {
            None => return Ok((false, collect(&sc.bits, nn, &sc.extras))),
            Some(j) => {
                sc.bits[j >> 6] |= 1u64 << (j & 63);
                count += 1;
            }
        }
    }
}

fn collect(bits: &[u64], nn: usize, extras: &[i64]) -> Vec<i64> {
    let mut out = Vec::with_capacity(extras.len() + 8);
    for j in 0..nn {
        if bits[j >> 6] & (1u64 << (j & 63)) != 0 {
            out.push(j as i64);
        }
    }
    out.extend_from_slice(extras);
    out
}

/// Convenience wrapper that allocates its own scratch.
pub fn force_once(
    rows: &[Vec<i64>],
    n: i64,
    t0: &[i64],
    p: i64,
) -> Result<(bool, Vec<i64>), KErr> {
    let mut sc = ForceScratch::new();
    force(rows, n, t0, p, &mut sc)
}

// ---------------------------------------------------------------------------
// rank
// ---------------------------------------------------------------------------

/// `rank(rows, p)`.  Forward elimination only, all rows kept, width from
/// `rows[0]`, and the `zip` truncation of ragged rows reproduced exactly.
pub fn rank(rows: &[Vec<i64>], p: i64) -> Result<i64, KErr> {
    if rows.is_empty() {
        return Ok(0);
    }
    if rows.iter().all(|r| r.is_empty()) {
        // No `% p` is ever evaluated, and w = len(rows[0]) = 0.
        return Ok(0);
    }
    let pu = validate_p(p)?;

    let mut b: Vec<Vec<u64>> = rows
        .iter()
        .map(|r| r.iter().map(|&x| reduce(x, pu)).collect())
        .collect();
    let w = b[0].len();
    let nb = b.len();
    let mut rk: usize = 0;
    for c in 0..w {
        if rk >= nb {
            break;
        }
        let mut sel = usize::MAX;
        // Indexing is deliberate: the bounds check below must run for every
        // row at or below the pivot, in order, before any element is read.
        #[allow(clippy::needless_range_loop)]
        for i in rk..nb {
            if c >= b[i].len() {
                return Err(KErr::Index);
            }
            if b[i][c] != 0 {
                sel = i;
                break;
            }
        }
        if sel == usize::MAX {
            continue;
        }
        b.swap(rk, sel);
        let iv = fermat_inv(b[rk][c], pu);
        for x in b[rk].iter_mut() {
            if *x != 0 {
                *x = (*x * iv) % pu;
            }
        }
        let (head, tail) = b.split_at_mut(rk + 1);
        let pr: &[u64] = &head[rk];
        for row in tail.iter_mut() {
            if c >= row.len() {
                return Err(KErr::Index);
            }
            let fac = row[c];
            if fac == 0 {
                continue;
            }
            // `zip(B[i], pr)` truncates to the shorter of the two.
            if row.len() > pr.len() {
                row.truncate(pr.len());
            }
            for (k, a) in row.iter_mut().enumerate() {
                let bb = pr[k];
                if bb != 0 {
                    let t = (fac * bb) % pu;
                    *a = (*a + pu - t) % pu;
                }
            }
        }
        rk += 1;
    }
    Ok(rk as i64)
}

#[cfg(test)]
mod tests;

// ===========================================================================
// PERF LENS (improve/perf) -- prototype only.  Not in the audited tree.
// `force_fast` must be bit-identical to `force`; `KAKEYA_KERNEL=fast` selects
// it, `KAKEYA_STATS=1` turns on the call/round counters.
// ===========================================================================

pub mod perf {
    use super::*;
    use std::sync::atomic::{AtomicU64, Ordering::Relaxed};
    use std::sync::OnceLock;

    pub static CALLS: AtomicU64 = AtomicU64::new(0);
    pub static ROUNDS: AtomicU64 = AtomicU64::new(0);
    pub static ROUND_HIST: [AtomicU64; 20] = {
        #[allow(clippy::declare_interior_mutable_const)]
        const Z: AtomicU64 = AtomicU64::new(0);
        [Z; 20]
    };
    pub static SUM_NB: AtomicU64 = AtomicU64::new(0);
    pub static SUM_W: AtomicU64 = AtomicU64::new(0);
    pub static SUM_RK: AtomicU64 = AtomicU64::new(0);
    /// element-ops charged to step 3 (RREF elimination) and step 4 (membership)
    pub static OPS_RREF: AtomicU64 = AtomicU64::new(0);
    pub static OPS_MEMB: AtomicU64 = AtomicU64::new(0);
    pub static OPS_BUILD: AtomicU64 = AtomicU64::new(0);
    pub static OPS_INV: AtomicU64 = AtomicU64::new(0);

    pub fn stats_on() -> bool {
        static F: OnceLock<bool> = OnceLock::new();
        *F.get_or_init(|| std::env::var("KAKEYA_STATS").as_deref() == Ok("1"))
    }
    /// 0 = reference kernel, 1 = all levers, 2 = Mersenne arithmetic only
    /// (reference membership scan), 3 = membership shortcut only (generic
    /// `%`-based arithmetic).  Selected once by `KAKEYA_KERNEL`.
    pub fn mode() -> u8 {
        static F: OnceLock<u8> = OnceLock::new();
        *F.get_or_init(|| match std::env::var("KAKEYA_KERNEL").as_deref() {
            Ok("fast") => 1,
            Ok("mersenne") => 2,
            Ok("memb") => 3,
            Ok("fastcache") => 4,
            _ => 0,
        })
    }
    pub fn fast_on() -> bool {
        mode() != 0
    }
    pub fn dump() -> String {
        let calls = CALLS.load(Relaxed);
        let rounds = ROUNDS.load(Relaxed);
        let mut h = String::new();
        for (i, c) in ROUND_HIST.iter().enumerate() {
            let v = c.load(Relaxed);
            if v > 0 {
                h.push_str(&format!(" r{}={}", i, v));
            }
        }
        format!(
            "STATS calls={} rounds={} rounds_per_call={:.3} mean_nb={:.2} mean_w={:.2} \
mean_rk={:.2} ops_build={} ops_rref={} ops_memb={} ops_inv={} hist:{}",
            calls,
            rounds,
            rounds as f64 / calls.max(1) as f64,
            SUM_NB.load(Relaxed) as f64 / rounds.max(1) as f64,
            SUM_W.load(Relaxed) as f64 / rounds.max(1) as f64,
            SUM_RK.load(Relaxed) as f64 / rounds.max(1) as f64,
            OPS_BUILD.load(Relaxed),
            OPS_RREF.load(Relaxed),
            OPS_MEMB.load(Relaxed),
            OPS_INV.load(Relaxed),
            h
        )
    }

    // --- modulus back-ends -------------------------------------------------
    pub trait Md: Copy {
        fn p(self) -> u64;
        fn red(self, x: i64) -> u64;
        fn mul(self, a: u64, b: u64) -> u64;
        #[inline(always)]
        fn sub(self, a: u64, b: u64) -> u64 {
            // a, b < p  =>  a + p - b < 2p, one conditional subtract, no division
            let x = a + self.p() - b;
            if x >= self.p() {
                x - self.p()
            } else {
                x
            }
        }
        #[inline]
        fn inv(self, a: u64) -> u64 {
            let p = self.p();
            let mut base = a % p;
            let mut exp = p - 2;
            let mut acc: u64 = 1 % p;
            while exp > 0 {
                if exp & 1 == 1 {
                    acc = self.mul(acc, base);
                }
                base = self.mul(base, base);
                exp >>= 1;
            }
            acc
        }
    }

    /// p = 2^31 - 1: `x mod p` by shift-and-add, no 64-bit division anywhere.
    #[derive(Clone, Copy)]
    pub struct M31;
    pub const P31: u64 = (1u64 << 31) - 1;
    impl Md for M31 {
        #[inline(always)]
        fn p(self) -> u64 {
            P31
        }
        #[inline(always)]
        fn red(self, x: i64) -> u64 {
            if x >= 0 && (x as u64) < P31 {
                x as u64
            } else {
                x.rem_euclid(P31 as i64) as u64
            }
        }
        #[inline(always)]
        fn mul(self, a: u64, b: u64) -> u64 {
            let t = a * b; // < 2^62
            let s = (t & P31) + (t >> 31); // < 2^32
            let s = (s & P31) + (s >> 31); // <= P31
            if s >= P31 {
                s - P31
            } else {
                s
            }
        }
    }

    /// Any other modulus: hardware division, but still no `%` on add/sub.
    #[derive(Clone, Copy)]
    pub struct MGen(pub u64);
    impl Md for MGen {
        #[inline(always)]
        fn p(self) -> u64 {
            self.0
        }
        #[inline(always)]
        fn red(self, x: i64) -> u64 {
            x.rem_euclid(self.0 as i64) as u64
        }
        #[inline(always)]
        fn mul(self, a: u64, b: u64) -> u64 {
            (a * b) % self.0
        }
    }

    /// Bit-identical replacement for `force`.  Three changes, all provably
    /// value-preserving:
    ///   1. `p = 2^31-1` uses Mersenne reduction instead of `%`;
    ///   2. `(a + p - t) % p` becomes a conditional subtract (a, t < p);
    ///   3. step 4 tests membership of `e_{c1} - e_{c2}` in the RREF row space
    ///      in O(w) instead of reducing against every pivot row: in a *reduced*
    ///      row echelon form the reduction coefficient of pivot row q is the
    ///      untouched original v[piv[q]], and v has at most two nonzeros, so at
    ///      most two pivot rows can contribute.
    pub fn force_fast(
        rows: &[Vec<i64>],
        n: i64,
        t0: &[i64],
        p: i64,
        sc: &mut ForceScratch,
    ) -> Result<(bool, Vec<i64>), KErr> {
        if n > MAX_N {
            return Err(KErr::Value(format!("n too large: {n} (max {MAX_N})")));
        }
        let nn: usize = if n > 0 { n as usize } else { 0 };
        let words = nn.div_ceil(64);

        sc.bits.clear();
        sc.bits.resize(words, 0);
        sc.extras.clear();
        let mut count: usize = 0;
        for &e in t0 {
            if e >= 0 && e < n {
                let e = e as usize;
                if sc.bits[e >> 6] & (1u64 << (e & 63)) == 0 {
                    sc.bits[e >> 6] |= 1u64 << (e & 63);
                    count += 1;
                }
            } else if !sc.extras.contains(&e) {
                sc.extras.push(e);
            }
        }
        if stats_on() {
            CALLS.fetch_add(1, Relaxed);
        }

        let mut nrounds = 0u64;
        loop {
            if (count + sc.extras.len()) as i64 >= n {
                if stats_on() {
                    ROUND_HIST[(nrounds as usize).min(19)].fetch_add(1, Relaxed);
                }
                return Ok((true, collect(&sc.bits, nn, &sc.extras)));
            }
            nrounds += 1;

            sc.u.clear();
            for j in 0..nn {
                if sc.bits[j >> 6] & (1u64 << (j & 63)) == 0 {
                    sc.u.push(j);
                }
            }
            let w = 2 * sc.u.len();

            let first_read_happens = match rows.first() {
                Some(r0) => 2 * sc.u[0] < r0.len(),
                None => false,
            };
            let pu: u64 = if first_read_happens { validate_p(p)? } else { 1 };

            let md = mode();
            let shortcut = md != 2;
            let cache = md == 4;
            let r = if pu == P31 && md != 3 {
                round::<M31>(M31, rows, w, pu, shortcut, cache, sc)?
            } else {
                round::<MGen>(MGen(pu), rows, w, pu, shortcut, false, sc)?
            };
            if stats_on() {
                ROUNDS.fetch_add(1, Relaxed);
            }
            match r {
                None => {
                    if stats_on() {
                        ROUND_HIST[(nrounds as usize).min(19)].fetch_add(1, Relaxed);
                    }
                    return Ok((false, collect(&sc.bits, nn, &sc.extras)));
                }
                Some(j) => {
                    sc.bits[j >> 6] |= 1u64 << (j & 63);
                    count += 1;
                }
            }
        }
    }

    /// One round: build B, full RREF, membership scan.  Returns the forced
    /// vertex (a member of `sc.u`) or None.
    #[inline]
    fn round<M: Md>(
        m: M,
        rows: &[Vec<i64>],
        w: usize,
        pu: u64,
        shortcut: bool,
        cache: bool,
        sc: &mut ForceScratch,
    ) -> Result<Option<usize>, KErr> {
        // --- step 2: build B ------------------------------------------------
        sc.bmat.clear();
        sc.bmat.resize(rows.len() * w, 0);
        let mut nb: usize = 0;
        for r in rows {
            let base = nb * w;
            let mut nz = false;
            for (idx, &j) in sc.u.iter().enumerate() {
                let i = 2 * j;
                if i >= r.len() {
                    return Err(KErr::Index);
                }
                let a = m.red(r[i]);
                if i + 1 >= r.len() {
                    return Err(KErr::Index);
                }
                let b = m.red(r[i + 1]);
                if a != 0 || b != 0 {
                    nz = true;
                    sc.bmat[base + 2 * idx] = a;
                    sc.bmat[base + 2 * idx + 1] = b;
                }
            }
            if nz {
                nb += 1;
            }
        }
        if stats_on() {
            SUM_NB.fetch_add(nb as u64, Relaxed);
            SUM_W.fetch_add(w as u64, Relaxed);
            OPS_BUILD.fetch_add((rows.len() * w) as u64, Relaxed);
        }

        // --- step 3: full RREF ----------------------------------------------
        sc.piv.clear();
        sc.prow.clear();
        sc.prow.resize(w, 0);
        let mut rk: usize = 0;
        let mut ops: u64 = 0;
        // Every pivot scaled to exactly 1 at its own step?  If so the result is
        // a genuine RREF (each pivot column is then cleared in every other row,
        // and later pivot rows carry 0 in earlier pivot columns, so nothing
        // disturbs it).  `fermat_inv` is `pow(a, p-2, p)` verbatim, which is a
        // true inverse only for prime p, so for composite p this can fail --
        // and then the O(w) membership shortcut is invalid.  Checking the FINAL
        // pivot entries is NOT enough: a later elimination can restore a 1 in a
        // pivot slot that was never actually 1 when it mattered (p = 91,
        // rows [[-5, 2147483649], ...], n = 1 -- caught by the differential).
        let mut genuine = true;
        for c in 0..w {
            if rk >= nb {
                break;
            }
            let mut sel = usize::MAX;
            for i in rk..nb {
                if sc.bmat[i * w + c] != 0 {
                    sel = i;
                    break;
                }
            }
            if sel == usize::MAX {
                continue;
            }
            if sel != rk {
                for k in 0..w {
                    sc.bmat.swap(rk * w + k, sel * w + k);
                }
            }
            let pivval = sc.bmat[rk * w + c];
            let iv = if cache {
                inv_cached(&mut sc.invc, pivval)
            } else {
                m.inv(pivval)
            };
            for k in 0..w {
                let x = sc.bmat[rk * w + k];
                sc.bmat[rk * w + k] = if x == 0 { 0 } else { m.mul(x, iv) };
            }
            if sc.bmat[rk * w + c] != 1 {
                genuine = false;
            }
            sc.prow.copy_from_slice(&sc.bmat[rk * w..rk * w + w]);
            for i in 0..nb {
                if i == rk {
                    continue;
                }
                let fac = sc.bmat[i * w + c];
                if fac == 0 {
                    continue;
                }
                let base = i * w;
                ops += w as u64;
                for k in 0..w {
                    let b = sc.prow[k];
                    if b != 0 {
                        let a = sc.bmat[base + k];
                        sc.bmat[base + k] = m.sub(a, m.mul(fac, b));
                    }
                }
            }
            sc.piv.push(c);
            rk += 1;
        }
        if stats_on() {
            SUM_RK.fetch_add(rk as u64, Relaxed);
            OPS_RREF.fetch_add(ops, Relaxed);
            OPS_INV.fetch_add(rk as u64, Relaxed);
        }

        // --- step 4: membership scan ----------------------------------------
        // The O(w) shortcut below is valid only when step 3 produced a GENUINE
        // reduced row echelon form, i.e. every pivot entry is exactly 1.  That
        // holds for prime p, but `fermat_inv` is `pow(a, p-2, p)` verbatim, so
        // for composite p (the reference's "deterministic garbage" case) the
        // pivot need not be 1 and the pivot columns are not cleared.  Check,
        // and fall back to the reference's own reduction when it fails.
        if !genuine || !shortcut {
            return round_slow(m, w, pu, sc);
        }
        // pivrow[c] = index of the RREF row whose pivot column is c.
        sc.vvec.clear();
        sc.vvec.resize(w, u64::MAX);
        for (q, &c) in sc.piv.iter().enumerate() {
            sc.vvec[c] = q as u64;
        }
        let pm1 = pu - 1;
        let mut memb_ops: u64 = 0;
        for (idx, &j) in sc.u.iter().enumerate() {
            let c1 = 2 * idx;
            let c2 = c1 + 1;
            let q1 = sc.vvec[c1];
            let q2 = sc.vvec[c2];
            memb_ops += w as u64;
            let hit = match (q1 == u64::MAX, q2 == u64::MAX) {
                (false, false) => {
                    // e_{c1}-e_{c2} - R_q1 + R_q2 == 0  <=>  R_q1 and R_q2 agree
                    // off {c1, c2} (they already differ correctly on c1, c2).
                    let a = (q1 as usize) * w;
                    let b = (q2 as usize) * w;
                    let mut eq = true;
                    for k in 0..w {
                        if k == c1 || k == c2 {
                            continue;
                        }
                        if sc.bmat[a + k] != sc.bmat[b + k] {
                            eq = false;
                            break;
                        }
                    }
                    eq
                }
                (false, true) => {
                    // need R_q1 == e_{c1} - e_{c2}
                    let a = (q1 as usize) * w;
                    let mut eq = sc.bmat[a + c2] == pm1;
                    if eq {
                        for k in 0..w {
                            if k == c1 || k == c2 {
                                continue;
                            }
                            if sc.bmat[a + k] != 0 {
                                eq = false;
                                break;
                            }
                        }
                    }
                    eq
                }
                (true, false) => {
                    // need R_q2 == e_{c2} - e_{c1}
                    let b = (q2 as usize) * w;
                    let mut eq = sc.bmat[b + c1] == pm1;
                    if eq {
                        for k in 0..w {
                            if k == c1 || k == c2 {
                                continue;
                            }
                            if sc.bmat[b + k] != 0 {
                                eq = false;
                                break;
                            }
                        }
                    }
                    eq
                }
                (true, true) => false,
            };
            if hit {
                if stats_on() {
                    OPS_MEMB.fetch_add(memb_ops, Relaxed);
                }
                return Ok(Some(j));
            }
        }
        if stats_on() {
            OPS_MEMB.fetch_add(memb_ops, Relaxed);
        }
        Ok(None)
    }

    /// Direct-mapped memo for the p = 2^31-1 Fermat inverse.  `pow(a, p-2, p)`
    /// is a pure function of `a`, so memoising it cannot change any value; the
    /// table is per-worker (in `ForceScratch`), never global, so there is no
    /// cross-`p` contamination of the kind the reference's `_INV` has.
    #[inline]
    fn inv_cached(c: &mut Vec<u64>, a: u64) -> u64 {
        const N: usize = 8192;
        if c.len() != N {
            c.clear();
            c.resize(N, 0);
        }
        let i = (a as usize) & (N - 1);
        let e = c[i];
        if (e >> 32) == a {
            return e & 0xffff_ffff;
        }
        let v = M31.inv(a);
        c[i] = (a << 32) | v;
        v
    }

    /// The reference membership scan, verbatim, but with `M`'s division-free
    /// add/sub.  Used when the echelon form is not genuine (composite p).
    fn round_slow<M: Md>(
        m: M,
        w: usize,
        pu: u64,
        sc: &mut ForceScratch,
    ) -> Result<Option<usize>, KErr> {
        let u = std::mem::take(&mut sc.u);
        let mut found = None;
        for (idx, &j) in u.iter().enumerate() {
            let i2 = 2 * idx;
            sc.vvec.clear();
            sc.vvec.resize(w, 0);
            sc.vvec[i2] = 1;
            sc.vvec[i2 + 1] = pu - 1;
            for (q, &c) in sc.piv.iter().enumerate() {
                let fac = sc.vvec[c];
                if fac == 0 {
                    continue;
                }
                let base = q * w;
                for k in 0..w {
                    let b = sc.bmat[base + k];
                    if b != 0 {
                        sc.vvec[k] = m.sub(sc.vvec[k], m.mul(fac, b));
                    }
                }
            }
            if !sc.vvec.iter().any(|&x| x != 0) {
                found = Some(j);
                break;
            }
        }
        sc.u = u;
        Ok(found)
    }

    /// Runtime-selected kernel: `KAKEYA_KERNEL=fast` -> `force_fast`.
    #[inline]
    pub fn force_sel(
        rows: &[Vec<i64>],
        n: i64,
        t0: &[i64],
        p: i64,
        sc: &mut ForceScratch,
    ) -> Result<(bool, Vec<i64>), KErr> {
        if fast_on() {
            force_fast(rows, n, t0, p, sc)
        } else {
            if stats_on() {
                CALLS.fetch_add(1, Relaxed);
            }
            force(rows, n, t0, p, sc)
        }
    }
}
