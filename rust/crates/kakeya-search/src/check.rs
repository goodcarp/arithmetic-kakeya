//! `check`: run every CHEAP fixture from the S2 driver contract and compare
//! against the recorded Python oracle.  Exits nonzero if anything FAILs.

use crate::common::alphabet_of;
use crate::drivers::{cycles8, g2_tall, rzero, scan};
use crate::frac::Frac;
use crate::graph::{Label, POOL3, POOL4, POOL6};
use crate::pyrandom::sample_labels;

struct Report {
    lines: Vec<String>,
    failed: usize,
}

impl Report {
    fn pass(&mut self, tag: &str, detail: String) {
        self.lines.push(format!("PASS {tag}: {detail}"));
    }
    fn fail(&mut self, tag: &str, detail: String) {
        self.failed += 1;
        self.lines.push(format!("FAIL {tag}: {detail}"));
    }
    fn skip(&mut self, tag: &str, detail: &str) {
        self.lines.push(format!("SKIP {tag}: {detail}"));
    }
}

/// FNV-1a 64 over the HITOBJ stream (`\n`-joined), so `check` gates every hit
/// line and not just the first and last.  The expected values below were taken
/// from the unmodified Python drivers' own stdout on this machine.
fn fnv1a64(s: &str) -> u64 {
    let mut h: u64 = 0xcbf2_9ce4_8422_2325;
    for b in s.as_bytes() {
        h ^= *b as u64;
        h = h.wrapping_mul(0x0000_0100_0000_01b3);
    }
    h
}

fn hits_digest(hits: &[crate::engine::HitRec]) -> u64 {
    let joined: Vec<&str> = hits
        .iter()
        .filter_map(|h| h.obj.as_deref())
        .collect();
    fnv1a64(&joined.join("\n"))
}

const N4_P6_T1_HITOBJ_DIGEST: u64 = 0xe8f5_6b16_fc6c_9314;

const FIRST_HITOBJ: &str = "{\"d\": [2, 2], \"labels\": [[1, 0], [0, 1], [1, 1]], \"m\": 4, \
\"gens\": [[0, [1, 1]], [1, [1, 2]], [3, [0, 1]]], \"T0\": [], \"score\": \"7/4\", \"n\": 4}";
const LAST_HITOBJ: &str = "{\"d\": [2, 2], \"labels\": [[2, 1], [1, 3], [1, 3]], \"m\": 4, \
\"gens\": [[0, [1, 0]], [1, [1, 1]], [2, [1, 1]]], \"T0\": [], \"score\": \"7/4\", \"n\": 4}";

#[allow(clippy::too_many_arguments)]
fn check_scan(
    rep: &mut Report,
    threads: usize,
    tag: &str,
    d: &[usize],
    pool: &[Label],
    max_t: usize,
    target: &str,
    exp_scanned: u64,
    exp_total: u64,
    exp_best: Option<&str>,
    exp_hits: usize,
    exp_complete: bool,
    hitobjs: Option<(&str, &str)>,
    exp_digest: Option<u64>,
) {
    let cfg = scan::ScanCfg {
        tag: tag.to_string(),
        d: d.to_vec(),
        pool: pool.to_vec(),
        max_t,
        target: Frac::parse(target).expect("target"),
        limit: None,
        seed: 11,
        tlimit: None,
        threads,
        verbose: false,
    };
    let r = scan::run(&cfg);
    let got_best = r.best.filter(|b| b.is_truthy()).map(|b| b.to_string());
    let mut errs: Vec<String> = Vec::new();
    if r.scanned != exp_scanned {
        errs.push(format!("scanned {} != {}", r.scanned, exp_scanned));
    }
    if r.total != exp_total {
        errs.push(format!("total {} != {}", r.total, exp_total));
    }
    if got_best.as_deref() != exp_best {
        errs.push(format!("best {got_best:?} != {exp_best:?}"));
    }
    if r.hits.len() != exp_hits {
        errs.push(format!("hits {} != {}", r.hits.len(), exp_hits));
    }
    if r.complete != exp_complete {
        errs.push(format!("complete {} != {}", r.complete, exp_complete));
    }
    if let Some((first, last)) = hitobjs {
        let got_first = r.hits.first().and_then(|h| h.obj.clone()).unwrap_or_default();
        let got_last = r.hits.last().and_then(|h| h.obj.clone()).unwrap_or_default();
        if got_first != first {
            errs.push(format!("first HITOBJ\n  got {got_first}\n  exp {first}"));
        }
        if got_last != last {
            errs.push(format!("last HITOBJ\n  got {got_last}\n  exp {last}"));
        }
    }
    if let Some(want) = exp_digest {
        let got = hits_digest(&r.hits);
        if got != want {
            errs.push(format!("HITOBJ digest {got:#018x} != {want:#018x}"));
        }
    }
    let detail = format!(
        "scanned {}/{} best {} hits {} complete {} [{:.2}s]",
        r.scanned,
        r.total,
        got_best.unwrap_or_else(|| "null".into()),
        r.hits.len(),
        r.complete,
        r.elapsed
    );
    if errs.is_empty() {
        rep.pass(tag, detail);
    } else {
        rep.fail(tag, format!("{} | {}", detail, errs.join("; ")));
    }
}

#[allow(clippy::too_many_arguments)]
fn check_rzero(
    rep: &mut Report,
    threads: usize,
    tag: &str,
    d: &[usize],
    pool: &[Label],
    limit: Option<usize>,
    exp_scanned: u64,
    exp_total: u64,
    exp_forcing: u64,
    exp_complete: bool,
) {
    let cfg = rzero::RzeroCfg {
        d: d.to_vec(),
        pool: pool.to_vec(),
        limit,
        seed: 0,
        tlimit: None,
        threads,
        verbose: false,
    };
    let r = rzero::run(&cfg);
    let mut errs: Vec<String> = Vec::new();
    if r.scanned != exp_scanned {
        errs.push(format!("scanned {} != {}", r.scanned, exp_scanned));
    }
    if r.total != exp_total {
        errs.push(format!("total {} != {}", r.total, exp_total));
    }
    if r.forcing != exp_forcing {
        errs.push(format!("forcing_objects {} != {}", r.forcing, exp_forcing));
    }
    if r.best.is_some() {
        errs.push(format!("best_score {:?} != null", r.best.map(|b| b.to_string())));
    }
    if r.complete != exp_complete {
        errs.push(format!("complete {} != {}", r.complete, exp_complete));
    }
    let detail = format!(
        "scanned {}/{} forcing_objects {} complete {} [{:.2}s]",
        r.scanned, r.total, r.forcing, r.complete, r.elapsed
    );
    if errs.is_empty() {
        rep.pass(tag, detail);
    } else {
        rep.fail(tag, format!("{} | {}", detail, errs.join("; ")));
    }
}

/// `g2_tall.run(rows_, max_t)` on the small 2 x 3 box.  Verified against the
/// unmodified `g2_tall.py` via `rust/oracle_drivers.py g2-tall 3 <max_t>`:
/// both max_t = 0 and max_t = 1 give `best null, hits 0` -- the cap rule is a
/// *strict* improvement on 11/6, and 11/6 itself is the best this box reaches.
/// `exp_pairs` is the (graph, T0) pair count from Fable's independent
/// `adversary-fable/count_pairs.py` (2x3, max_t = 1: 1587; its t = 0 buckets
/// sum to 237, which is the max_t = 0 count).
fn check_g2_tall(
    rep: &mut Report,
    threads: usize,
    rows: usize,
    max_t: usize,
    exp_best: Option<&str>,
    exp_hits: usize,
    exp_pairs: u64,
) {
    let cfg = g2_tall::TallCfg {
        rows,
        max_t,
        tlimit: None,
        threads,
        verbose: false,
    };
    let r = g2_tall::run(&cfg);
    let got_best = r.best.filter(|b| b.is_truthy()).map(|b| b.to_string());
    let tag = format!("g2_tall_2x{rows}_t{max_t}");
    let mut errs: Vec<String> = Vec::new();
    if got_best.as_deref() != exp_best {
        errs.push(format!("best {got_best:?} != {exp_best:?}"));
    }
    if r.hits != exp_hits {
        errs.push(format!("hits {} != {}", r.hits, exp_hits));
    }
    if !r.complete {
        errs.push("complete false (no tlimit was set)".to_string());
    }
    if r.walked != r.total {
        errs.push(format!("walked {} != total {}", r.walked, r.total));
    }
    if r.pairs != exp_pairs {
        errs.push(format!("pairs {} != {}", r.pairs, exp_pairs));
    }
    let detail = format!(
        "best {} hits {} complete {} walked {}/{} pairs {} [{:.2}s]",
        got_best.unwrap_or_else(|| "null".into()),
        r.hits,
        r.complete,
        r.walked,
        r.total,
        r.pairs,
        r.elapsed
    );
    if errs.is_empty() {
        rep.pass(&tag, detail);
    } else {
        rep.fail(&tag, format!("{} | {}", detail, errs.join("; ")));
    }
}

/// `cycles8.main`'s step-1 pre-pass, which is instant, pool-independent and
/// deterministic.  The five patterns, their `npres` counts and the two
/// enumeration totals are all recorded in the S2 target sheet
/// (`cycles8_pool6` inputs: good_patterns, npres_per_pattern,
/// exhaustive_total 57240; `cycles8_pool8`: exhaustive_total 303616), and were
/// re-confirmed by running the unmodified `cycles8.py` (its first stdout line
/// `5 presence patterns are 2-regular with m = 8`).
fn check_cycles8_patterns(rep: &mut Report) {
    const WANT: [[u8; 7]; 5] = [
        [0, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 1, 1, 1, 1],
        [1, 0, 1, 1, 1, 0, 0],
        [1, 1, 0, 0, 0, 1, 1],
        [1, 1, 1, 0, 0, 0, 0],
    ];
    let good = cycles8::regular_patterns(2, POOL6[0]);
    let mut errs: Vec<String> = Vec::new();
    if good.len() != WANT.len() {
        errs.push(format!("{} patterns != {}", good.len(), WANT.len()));
    } else {
        for (i, w) in WANT.iter().enumerate() {
            if good[i] != w {
                errs.push(format!("pattern {i} {:?} != {w:?}", good[i]));
            }
        }
    }
    let npres: Vec<usize> = good
        .iter()
        .map(|p| p.iter().map(|&x| x as usize).sum())
        .collect();
    if npres != vec![6, 5, 4, 4, 3] {
        errs.push(format!("npres {npres:?} != [6, 5, 4, 4, 3]"));
    }
    let t6 = cycles8::pattern_total(&good, 6);
    let t8 = cycles8::pattern_total(&good, 8);
    if t6 != 57240 {
        errs.push(format!("POOL6 total {t6} != 57240"));
    }
    if t8 != 303616 {
        errs.push(format!("POOL8 total {t8} != 303616"));
    }
    let detail = format!("{} patterns, npres {npres:?}, POOL6 {t6}, POOL8 {t8}", good.len());
    if errs.is_empty() {
        rep.pass("cycles8_patterns", detail);
    } else {
        rep.fail("cycles8_patterns", format!("{} | {}", detail, errs.join("; ")));
    }
}

fn check_rng(rep: &mut Report) {
    let cases: [(u64, &[Label], usize, &[Label]); 3] = [
        (
            11,
            &POOL3,
            9,
            &[(1, 1), (1, 1), (1, 1), (1, 0), (1, 0), (1, 1), (1, 0), (0, 0), (1, 1)],
        ),
        (
            11,
            &POOL4,
            7,
            &[(1, 1), (1, 2), (1, 1), (1, 1), (1, 2), (1, 2), (1, 0)],
        ),
        (
            0,
            &POOL6,
            7,
            &[(2, 1), (1, 1), (2, 1), (1, 1), (0, 0), (0, 1), (1, 2)],
        ),
    ];
    for (seed, pool, nslots, expect) in cases {
        let alpha = alphabet_of(pool);
        let got = sample_labels(seed, &alpha, nslots, 1);
        let tag = format!("rng_seed{}_pool{}_slots{}", seed, pool.len(), nslots);
        if got[0] == expect {
            rep.pass(&tag, format!("{:?}", got[0]));
        } else {
            rep.fail(&tag, format!("got {:?} exp {expect:?}", got[0]));
        }
    }
}

/// Returns (report lines, number of failures).
pub fn run(threads: usize) -> (Vec<String>, usize) {
    let mut rep = Report {
        lines: Vec::new(),
        failed: 0,
    };

    check_scan(
        &mut rep,
        threads,
        "n4_p6_t1",
        &[2, 2],
        &POOL6,
        1,
        "7/4",
        343,
        343,
        Some("7/4"),
        120,
        true,
        Some((FIRST_HITOBJ, LAST_HITOBJ)),
        Some(N4_P6_T1_HITOBJ_DIGEST),
    );
    check_scan(
        &mut rep, threads, "g2_23_t1", &[2, 3], &POOL3, 1, "9/5", 1024, 1024, None, 0, true, None,
        None,
    );
    check_scan(
        &mut rep, threads, "g2_32_t1", &[3, 2], &POOL3, 1, "9/5", 1024, 1024, None, 0, true, None,
        None,
    );
    check_rzero(
        &mut rep, threads, "rzero_2x2_pool6", &[2, 2], &POOL6, None, 343, 343, 0, true,
    );
    check_rzero(
        &mut rep, threads, "rzero_2x2x2_pool4", &[2, 2, 2], &POOL4, None, 78125, 78125, 0, true,
    );
    check_rzero(
        &mut rep, threads, "rzero_2x3_pool4", &[2, 3], &POOL4, None, 3125, 3125, 0, true,
    );
    check_rzero(
        &mut rep, threads, "rzero_3x2_pool4", &[3, 2], &POOL4, None, 3125, 3125, 0, true,
    );
    check_rzero(
        &mut rep,
        threads,
        "rzero_2x2x2_pool6_lim60000",
        &[2, 2, 2],
        &POOL6,
        Some(60000),
        60000,
        60000,
        0,
        false,
    );
    check_cycles8_patterns(&mut rep);
    check_g2_tall(&mut rep, threads, 3, 0, None, 0, 237);
    check_g2_tall(&mut rep, threads, 3, 1, None, 0, 1587);
    check_rng(&mut rep);
    rep.skip("ladder", "pure sympy, no force/rank call -- not ported (contract sec 2.8)");
    rep.skip("schemes", "pure sympy, no force/rank call -- not ported (contract sec 2.8)");

    (rep.lines, rep.failed)
}
