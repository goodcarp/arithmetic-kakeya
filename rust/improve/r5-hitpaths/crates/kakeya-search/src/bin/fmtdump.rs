//! fmtdump -- exercise the four uncovered "found something" formatters of the
//! Rust drivers on synthetic inputs and echo both the inputs and the produced
//! lines, so a Python script can regenerate the same lines from the *Python*
//! drivers' own f-strings (extracted from src/*.py with `ast`) and diff.
//!
//! Nothing in the driver modules is modified; this binary only calls the
//! already-public formatters.  The one exception is cycles8's HITOBJ string,
//! which is an inline `format!` inside `cycles8::run`; the expression below is
//! copied character-for-character from that call site and is marked HITOBJ_INLINE.

use kakeya_search::drivers::{cycles8, g2_tall, rzero, stacked};
use kakeya_search::fmt;
use kakeya_search::frac::Frac;
use kakeya_search::graph::Label;

fn labs_str(v: &[Label]) -> String {
    if v.is_empty() {
        return "-".to_string();
    }
    v.iter()
        .map(|l| format!("{},{}", l.0, l.1))
        .collect::<Vec<_>>()
        .join(";")
}
fn gens_str(v: &[(usize, Label)]) -> String {
    if v.is_empty() {
        return "-".to_string();
    }
    v.iter()
        .map(|(j, l)| format!("{}:{},{}", j, l.0, l.1))
        .collect::<Vec<_>>()
        .join(";")
}
fn us_str(v: &[usize]) -> String {
    if v.is_empty() {
        return "-".to_string();
    }
    v.iter()
        .map(|x| x.to_string())
        .collect::<Vec<_>>()
        .join(",")
}
fn u8_str(v: &[u8]) -> String {
    if v.is_empty() {
        return "-".to_string();
    }
    v.iter()
        .map(|x| x.to_string())
        .collect::<Vec<_>>()
        .join(",")
}

/// A tiny deterministic LCG so both sides can agree on the case list without
/// sharing a random generator: the cases are echoed, so Python never samples.
struct Lcg(u64);
impl Lcg {
    fn next(&mut self, n: usize) -> usize {
        self.0 = self.0.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        ((self.0 >> 33) as usize) % n
    }
}

fn main() {
    // Every label the drivers can carry: ZERO plus POOL8, plus the negative one.
    let alphabet: [Label; 9] = [
        (0, 0),
        (1, 0),
        (0, 1),
        (1, 1),
        (1, 2),
        (1, 3),
        (2, 1),
        (1, -2),
        (3, 1),
    ];
    let mut rng = Lcg(20260906);
    let mut cases: Vec<(usize, usize, i64, usize, usize, Vec<Label>, Vec<(usize, Label)>, Vec<usize>, Vec<u8>)> =
        Vec::new();

    // Hand-picked corner cases first: empty labels, empty gens, empty T0,
    // 1-element tuples (the repr comma), a negative label, den == 1.
    cases.push((13, 8, 8, 0, 1, vec![], vec![], vec![], vec![1]));
    cases.push((2, 1, 4, 1, 1, vec![(0, 0)], vec![(0, (1, 0))], vec![3], vec![0, 1]));
    cases.push((
        11,
        6,
        12,
        2,
        3,
        vec![(1, -2), (0, 0), (3, 1)],
        vec![(0, (1, -2)), (7, (3, 1))],
        vec![0, 7],
        vec![1, 1, 0, 0, 0, 1, 1],
    ));
    cases.push((0, 1, 0, 0, 1, vec![(0, 0)], vec![], vec![], vec![0]));
    cases.push((
        67,
        40,
        8,
        2,
        6,
        vec![(1, 0), (0, 1), (1, 1), (1, 2)],
        vec![(1, (0, 1)), (2, (1, 1)), (3, (1, 2)), (4, (1, 3)), (5, (2, 1)), (6, (1, -2))],
        vec![2, 5],
        vec![0, 1, 1, 1, 1, 1, 1],
    ));

    // ... then 60 pseudo-random ones over the same shapes.
    for _ in 0..60 {
        let den = 1 + rng.next(16);
        let num = 1 + rng.next(40);
        let m = rng.next(20) as i64;
        let t = rng.next(3);
        let rows = 1 + rng.next(6);
        let nl = rng.next(7);
        let labs: Vec<Label> = (0..nl).map(|_| alphabet[rng.next(9)]).collect();
        let ng = rng.next(7);
        let mut gens: Vec<(usize, Label)> = (0..ng)
            .map(|_| (rng.next(8), alphabet[1 + rng.next(8)]))
            .collect();
        gens.sort_unstable();
        gens.dedup_by_key(|g| g.0);
        let nt = rng.next(4);
        let mut t0: Vec<usize> = (0..nt).map(|_| rng.next(8)).collect();
        t0.sort_unstable();
        t0.dedup();
        let np = 1 + rng.next(7);
        let pat: Vec<u8> = (0..np).map(|_| rng.next(2) as u8).collect();
        cases.push((num, den, m, t, rows, labs, gens, t0, pat));
    }

    for (i, (num, den, m, t, rows, labs, gens, t0, pat)) in cases.iter().enumerate() {
        let sc = Frac::new(*num as i64, *den as i64);
        println!(
            "CASE {i} num={} den={} m={m} t={t} rows={rows} r={} LABS={} GENS={} T0={} PAT={}",
            sc.num,
            sc.den,
            gens.len(),
            labs_str(labs),
            gens_str(gens),
            us_str(t0),
            u8_str(pat)
        );
        println!("G2 {}", g2_tall::progress_line(*rows, sc, *m, gens, *t, labs));
        println!(
            "C8P {}",
            cycles8::progress_line(sc, pat, labs, gens.len(), *t)
        );
        // HITOBJ_INLINE -- copied verbatim from drivers/cycles8.rs
        println!(
            "C8H [\"{}\", {}, {}, {}, {}]",
            sc,
            fmt::json_u8(pat),
            fmt::json_labels(labs),
            fmt::json_gens(gens),
            fmt::json_usize(t0)
        );
        println!("ST {}", stacked::hit_line(sc, labs, *m, gens, t0));
        println!("RZ {}", rzero::progress_line(*m, 8, sc, labs));
    }
}
