//! `search.scan_dims` + the `scan1.py` stdout format.

use std::time::Instant;

use crate::common::{alphabet_of, combinations, score, LabelSource, Worker};
use crate::engine::{self, ChunkOut, HitRec, Improvement, RunOpts};
use crate::fmt;
use crate::frac::Frac;
use crate::graph::{slots_of, Label};
use crate::pyrandom::sample_labels;
use crate::search::min_generators;

pub struct ScanCfg {
    pub tag: String,
    pub d: Vec<usize>,
    pub pool: Vec<Label>,
    pub max_t: usize,
    pub target: Frac,
    pub limit: Option<usize>,
    pub seed: u64,
    pub tlimit: Option<f64>,
    pub threads: usize,
    pub verbose: bool,
}

pub struct ScanResult {
    pub scanned: u64,
    pub total: u64,
    pub best: Option<Frac>,
    pub hits: Vec<HitRec>,
    pub complete: bool,
    pub elapsed: f64,
}

/// `scan_dims`' verbose line:
/// `f"   HIT {sc} (={float(sc):.4f})  d={d} m={m} r={len(gens)} t={t}"`
pub fn hit_line(sc: Frac, d_repr: &str, m: i64, r: usize, t: usize) -> String {
    format!(
        "   HIT {} (={})  d={} m={} r={} t={}",
        sc,
        fmt::f4(sc.as_f64()),
        d_repr,
        m,
        r,
        t
    )
}

pub fn run(cfg: &ScanCfg) -> ScanResult {
    let slots = slots_of(&cfg.d);
    let nslots = slots.len();
    let n: usize = cfg.d.iter().product();
    let alphabet = alphabet_of(&cfg.pool);
    let src = match cfg.limit {
        None => LabelSource::Exhaustive {
            alphabet: alphabet.clone(),
            nslots,
        },
        Some(l) => LabelSource::Sampled(sample_labels(cfg.seed, &alphabet, nslots, l)),
    };
    let total = src.total();
    let combos: Vec<Vec<(u64, Vec<usize>)>> =
        (0..=cfg.max_t).map(|t| combinations(n, t)).collect();
    let m_cap = cfg.target.mul_int_floor(n as i64);
    let d_repr = fmt::list_usize(&cfg.d);

    let opts = RunOpts {
        total,
        tlimit: cfg.tlimit,
        threads: cfg.threads,
        print_improvements: false, // scan_dims never prints on a best update
        print_hits: cfg.verbose,
    };
    let t0 = Instant::now();
    let out = engine::run(&opts, t0, |start, end, stop| {
        let mut w = Worker::new(n);
        let mut c = ChunkOut::default();
        let mut chunk_best: Option<Frac> = None;
        for index in start..end {
            if stop.should_stop(index) {
                break;
            }
            src.decode(index, &mut w.labels);
            let labels = std::mem::take(&mut w.labels);
            let m = crate::graph::m_of_labels(&slots, &labels);
            if m > m_cap {
                w.labels = labels;
                continue;
            }
            let rk = w.prepare(&slots, &labels);
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
                            witness: None,
                        });
                    }
                    if sc <= cfg.target {
                        let progress = hit_line(sc, &d_repr, m, gens.len(), t);
                        let obj = format!(
                            "{{\"d\": {}, \"labels\": {}, \"m\": {}, \"gens\": {}, \
                             \"T0\": {}, \"score\": \"{}\", \"n\": {}}}",
                            d_repr,
                            fmt::json_labels(&labels),
                            m,
                            fmt::json_gens(&gens),
                            fmt::json_usize(members),
                            sc,
                            n
                        );
                        c.hits.push(HitRec {
                            index,
                            progress: Some(progress),
                            obj: Some(obj),
                        });
                    }
                }
            }
            w.labels = labels;
        }
        c
    });

    ScanResult {
        scanned: out.scanned,
        total,
        best: out.merged.best,
        hits: out.merged.hits,
        complete: cfg.limit.is_none() && out.scanned >= total,
        elapsed: out.elapsed,
    }
}

pub fn emit(cfg: &ScanCfg, r: &ScanResult) {
    let best = r
        .best
        .filter(|b| b.is_truthy())
        .map(|b| b.to_string());
    println!(
        "RESULT {{\"tag\": \"{}\", \"d\": {}, \"pool\": {}, \"max_t\": {}, \
         \"target\": \"{}\", \"scanned\": {}, \"total\": {}, \"best\": {}, \
         \"hits\": {}, \"complete\": {}, \"seconds\": {}}}",
        cfg.tag,
        fmt::list_usize(&cfg.d),
        cfg.pool.len(),
        cfg.max_t,
        cfg.target,
        r.scanned,
        r.total,
        fmt::json_opt_str(best),
        r.hits.len(),
        fmt::json_bool(r.complete),
        fmt::seconds(r.elapsed)
    );
    for h in &r.hits {
        if let Some(o) = &h.obj {
            println!("HITOBJ {o}");
        }
    }
}
