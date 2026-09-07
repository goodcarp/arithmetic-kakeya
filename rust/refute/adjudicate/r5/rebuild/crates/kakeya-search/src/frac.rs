//! Exact rationals with the same semantics as Python's `fractions.Fraction`
//! at every site the drivers use (contract sec 7).
//!
//! Denominators here are always positive and small (`n - t <= 16`), numerators
//! are `m + r <= a few hundred`, so `i64` is far more than enough; comparisons
//! widen to `i128` anyway so no cross-multiplication can overflow.

use std::cmp::Ordering;
use std::fmt;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Frac {
    pub num: i64,
    pub den: i64,
}

fn gcd(mut a: i64, mut b: i64) -> i64 {
    while b != 0 {
        let t = a % b;
        a = b;
        b = t;
    }
    a.abs()
}

impl Frac {
    /// `Fraction(num, den)` -- normalised, denominator forced positive.
    pub fn new(num: i64, den: i64) -> Frac {
        assert!(den != 0, "zero denominator");
        let (mut n, mut d) = (num, den);
        if d < 0 {
            n = -n;
            d = -d;
        }
        let g = gcd(n, d);
        if g > 1 {
            n /= g;
            d /= g;
        }
        Frac { num: n, den: d }
    }

    /// Parse `"7/4"` or `"2"` the way `Fraction(str)` does for the forms the
    /// drivers actually pass.
    pub fn parse(s: &str) -> Result<Frac, String> {
        let s = s.trim();
        match s.split_once('/') {
            None => s
                .parse::<i64>()
                .map(|n| Frac::new(n, 1))
                .map_err(|e| format!("bad fraction {s:?}: {e}")),
            Some((a, b)) => {
                let n: i64 = a
                    .trim()
                    .parse()
                    .map_err(|e| format!("bad fraction {s:?}: {e}"))?;
                let d: i64 = b
                    .trim()
                    .parse()
                    .map_err(|e| format!("bad fraction {s:?}: {e}"))?;
                if d == 0 {
                    return Err(format!("bad fraction {s:?}: zero denominator"));
                }
                Ok(Frac::new(n, d))
            }
        }
    }

    /// `int(self * k)` for `k > 0` -- Python's `int()` truncates toward zero,
    /// and every value at every call site is non-negative, so this is `floor`.
    pub fn mul_int_floor(&self, k: i64) -> i64 {
        debug_assert!(k >= 0 && self.num >= 0);
        (self.num * k).div_euclid(self.den)
    }

    pub fn as_f64(&self) -> f64 {
        self.num as f64 / self.den as f64
    }

    /// Python's truthiness of a Fraction: `bool(Fraction(0, d))` is False.
    /// `scan1.py` writes `str(b) if b else None`, so a zero best prints null.
    pub fn is_truthy(&self) -> bool {
        self.num != 0
    }
}

impl PartialOrd for Frac {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for Frac {
    fn cmp(&self, other: &Self) -> Ordering {
        let l = self.num as i128 * other.den as i128;
        let r = other.num as i128 * self.den as i128;
        l.cmp(&r)
    }
}

impl fmt::Display for Frac {
    /// `Fraction.__str__`: bare integer when the denominator is 1.
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.den == 1 {
            write!(f, "{}", self.num)
        } else {
            write!(f, "{}/{}", self.num, self.den)
        }
    }
}

/// `repr(Fraction(n, d))`, used by `stacked.py`'s hit lines.
pub fn frac_repr(x: &Frac) -> String {
    format!("Fraction({}, {})", x.num, x.den)
}
