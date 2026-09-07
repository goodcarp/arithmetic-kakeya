//! `rzero.py`: generator-free forcing probe -- one `force` call per label.

use std::time::Instant;

use kakeya_core::force;

use crate::common::{alphabet_of, LabelSource, Worker};
use crate::engine::{self, ChunkOut, Improvement, RunOpts};
use crate::fmt;
use crate::frac::Frac;
use crate::graph::{build_rows, m_of_labels, slots_of, Label};
use crate::pyrandom::sample_labels;
use crate::search::P;

pub struct RzeroCfg {
    pub d: Vec<usize>,
    pub pool: Vec<Label>,
    pub limit: Option<usize>,
    pub seed: u64,
    pub tlimit: Option<f64>,
    pub threads: usize,
    pub verbose: bool,
}

pub struct RzeroResult {
    pub scanned: u64,
    pub total: u64,
    pub forcing: u64,
    pub best: Option<Frac>,
    pub complete: bool,
    pub elapsed: f64,
}

/// `rzero.sweep`'s hit line:
/// `f"  generator-free forcing object! m={m} n={n} score={sc} labels={labels}"`
pub fn progress_line(m: i64, n: usize, sc: Frac, labels: &[Label]) -> String {
    format!(
        "  generator-free forcing object! m={} n={} score={} labels={}",
        m,
        n,
        sc,
        fmt::tuple_labels(labels)
    )
}

pub fn run(cfg: &RzeroCfg) -> RzeroResult {
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
        for index in start..end {
            if stop.should_stop(index) {
                break;
            }
            src.decode(index, &mut w.labels);
            let labels = std::mem::take(&mut w.labels);
            let m = m_of_labels(&slots, &labels);
            w.graph.fill(&slots, &labels);
            build_rows(&w.graph, &mut w.rows);
            let (ok, _) = force(&w.rows, n as i64, &[], P, &mut w.gen.scratch)
                .expect("force on a well-formed instance");
            if ok {
                c.tested.push((index, 1));
                let sc = Frac::new(m, n as i64);
                if chunk_best.is_none() || sc < chunk_best.expect("checked") {
                    chunk_best = Some(sc);
                    c.improvements.push(Improvement {
                        index,
                        sc,
                        line: Some(progress_line(m, n, sc, &labels)),
                        witness: None,
                    });
                }
            }
            w.labels = labels;
        }
        c
    });

    RzeroResult {
        scanned: out.scanned,
        total,
        forcing: out.merged.tested,
        best: out.merged.best,
        complete: cfg.limit.is_none() && out.scanned >= total,
        elapsed: out.elapsed,
    }
}

pub fn emit(cfg: &RzeroCfg, r: &RzeroResult) {
    let best = r.best.filter(|b| b.is_truthy()).map(|b| b.to_string());
    println!(
        "RESULT {{\"tag\": \"rzero\", \"d\": {}, \"pool\": {}, \"scanned\": {}, \
         \"total\": {}, \"forcing_objects\": {}, \"best_score\": {}, \
         \"complete\": {}, \"seconds\": {}}}",
        fmt::list_usize(&cfg.d),
        cfg.pool.len(),
        r.scanned,
        r.total,
        r.forcing,
        fmt::json_opt_str(best),
        fmt::json_bool(r.complete),
        fmt::seconds(r.elapsed)
    );
}
