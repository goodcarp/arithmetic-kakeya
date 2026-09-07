//! CPython's `random.Random(int_seed)` -- MT19937 with `init_by_array` seeding
//! -- and `random.choice`, so the sampled (`limit`-capped) sweeps reproduce
//! byte-for-byte.  Validated against `rust/GOLDEN-VECTORS.json:rng_vectors`.

const N: usize = 624;
const M: usize = 397;
const MATRIX_A: u32 = 0x9908b0df;
const UPPER_MASK: u32 = 0x8000_0000;
const LOWER_MASK: u32 = 0x7fff_ffff;

pub struct PyRandom {
    mt: [u32; N],
    mti: usize,
}

impl PyRandom {
    fn init_genrand(s: u32) -> PyRandom {
        let mut mt = [0u32; N];
        mt[0] = s;
        for i in 1..N {
            let prev = mt[i - 1];
            mt[i] = 1812433253u32
                .wrapping_mul(prev ^ (prev >> 30))
                .wrapping_add(i as u32);
        }
        PyRandom { mt, mti: N }
    }

    /// `random_seed` for a non-negative int: the little-endian 32-bit limbs of
    /// `abs(seed)` (a single zero limb when the seed is 0).
    pub fn seed(seed: u64) -> PyRandom {
        let mut key: Vec<u32> = Vec::new();
        let mut v = seed;
        if v == 0 {
            key.push(0);
        }
        while v > 0 {
            key.push((v & 0xffff_ffff) as u32);
            v >>= 32;
        }
        let mut r = PyRandom::init_genrand(19650218);
        let mut i = 1usize;
        let mut j = 0usize;
        let mut k = N.max(key.len());
        while k > 0 {
            let prev = r.mt[i - 1];
            r.mt[i] = (r.mt[i] ^ (prev ^ (prev >> 30)).wrapping_mul(1664525))
                .wrapping_add(key[j])
                .wrapping_add(j as u32);
            i += 1;
            j += 1;
            if i >= N {
                r.mt[0] = r.mt[N - 1];
                i = 1;
            }
            if j >= key.len() {
                j = 0;
            }
            k -= 1;
        }
        let mut k = N - 1;
        while k > 0 {
            let prev = r.mt[i - 1];
            r.mt[i] = (r.mt[i] ^ (prev ^ (prev >> 30)).wrapping_mul(1566083941))
                .wrapping_sub(i as u32);
            i += 1;
            if i >= N {
                r.mt[0] = r.mt[N - 1];
                i = 1;
            }
            k -= 1;
        }
        r.mt[0] = 0x8000_0000;
        r.mti = N;
        r
    }

    pub fn genrand_uint32(&mut self) -> u32 {
        if self.mti >= N {
            for kk in 0..N - M {
                let y = (self.mt[kk] & UPPER_MASK) | (self.mt[kk + 1] & LOWER_MASK);
                self.mt[kk] = self.mt[kk + M] ^ (y >> 1) ^ if y & 1 != 0 { MATRIX_A } else { 0 };
            }
            for kk in N - M..N - 1 {
                let y = (self.mt[kk] & UPPER_MASK) | (self.mt[kk + 1] & LOWER_MASK);
                self.mt[kk] =
                    self.mt[kk + M - N] ^ (y >> 1) ^ if y & 1 != 0 { MATRIX_A } else { 0 };
            }
            let y = (self.mt[N - 1] & UPPER_MASK) | (self.mt[0] & LOWER_MASK);
            self.mt[N - 1] = self.mt[M - 1] ^ (y >> 1) ^ if y & 1 != 0 { MATRIX_A } else { 0 };
            self.mti = 0;
        }
        let mut y = self.mt[self.mti];
        self.mti += 1;
        y ^= y >> 11;
        y ^= (y << 7) & 0x9d2c_5680;
        y ^= (y << 15) & 0xefc6_0000;
        y ^= y >> 18;
        y
    }

    /// `getrandbits(k)` for `1 <= k <= 32`.
    fn getrandbits(&mut self, k: u32) -> u32 {
        if k == 0 {
            return 0;
        }
        self.genrand_uint32() >> (32 - k)
    }

    /// `Random._randbelow_with_getrandbits(n)` for `n >= 1`.
    pub fn randbelow(&mut self, n: u32) -> u32 {
        let k = 32 - n.leading_zeros();
        loop {
            let r = self.getrandbits(k);
            if r < n {
                return r;
            }
        }
    }

    /// `random.choice(seq)`.
    pub fn choice<T: Copy>(&mut self, seq: &[T]) -> T {
        seq[self.randbelow(seq.len() as u32) as usize]
    }
}

/// The `limit`-capped sample stream of `scan_dims` / `rzero.sweep`:
/// `(tuple(rng.choice(alphabet) for _ in range(nslots)) for _ in range(limit))`.
pub fn sample_labels<T: Copy>(seed: u64, alphabet: &[T], nslots: usize, limit: usize) -> Vec<Vec<T>> {
    let mut rng = PyRandom::seed(seed);
    let mut out = Vec::with_capacity(limit);
    for _ in 0..limit {
        let mut row = Vec::with_capacity(nslots);
        for _ in 0..nslots {
            row.push(rng.choice(alphabet));
        }
        out.push(row);
    }
    out
}
