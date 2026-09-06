//! Shared per-worker state and the enumeration helpers every driver reuses.

use kakeya_core::rank;

use crate::frac::Frac;
use crate::graph::{build_rows, Graph, Label, Slot, ZERO};
use crate::search::{local_requirement, GenScratch, LocalReqScratch, Mand, P};

/// Everything one rayon chunk needs; created once per chunk, reused per item.
#[derive(Default)]
pub struct Worker {
    pub graph: Graph,
    pub rows: Vec<Vec<i64>>,
    pub lr: LocalReqScratch,
    pub mand: Vec<Mand>,
    pub gen: GenScratch,
    pub labels: Vec<Label>,
}

impl Worker {
    pub fn new(n: usize) -> Worker {
        let mut w = Worker::default();
        w.graph.n = n;
        w
    }

    /// Build the graph and its edge rows, and return `rank(base_rows)`.
    pub fn prepare(&mut self, slots: &[Slot], labels: &[Label]) -> i64 {
        self.graph.fill(slots, labels);
        build_rows(&self.graph, &mut self.rows);
        rank(&self.rows, P).expect("rank on a well-formed instance")
    }

    pub fn local_req(&mut self, n: usize, t0_mask: u64) -> i64 {
        local_requirement(&self.graph, n, t0_mask, &mut self.lr, &mut self.mand)
    }
}

/// `itertools.combinations(range(n), t)` as (mask, sorted members), in order.
pub fn combinations(n: usize, t: usize) -> Vec<(u64, Vec<usize>)> {
    let mut out = Vec::new();
    if t == 0 {
        out.push((0u64, Vec::new()));
        return out;
    }
    if t > n {
        return out;
    }
    let mut c: Vec<usize> = (0..t).collect();
    loop {
        let mut mask = 0u64;
        for &j in &c {
            mask |= 1u64 << j;
        }
        out.push((mask, c.clone()));
        let mut i = t;
        loop {
            if i == 0 {
                return out;
            }
            i -= 1;
            if c[i] != i + n - t {
                break;
            }
        }
        c[i] += 1;
        for j in i + 1..t {
            c[j] = c[j - 1] + 1;
        }
    }
}

/// Where an outer item's label vector comes from.
pub enum LabelSource {
    /// `itertools.product(alphabet, repeat=nslots)`, last slot fastest.
    Exhaustive {
        alphabet: Vec<Label>,
        nslots: usize,
    },
    /// The `limit`-capped `random.Random(seed).choice` stream.
    Sampled(Vec<Vec<Label>>),
}

impl LabelSource {
    pub fn total(&self) -> u64 {
        match self {
            LabelSource::Exhaustive { alphabet, nslots } => {
                // Audit C6 (2026-09-06): an unchecked pow wrapped silently on large
                // boxes and let a RESULT line claim `complete: true` for an index
                // space that was never scanned. Refuse loudly instead.
                (alphabet.len() as u64)
                    .checked_pow(*nslots as u32)
                    .unwrap_or_else(|| panic!(
                        "label index space {}^{} exceeds u64; refusing to run (audit C6)",
                        alphabet.len(), nslots))
            }
            LabelSource::Sampled(v) => v.len() as u64,
        }
    }

    pub fn nslots(&self) -> usize {
        match self {
            LabelSource::Exhaustive { nslots, .. } => *nslots,
            LabelSource::Sampled(v) => v.first().map_or(0, |r| r.len()),
        }
    }

    /// Write the label vector for enumeration index `index` into `out`.
    pub fn decode(&self, index: u64, out: &mut Vec<Label>) {
        match self {
            LabelSource::Exhaustive { alphabet, nslots } => {
                out.clear();
                out.resize(*nslots, ZERO);
                let a = alphabet.len() as u64;
                let mut x = index;
                for s in (0..*nslots).rev() {
                    out[s] = alphabet[(x % a) as usize];
                    x /= a;
                }
            }
            LabelSource::Sampled(v) => {
                out.clear();
                out.extend_from_slice(&v[index as usize]);
            }
        }
    }
}

/// `[ZERO] + list(pool)`.
pub fn alphabet_of(pool: &[Label]) -> Vec<Label> {
    let mut a = vec![ZERO];
    a.extend_from_slice(pool);
    a
}

/// `Fraction(num, den)` for a score.
pub fn score(m: i64, r: usize, den: usize) -> Frac {
    Frac::new(m + r as i64, den as i64)
}
