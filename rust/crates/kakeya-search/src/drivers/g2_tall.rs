//! `g2_tall.py`: 2 x r boxes with `f_1(1) = (1,0)` pinned, every level-2 label
//! free over POOL3, and the strict-improvement-on-11/6 cap rule.

use std::time::Instant;

use crate::common::{alphabet_of, combinations, score, LabelSource, Worker};
use crate::engine::{self, ChunkOut, HitRec, Improvement, RunOpts, Witness};
use crate::fmt;
use crate::frac::Frac;
use crate::graph::{slots_of, Label, POOL3};
use crate::search::min_generators;

pub struct TallCfg {
    pub rows: usize,
    pub max_t: usize,
    pub tlimit: Option<f64>,
    pub threads: usize,
    pub verbose: bool,
}

pub struct TallResult {
    pub best: Option<Frac>,
    pub bestobj: Option<Witness>,
    pub hits: usize,
    pub complete: bool,
    pub elapsed: f64,
    /// Rust-only progress fields (the Python RESULT has none): label tuples
    /// consumed, with `scan`'s `count` semantics (the tuple that trips the
    /// deadline is counted), the enumeration total, and the number of
    /// (graph, T0) pairs handed to `min_generators` -- the unit of DFS work,
    /// counted exactly where `cycles8` counts `tested`.
    pub walked: u64,
    pub total: u64,
    pub pairs: u64,
}

/// `cap = int(Fraction(11,6)*q); if Fraction(cap,q) >= Fraction(11,6): cap -= 1`
pub fn cap_for(q: i64) -> i64 {
    let mut cap = (11 * q).div_euclid(6);
    if cap * 6 >= 11 * q {
        cap -= 1;
    }
    cap
}

/// `g2_tall.run`'s best-update line:
/// `f"  [2x{rows_}] score {sc} = {float(sc):.4f}  m={G.m} r={len(gens)} t={t} labels={labs} gens={gens}"`
pub fn progress_line(
    rows: usize,
    sc: Frac,
    m: i64,
    gens: &[(usize, Label)],
    t: usize,
    labs: &[Label],
) -> String {
    format!(
        "  [2x{}] score {} = {}  m={} r={} t={} labels={} gens={}",
        rows,
        sc,
        fmt::f4(sc.as_f64()),
        m,
        gens.len(),
        t,
        fmt::tuple_labels(labs),
        fmt::repr_gens(gens)
    )
}

pub fn run(cfg: &TallCfg) -> TallResult {
    let d = vec![2usize, cfg.rows];
    let n: usize = 2 * cfg.rows;
    let slots = slots_of(&d);
    let pool: Vec<Label> = POOL3.to_vec();
    let nfree = slots.len() - 1; // slot 0 is the pinned level-1 bundle
    let src = LabelSource::Exhaustive {
        alphabet: alphabet_of(&pool),
        nslots: nfree,
    };
    let total = src.total();
    let combos: Vec<Vec<(u64, Vec<usize>)>> =
        (0..=cfg.max_t).map(|t| combinations(n, t)).collect();

    let opts = RunOpts {
        total,
        tlimit: cfg.tlimit,
        threads: cfg.threads,
        print_improvements: cfg.verbose,
        print_hits: false,
    };
    let t0 = Instant::now();
    let out = engine::run(&opts, t0, |start, end, stop| {
        let mut w = Worker::new(n);
        let mut c = ChunkOut::default();
        let mut chunk_best: Option<Frac> = None;
        let mut free: Vec<Label> = Vec::new();
        for index in start..end {
            if stop.should_stop(index) {
                break;
            }
            src.decode(index, &mut free);
            let mut labels: Vec<Label> = Vec::with_capacity(slots.len());
            labels.push((1, 0));
            labels.extend_from_slice(&free);
            let rk = w.prepare(&slots, &labels);
            let m = w.graph.m;
            let mut pairs_here = 0u64;
            for (t, combos_t) in combos.iter().enumerate() {
                let q = n - t;
                let budget = cap_for(q as i64) - m;
                if budget < 0 || (q as i64 - rk) > budget {
                    continue;
                }
                for (mask, members) in combos_t {
                    let mand_total = w.local_req(n, *mask);
                    if mand_total > budget {
                        continue;
                    }
                    pairs_here += 1;
                    let mand = std::mem::take(&mut w.mand);
                    let gens =
                        min_generators(&w.rows, n, *mask, &pool, budget, &mand, &mut w.gen);
                    w.mand = mand;
                    let gens = match gens {
                        None => continue,
                        Some(g) => g,
                    };
                    let sc = score(m, gens.len(), q);
                    if chunk_best.is_none() || sc < chunk_best.expect("checked") {
                        chunk_best = Some(sc);
                        let line = progress_line(cfg.rows, sc, m, &gens, t, &free);
                        c.improvements.push(Improvement {
                            index,
                            sc,
                            line: Some(line),
                            witness: Some(Witness {
                                labels: free.clone(),
                                m,
                                gens: gens.clone(),
                                t0: members.clone(),
                                t,
                            }),
                        });
                    }
                    // g2_tall appends every witness found; the cap already
                    // guarantees the score is strictly below 11/6.
                    c.hits.push(HitRec {
                        index,
                        progress: None,
                        obj: None,
                    });
                }
            }
            if pairs_here > 0 {
                c.tested.push((index, pairs_here));
            }
        }
        c
    });

    if out.stopped && cfg.verbose {
        println!("  [2x{}] TIME LIMIT", cfg.rows);
    }
    TallResult {
        best: out.merged.best,
        bestobj: out.merged.bestobj,
        hits: out.merged.hits.len(),
        complete: !out.stopped,
        elapsed: out.elapsed,
        walked: out.scanned,
        total,
        pairs: out.merged.tested,
    }
}

/// The Python RESULT line plus three Rust-only keys appended after `seconds`:
/// `walked`/`total` (label tuples, `scan`-style) and `pairs` ((graph, T0)
/// pairs run through the DFS), so a TIME LIMIT run reports how far it got.
/// Everything up to and including `seconds` is byte-identical to
/// `g2_tall.py`; strip the tail to diff against a Python log.
pub fn emit(cfg: &TallCfg, r: &TallResult) {
    let best = r.best.filter(|b| b.is_truthy()).map(|b| b.to_string());
    println!(
        "RESULT {{\"tag\": \"g2_tall_2x{}\", \"d\": [2, {}], \"pool\": 3, \
         \"max_t\": 1, \"target\": \"<11/6\", \"best\": {}, \"hits\": {}, \
         \"complete\": {}, \"seconds\": {}, \"walked\": {}, \"total\": {}, \
         \"pairs\": {}}}",
        cfg.rows,
        cfg.rows,
        fmt::json_opt_str(best),
        r.hits,
        fmt::json_bool(r.complete),
        fmt::seconds(r.elapsed),
        r.walked,
        r.total,
        r.pairs
    );
}
