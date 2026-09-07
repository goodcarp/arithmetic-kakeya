//! `search.py`'s pruning helpers and the generator DFS, bit-for-bit.
//!
//! Every scan order that the reported witness depends on is preserved:
//! `cand` ascending by vertex then by pool position, mandatory slots ascending
//! by vertex, `itertools.product` odometer order over the per-slot choice
//! lists, and the strict `len(gens) < len(best)` update that makes the *first*
//! minimal-length witness in DFS order the one reported.

use kakeya_core::{force, ForceScratch};

use crate::graph::{gen_row, Graph, Label, ZERO};

pub const P: i64 = (1 << 31) - 1;

#[inline]
fn parallel(a: Label, b: Label) -> bool {
    a.0 * b.1 - a.1 * b.0 == 0
}

/// `search.indep_dirs(labels)` -- pairwise non-parallel directions, capped at 2.
pub fn indep_dirs(labels: &[Label], seen: &mut Vec<Label>) -> usize {
    seen.clear();
    for &s in labels {
        if s == ZERO {
            continue;
        }
        if seen.is_empty() {
            seen.push(s);
            continue;
        }
        if seen.iter().all(|&a| !parallel(a, s)) {
            seen.push(s);
            if seen.len() >= 2 {
                return 2;
            }
        }
    }
    seen.len()
}

/// One mandatory-generator slot from P4: `(vertex, existing directions, need)`.
#[derive(Clone, Debug)]
pub struct Mand {
    pub j: usize,
    pub existing: Vec<Label>,
    pub need: usize,
}

/// Reusable buffers for `local_requirement`.
#[derive(Default)]
pub struct LocalReqScratch {
    inc: Vec<Vec<Label>>,
    seen: Vec<Label>,
}

/// `search.local_requirement(G, idx, n, T0, pool)`.
pub fn local_requirement(
    g: &Graph,
    n: usize,
    t0_mask: u64,
    sc: &mut LocalReqScratch,
    out: &mut Vec<Mand>,
) -> i64 {
    if sc.inc.len() < n {
        sc.inc.resize_with(n, Vec::new);
    }
    for v in sc.inc.iter_mut().take(n) {
        v.clear();
    }
    for &(u, v, x) in &g.edges {
        sc.inc[u].push(x);
        sc.inc[v].push(x);
    }
    let mut total = 0i64;
    out.clear();
    for j in 0..n {
        if t0_mask & (1u64 << j) != 0 {
            continue;
        }
        let k = indep_dirs(&sc.inc[j], &mut sc.seen);
        if k < 2 {
            total += (2 - k) as i64;
            out.push(Mand {
                j,
                existing: sc.seen.clone(),
                need: 2 - k,
            });
        }
    }
    total
}

/// `search._dir_choices(existing, pool, k)`.
///
/// `k >= 2` returns nothing (P6): the whole (graph, T) pair is discarded.
pub fn dir_choices(existing: &[Label], pool: &[Label], k: usize) -> Vec<Vec<Label>> {
    match k {
        1 => pool
            .iter()
            .filter(|&&s| existing.iter().all(|&e| !parallel(s, e)))
            .map(|&s| vec![s])
            .collect(),
        0 => vec![Vec::new()],
        _ => Vec::new(),
    }
}

/// All the reusable state one worker needs to run `min_generators`.
#[derive(Default)]
pub struct GenScratch {
    pub scratch: ForceScratch,
    rows: Vec<Vec<i64>>,
    row_pool: Vec<Vec<i64>>,
    cand: Vec<(usize, Label)>,
    slot_choices: Vec<Vec<Vec<Label>>>,
    slot_j: Vec<usize>,
    odometer: Vec<usize>,
    gens: Vec<(usize, Label)>,
    best: Option<Vec<(usize, Label)>>,
    t0: Vec<i64>,
}

struct Ctx<'a> {
    n: usize,
    cand: &'a [(usize, Label)],
}

#[allow(clippy::too_many_arguments)]
fn extend(
    ctx: &Ctx,
    rows: &mut Vec<Vec<i64>>,
    row_pool: &mut Vec<Vec<i64>>,
    gens: &mut Vec<(usize, Label)>,
    used: u64,
    best: &mut Option<Vec<(usize, Label)>>,
    scratch: &mut ForceScratch,
    start: usize,
    t: &[i64],
    budget_left: i64,
) {
    let (ok, t2) = force(rows, ctx.n as i64, t, P, scratch).expect("force on a well-formed instance");
    if ok {
        if best.as_ref().map_or(true, |b| gens.len() < b.len()) {
            *best = Some(gens.clone());
        }
        return;
    }
    if budget_left == 0 {
        return;
    }
    if best.as_ref().is_some_and(|b| gens.len() + 1 >= b.len()) {
        return;
    }
    let mut t2_mask = 0u64;
    for &j in &t2 {
        if j >= 0 && (j as usize) < 64 {
            t2_mask |= 1u64 << j;
        }
    }
    for ci in start..ctx.cand.len() {
        let (j, sl) = ctx.cand[ci];
        if t2_mask & (1u64 << j) != 0 {
            continue;
        }
        if used & (1u64 << j) != 0 {
            continue; // P6: at most one generator per vertex
        }
        let mut row = row_pool.pop().unwrap_or_default();
        gen_row(ctx.n, j, sl, &mut row);
        rows.push(row);
        gens.push((j, sl));
        extend(
            ctx,
            rows,
            row_pool,
            gens,
            used | (1u64 << j),
            best,
            scratch,
            ci + 1,
            &t2,
            budget_left - 1,
        );
        gens.pop();
        row_pool.push(rows.pop().expect("pushed above"));
    }
}

/// `search.min_generators(base_rows, n, T0, pool, budget, mand)`.
///
/// Returns the fewest generators (first such list in DFS order) or `None`.
pub fn min_generators(
    base_rows: &[Vec<i64>],
    n: usize,
    t0_mask: u64,
    pool: &[Label],
    budget: i64,
    mand: &[Mand],
    sc: &mut GenScratch,
) -> Option<Vec<(usize, Label)>> {
    let mand_total: i64 = mand.iter().map(|m| m.need as i64).sum();
    if mand_total > budget {
        return None;
    }
    // Destructured so the borrow checker sees the buffers as independent.
    let GenScratch {
        scratch,
        rows,
        row_pool,
        cand,
        slot_choices,
        slot_j,
        odometer,
        gens,
        best,
        t0,
    } = sc;

    slot_choices.clear();
    slot_j.clear();
    for m in mand {
        let ch = dir_choices(&m.existing, pool, m.need);
        if ch.is_empty() {
            return None;
        }
        slot_j.push(m.j);
        slot_choices.push(ch);
    }

    cand.clear();
    for j in 0..n {
        if t0_mask & (1u64 << j) != 0 {
            continue;
        }
        for &s in pool {
            cand.push((j, s));
        }
    }

    t0.clear();
    for j in 0..n {
        if t0_mask & (1u64 << j) != 0 {
            t0.push(j as i64);
        }
    }

    *best = None;
    let nslots = slot_choices.len();
    odometer.clear();
    odometer.resize(nslots, 0);

    let ctx = Ctx { n, cand };

    // Materialise the base rows ONCE per call, into buffers recycled from
    // `row_pool`.  Every combo below returns `rows` to exactly `base_len`
    // (the DFS pushes and pops symmetrically), so re-cloning them per combo
    // is pure waste -- and the old per-combo `rows.pop()` + `r.clone()` pair
    // was the row_pool leak: it parked the previous copies in the free list
    // and allocated fresh ones, growing the pool by `base_rows.len()` per
    // combo for the life of the worker.
    while let Some(r) = rows.pop() {
        row_pool.push(r);
    }
    for r in base_rows {
        let mut v = row_pool.pop().unwrap_or_default();
        v.clear();
        v.extend_from_slice(r);
        rows.push(v);
    }
    let base_len = rows.len();

    loop {
        // --- materialise this combo ---------------------------------------
        gens.clear();
        debug_assert_eq!(rows.len(), base_len);
        let mut used = 0u64;
        for si in 0..nslots {
            let j = slot_j[si];
            for &sl in &slot_choices[si][odometer[si]] {
                gens.push((j, sl));
                used |= 1u64 << j;
                let mut row = row_pool.pop().unwrap_or_default();
                gen_row(n, j, sl, &mut row);
                rows.push(row);
            }
        }
        let skip = best.as_ref().is_some_and(|b| gens.len() >= b.len());
        if !skip {
            let budget_left = budget - gens.len() as i64;
            extend(
                &ctx, rows, row_pool, gens, used, best, scratch, 0, t0, budget_left,
            );
        }
        while rows.len() > base_len {
            row_pool.push(rows.pop().expect("len checked"));
        }

        // --- odometer step (itertools.product order, last slot fastest) ----
        if nslots == 0 {
            break;
        }
        let mut si = nslots;
        let mut done = false;
        loop {
            if si == 0 {
                done = true;
                break;
            }
            si -= 1;
            odometer[si] += 1;
            if odometer[si] < slot_choices[si].len() {
                break;
            }
            odometer[si] = 0;
        }
        if done {
            break;
        }
    }
    best.clone()
}
