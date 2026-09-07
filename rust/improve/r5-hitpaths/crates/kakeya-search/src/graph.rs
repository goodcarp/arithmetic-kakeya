//! The `kakeya.py` surface the drivers need: `ZERO`, `ConstructibleGraph`
//! (vertices / n / m / edges), `build_rows`, plus `search.py`'s `domains`,
//! `mult`, `graph_from_labels`, `m_of_labels` and `gen_row`.
//!
//! Vertex indexing is the mixed-radix order of `itertools.product(*[range(1,
//! di+1) ...])`: last coordinate fastest.  A level-`i` bundle with key `key`
//! and a non-ZERO label emits `mult = prod(d[i..])` parallel edges joining
//! `idx(key)*mult + tail` to `(idx(key)+1)*mult + tail`, `tail` ascending --
//! which is exactly `edges()` in `edges()` order.

pub type Label = (i64, i64);
pub const ZERO: Label = (0, 0);

pub const POOL3: [Label; 3] = [(1, 0), (0, 1), (1, 1)];
pub const POOL4: [Label; 4] = [(1, 0), (0, 1), (1, 1), (1, 2)];
pub const POOL5: [Label; 5] = [(1, 0), (0, 1), (1, 1), (1, 2), (1, 3)];
pub const POOL6: [Label; 6] = [(1, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 1)];
pub const POOL8: [Label; 8] = [
    (1, 0),
    (0, 1),
    (1, 1),
    (1, 2),
    (1, 3),
    (2, 1),
    (1, -2),
    (3, 1),
];

pub fn pool_by_size(k: usize) -> Option<&'static [Label]> {
    match k {
        3 => Some(&POOL3),
        4 => Some(&POOL4),
        5 => Some(&POOL5),
        6 => Some(&POOL6),
        8 => Some(&POOL8),
        _ => None,
    }
}

/// `search.mult(d, i)` for the 1-based level `i`: `prod(d[i:])`.
pub fn mult(d: &[usize], i: usize) -> usize {
    d[i..].iter().product()
}

/// `search.domains(d)`: per level, the key tuples in Python's order
/// (prefix-major, last coordinate minor).
pub fn domains(d: &[usize]) -> Vec<Vec<Vec<usize>>> {
    let mut out = Vec::with_capacity(d.len());
    for i in 1..=d.len() {
        // itertools.product(*[range(1, d[j]+1) for j in range(i-1)])
        let mut prefixes: Vec<Vec<usize>> = vec![Vec::new()];
        for dj in d.iter().take(i - 1) {
            let mut next = Vec::with_capacity(prefixes.len() * dj);
            for p in &prefixes {
                for v in 1..=*dj {
                    let mut q = p.clone();
                    q.push(v);
                    next.push(q);
                }
            }
            prefixes = next;
        }
        let mut level = Vec::new();
        for p in &prefixes {
            for last in 1..d[i - 1] {
                let mut key = p.clone();
                key.push(last);
                level.push(key);
            }
        }
        out.push(level);
    }
    out
}

/// One enumeration slot: a level-`i` key, with everything the hot loop needs
/// precomputed.
#[derive(Clone, Debug)]
pub struct Slot {
    /// 1-based level.
    pub level: usize,
    pub key: Vec<usize>,
    /// `prod(d[level..])` -- both the edge multiplicity and the `m` weight.
    pub mult: usize,
    /// mixed-radix index of `key` inside `d[..level]`.
    pub idx_key: usize,
}

/// Flatten `domains(d)` into the slot vector, in the order `search.py` assigns
/// labels to it.
pub fn slots_of(d: &[usize]) -> Vec<Slot> {
    let doms = domains(d);
    let mut out = Vec::new();
    for (li, level) in doms.iter().enumerate() {
        let i = li + 1;
        let mu = mult(d, i);
        for key in level {
            let mut idx = 0usize;
            for (j, kv) in key.iter().enumerate() {
                idx = idx * d[j] + (kv - 1);
            }
            out.push(Slot {
                level: i,
                key: key.clone(),
                mult: mu,
                idx_key: idx,
            });
        }
    }
    out
}

/// `m_of_labels(d, doms, labels)`.
pub fn m_of_labels(slots: &[Slot], labels: &[Label]) -> i64 {
    let mut tot = 0i64;
    for (s, l) in slots.iter().zip(labels) {
        if *l != ZERO {
            tot += s.mult as i64;
        }
    }
    tot
}

/// A `ConstructibleGraph` reduced to what the drivers read off it.
#[derive(Clone, Debug, Default)]
pub struct Graph {
    pub n: usize,
    pub m: i64,
    /// `(u_index, v_index, label)` in `ConstructibleGraph.edges()` order.
    pub edges: Vec<(usize, usize, Label)>,
}

impl Graph {
    /// `ConstructibleGraph(X, d, graph_from_labels(d, doms, labels))`, built
    /// straight off the flat label vector.  ZERO slots contribute no key and
    /// no edges, exactly as `graph_from_labels` drops them.
    pub fn from_labels(d: &[usize], slots: &[Slot], labels: &[Label]) -> Graph {
        let n: usize = d.iter().product();
        let mut g = Graph {
            n,
            m: 0,
            edges: Vec::new(),
        };
        g.fill(slots, labels);
        g
    }

    /// Rebuild in place, reusing the edge buffer.
    pub fn fill(&mut self, slots: &[Slot], labels: &[Label]) {
        self.m = 0;
        self.edges.clear();
        for (s, lab) in slots.iter().zip(labels) {
            if *lab == ZERO {
                continue;
            }
            self.m += s.mult as i64;
            let base1 = s.idx_key * s.mult;
            let base2 = (s.idx_key + 1) * s.mult;
            for tail in 0..s.mult {
                self.edges.push((base1 + tail, base2 + tail, *lab));
            }
        }
    }

    /// `G.vertices()` -- the 1-based coordinate tuples, index order.
    pub fn vertices(d: &[usize]) -> Vec<Vec<usize>> {
        let mut out: Vec<Vec<usize>> = vec![Vec::new()];
        for di in d {
            let mut next = Vec::with_capacity(out.len() * di);
            for p in &out {
                for v in 1..=*di {
                    let mut q = p.clone();
                    q.push(v);
                    next.push(q);
                }
            }
            out = next;
        }
        out
    }

    /// `G.index(v)` for a 1-based coordinate tuple.
    pub fn index(d: &[usize], v: &[usize]) -> usize {
        let mut idx = 0usize;
        for (j, vj) in v.iter().enumerate() {
            idx = idx * d[j] + (vj - 1);
        }
        idx
    }
}

/// `build_rows(G, [])` -- one `2n`-wide integer row per edge, edges in order.
pub fn build_rows(g: &Graph, out: &mut Vec<Vec<i64>>) {
    let w = 2 * g.n;
    // Reuse whatever rows we already own; only grow if this graph has more.
    if out.len() < g.edges.len() {
        out.resize_with(g.edges.len(), || vec![0i64; w]);
    } else {
        out.truncate(g.edges.len());
    }
    for (row, &(u, v, x)) in out.iter_mut().zip(g.edges.iter()) {
        if row.len() != w {
            row.clear();
            row.resize(w, 0);
        } else {
            row.iter_mut().for_each(|c| *c = 0);
        }
        row[2 * u] += x.0;
        row[2 * u + 1] += x.1;
        row[2 * v] -= x.0;
        row[2 * v + 1] -= x.1;
    }
}

/// `search.gen_row(n, j, s)`.
pub fn gen_row(n: usize, j: usize, s: Label, row: &mut Vec<i64>) {
    row.clear();
    row.resize(2 * n, 0);
    row[2 * j] = s.0;
    row[2 * j + 1] = s.1;
}
