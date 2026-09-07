//! `stacked.py`: two copies of the certified 7/4 trapezoid stacked along a
//! third coordinate, every interface label pattern.

use std::time::Instant;

use crate::common::{alphabet_of, combinations, score, LabelSource, Worker};
use crate::engine::{self, ChunkOut, HitRec, Improvement, RunOpts, Witness};
use crate::fmt;
use crate::frac::{frac_repr, Frac};
use crate::graph::{slots_of, Label};
use crate::search::min_generators;

pub struct StackedCfg {
    pub name: String,
    pub pool: Vec<Label>,
    pub max_t: usize,
    pub target: Frac,
    pub tlimit: Option<f64>,
    pub threads: usize,
}

pub struct StackedResult {
    pub best: Option<Frac>,
    pub bestobj: Option<Witness>,
    pub hits: Vec<HitRec>,
    pub elapsed: f64,
}

/// One of `stacked.py`'s `for x in h[:5]: print("      ", x)` lines, i.e. six
/// spaces, the separator space, then `repr((sc, labs, m, gens, sorted(T0)))`.
pub fn hit_line(
    sc: Frac,
    labs: &[Label],
    m: i64,
    gens: &[(usize, Label)],
    t0: &[usize],
) -> String {
    format!(
        "       ({}, {}, {}, {}, {})",
        frac_repr(&sc),
        fmt::tuple_labels(labs),
        m,
        fmt::repr_gens(gens),
        fmt::list_usize(t0)
    )
}

pub fn run(cfg: &StackedCfg) -> StackedResult {
    let d = vec![2usize, 2, 2];
    let n = 8usize;
    let slots = slots_of(&d);
    // f_1 and f_2 are pinned to the 7/4 trapezoid; the four level-3 keys are free.
    let pinned: [Label; 3] = [(1, 0), (0, 1), (1, 2)];
    let src = LabelSource::Exhaustive {
        alphabet: alphabet_of(&cfg.pool),
        nslots: 4,
    };
    let total = src.total();
    let combos: Vec<Vec<(u64, Vec<usize>)>> =
        (0..=cfg.max_t).map(|t| combinations(n, t)).collect();

    let opts = RunOpts {
        total,
        tlimit: cfg.tlimit,
        threads: cfg.threads,
        print_improvements: false, // stacked prints nothing inside the loop
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
            labels.extend_from_slice(&pinned);
            labels.extend_from_slice(&free);
            let rk = w.prepare(&slots, &labels);
            let m = w.graph.m;
            for (t, combos_t) in combos.iter().enumerate() {
                let den = n - t;
                let budget = cfg.target.mul_int_floor(den as i64) - m;
                if budget < 0 || (den as i64 - rk) > budget {
                    continue;
                }
                for (mask, members) in combos_t {
                    let mand_total = w.local_req(n, *mask);
                    if mand_total > budget {
                        continue;
                    }
                    let mand = std::mem::take(&mut w.mand);
                    let gens = min_generators(
                        &w.rows, n, *mask, &cfg.pool, budget, &mand, &mut w.gen,
                    );
                    w.mand = mand;
                    let gens = match gens {
                        None => continue,
                        Some(g) => g,
                    };
                    let sc = score(m, gens.len(), den);
                    if chunk_best.is_none() || sc < chunk_best.expect("checked") {
                        chunk_best = Some(sc);
                        c.improvements.push(Improvement {
                            index,
                            sc,
                            line: None,
                            witness: Some(Witness {
                                labels: free.clone(),
                                m,
                                gens: gens.clone(),
                                t0: members.clone(),
                                t,
                            }),
                        });
                    }
                    if sc < Frac::new(7, 4) {
                        let obj = hit_line(sc, &free, m, &gens, members);
                        c.hits.push(HitRec {
                            index,
                            progress: None,
                            obj: Some(obj),
                        });
                    }
                }
            }
        }
        c
    });

    StackedResult {
        best: out.merged.best,
        bestobj: out.merged.bestobj,
        hits: out.merged.hits,
        elapsed: out.elapsed,
    }
}

pub fn emit(cfg: &StackedCfg, r: &StackedResult) -> bool {
    match (&r.best, &r.bestobj) {
        (Some(b), Some(bo)) => {
            println!(
                "{}: best score over all interfaces = {} ({})",
                cfg.name,
                b,
                py_float(b.as_f64())
            );
            println!(
                "   witness: interface labels={} m={} r={} t={} T0={}",
                fmt::tuple_labels(&bo.labels),
                bo.m,
                bo.gens.len(),
                bo.t,
                fmt::list_usize(&bo.t0)
            );
            println!(
                "   strictly-better-than-7/4 hits: {}   [{:.1}s]",
                r.hits.len(),
                r.elapsed
            );
            for h in r.hits.iter().take(5) {
                if let Some(o) = &h.obj {
                    println!("{o}");
                }
            }
            true
        }
        _ => {
            println!(
                "{}: best score over all interfaces = None (None)",
                cfg.name
            );
            eprintln!("stacked: no witness found (the Python driver raises TypeError here)");
            false
        }
    }
}

/// `repr(float(x))` for the values this driver prints (7/4 -> "1.75").
fn py_float(x: f64) -> String {
    let mut s = format!("{x}");
    if !s.contains('.') && !s.contains('e') && !s.contains("inf") && !s.contains("NaN") {
        s.push_str(".0");
    }
    s
}
