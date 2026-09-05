//! `cycles8.py`: every `deg`-regular constructible object on the 2x2x2 box.

use std::time::Instant;

use crate::common::{combinations, score, Worker};
use crate::engine::{self, ChunkOut, HitRec, Improvement, RunOpts};
use crate::fmt;
use crate::frac::Frac;
use crate::graph::{build_rows, slots_of, Graph, Label, Slot, ZERO};
use crate::search::min_generators;

pub struct CyclesCfg {
    pub pool: Vec<Label>,
    pub target: Frac,
    pub deg: usize,
    pub tlimit: Option<f64>,
    pub threads: usize,
    pub verbose: bool,
}

pub struct CyclesResult {
    pub good: usize,
    pub best: Option<Frac>,
    pub hits: Vec<HitRec>,
    pub tested: u64,
    pub stopped: bool,
    pub elapsed: f64,
}

/// `cycles8.build(pattern, labels, X)` -- present slots take the next label,
/// absent slots contribute nothing.
fn apply_pattern(pattern: &[u8], labels: &[Label], slots: &[Slot], out: &mut Vec<Label>) {
    out.clear();
    let mut li = 0usize;
    for &on in pattern {
        if on == 0 {
            out.push(ZERO);
        } else {
            out.push(labels[li]);
            li += 1;
        }
    }
    debug_assert_eq!(out.len(), slots.len());
}

/// Step 1 of `main`: the presence patterns that are `deg`-regular with m = n.
fn good_patterns(slots: &[Slot], d: &[usize], n: usize, deg: usize, probe: Label) -> Vec<Vec<u8>> {
    let nslots = slots.len();
    let mut good = Vec::new();
    let mut labels = vec![ZERO; nslots];
    for bits in 0..(1u32 << nslots) {
        let pattern: Vec<u8> = (0..nslots)
            .map(|i| ((bits >> (nslots - 1 - i)) & 1) as u8)
            .collect();
        for (i, l) in labels.iter_mut().enumerate() {
            *l = if pattern[i] == 1 { probe } else { ZERO };
        }
        let g = Graph::from_labels(d, slots, &labels);
        if g.m != n as i64 {
            continue;
        }
        let mut degs = vec![0usize; n];
        for &(u, v, _) in &g.edges {
            degs[u] += 1;
            degs[v] += 1;
        }
        if degs.iter().all(|&x| x == deg) {
            good.push(pattern);
        }
    }
    good
}

/// `cycles8.main`'s best-update line:
/// `f"  new best {sc} = {float(sc):.4f}  pattern={pattern} labels={labels} r={len(gens)} t={t}"`
pub fn progress_line(sc: Frac, pattern: &[u8], labels: &[Label], r: usize, t: usize) -> String {
    format!(
        "  new best {} = {}  pattern={} labels={} r={} t={}",
        sc,
        fmt::f4(sc.as_f64()),
        fmt::tuple_u8(pattern),
        fmt::tuple_labels(labels),
        r,
        t
    )
}

/// The `deg`-regular presence patterns on the 2x2x2 box, `itertools.product
/// ([0,1], repeat=7)` order -- step 1 of `cycles8.main`, which is instant and
/// independent of the pool, so `check` can gate it directly.  `probe` stands in
/// for `pool[0]`; only "is it ZERO" matters to the degree count.
pub fn regular_patterns(deg: usize, probe: Label) -> Vec<Vec<u8>> {
    let d = vec![2usize, 2, 2];
    let slots = slots_of(&d);
    good_patterns(&slots, &d, 8, deg, probe)
}

/// Total label tuples across the patterns: `sum |pool| ** npres(p)`.
pub fn pattern_total(good: &[Vec<u8>], pool_len: usize) -> u64 {
    good.iter()
        .map(|p| (pool_len as u64).pow(p.iter().map(|&x| x as u32).sum::<u32>()))
        .sum()
}

pub fn run(cfg: &CyclesCfg) -> CyclesResult {
    let d = vec![2usize, 2, 2];
    let n = 8usize;
    let slots = slots_of(&d);
    let good = good_patterns(&slots, &d, n, cfg.deg, cfg.pool[0]);
    if cfg.verbose {
        println!(
            "{} presence patterns are {}-regular with m = {}",
            good.len(),
            cfg.deg,
            n
        );
    }
    // Flatten (pattern, labels) into one index space, `good` order then label
    // order, exactly the nesting of the Python loops.
    let np = cfg.pool.len() as u64;
    let mut offsets: Vec<u64> = Vec::with_capacity(good.len() + 1);
    let mut acc = 0u64;
    for p in &good {
        offsets.push(acc);
        acc += np.pow(p.iter().map(|&x| x as u32).sum::<u32>());
    }
    offsets.push(acc);
    let total = acc;

    let combos: Vec<Vec<(u64, Vec<usize>)>> = (0..=2).map(|t| combinations(n, t)).collect();
    let t_values = [0usize, 1, 2];

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
        let mut labels: Vec<Label> = Vec::new();
        let mut full: Vec<Label> = Vec::new();
        // locate the pattern containing `start`
        let mut pi = match offsets.binary_search(&start) {
            Ok(i) => i,
            Err(i) => i - 1,
        };
        for index in start..end {
            while index >= offsets[pi + 1] {
                pi += 1;
            }
            if stop.should_stop(index) {
                break;
            }
            let pattern = &good[pi];
            let npres = pattern.iter().map(|&x| x as usize).sum::<usize>();
            let mut x = index - offsets[pi];
            labels.clear();
            labels.resize(npres, ZERO);
            for s in (0..npres).rev() {
                labels[s] = cfg.pool[(x % np) as usize];
                x /= np;
            }
            apply_pattern(pattern, &labels, &slots, &mut full);
            w.graph.fill(&slots, &full);
            build_rows(&w.graph, &mut w.rows);
            let rk =
                kakeya_core::rank(&w.rows, crate::search::P).expect("rank on a well-formed instance");
            let m = w.graph.m;
            let mut tested_here = 0u64;
            for &t in &t_values {
                let den = n - t;
                let budget = cfg.target.mul_int_floor(den as i64) - m;
                if budget < 0 || (den as i64 - rk) > budget {
                    continue;
                }
                for (mask, members) in &combos[t] {
                    let mand_total = w.local_req(n, *mask);
                    if mand_total > budget {
                        continue;
                    }
                    tested_here += 1;
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
                        let line = progress_line(sc, pattern, &labels, gens.len(), t);
                        c.improvements.push(Improvement {
                            index,
                            sc,
                            line: Some(line),
                            witness: None,
                        });
                    }
                    if sc <= cfg.target {
                        let obj = format!(
                            "[\"{}\", {}, {}, {}, {}]",
                            sc,
                            fmt::json_u8(pattern),
                            fmt::json_labels(&labels),
                            fmt::json_gens(&gens),
                            fmt::json_usize(members)
                        );
                        c.hits.push(HitRec {
                            index,
                            progress: None,
                            obj: Some(obj),
                        });
                    }
                }
            }
            if tested_here > 0 {
                c.tested.push((index, tested_here));
            }
        }
        c
    });

    if out.stopped && cfg.verbose {
        println!("TIME LIMIT");
    }
    CyclesResult {
        good: good.len(),
        best: out.merged.best,
        hits: out.merged.hits,
        tested: out.merged.tested,
        stopped: out.stopped,
        elapsed: out.elapsed,
    }
}

pub fn emit(cfg: &CyclesCfg, r: &CyclesResult) {
    let best = r.best.filter(|b| b.is_truthy()).map(|b| b.to_string());
    println!(
        "RESULT {{\"tag\": \"cycles8\", \"pool\": {}, \"best\": {}, \"hits\": {}, \
         \"tested\": {}}}",
        cfg.pool.len(),
        fmt::json_opt_str(best),
        r.hits.len(),
        r.tested
    );
    for h in r.hits.iter().take(20) {
        if let Some(o) = &h.obj {
            println!("HITOBJ {o}");
        }
    }
}
