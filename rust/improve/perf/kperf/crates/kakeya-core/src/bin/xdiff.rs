//! Differential harness for the perf lens: replay a pure-Python-generated
//! corpus through BOTH `kakeya_core::force` (the audited kernel, copied
//! verbatim) and `kakeya_core::perf::force_fast` (the prototype), and compare
//! each against the pure-Python answer recorded in the corpus.
//!
//!   xdiff <corpus>
use kakeya_core::perf::force_fast;
use kakeya_core::{force, ForceScratch, KErr};
use std::io::{BufRead, BufReader};

fn render(r: &Result<(bool, Vec<i64>), KErr>) -> String {
    match r {
        Ok((ok, t)) => {
            let mut v = t.clone();
            v.sort_unstable();
            format!(
                "{}:{}",
                if *ok { "T" } else { "F" },
                v.iter().map(|x| x.to_string()).collect::<Vec<_>>().join(",")
            )
        }
        Err(KErr::Index) => "X:IndexError".to_string(),
        Err(KErr::ZeroDivision) => "X:ZeroDivisionError".to_string(),
        Err(KErr::Value(_)) => "X:ValueError".to_string(),
    }
}

fn main() {
    let path = std::env::args().nth(1).expect("usage: xdiff <corpus>");
    let f = BufReader::new(std::fs::File::open(&path).expect("open corpus"));
    let mut sc = ForceScratch::new();
    let mut sc2 = ForceScratch::new();
    let (mut n_cases, mut bad_base, mut bad_fast, mut bad_cross) = (0u64, 0u64, 0u64, 0u64);
    let mut shown = 0;
    for line in f.lines() {
        let line = line.expect("read");
        if line.trim().is_empty() {
            continue;
        }
        let parts: Vec<&str> = line.split('|').collect();
        assert_eq!(parts.len(), 5, "bad line: {line}");
        let n: i64 = parts[0].parse().unwrap();
        let p: i64 = parts[1].parse().unwrap();
        let t0: Vec<i64> = if parts[2].is_empty() {
            vec![]
        } else {
            parts[2].split(',').map(|x| x.parse().unwrap()).collect()
        };
        let rows: Vec<Vec<i64>> = if parts[3].is_empty() {
            vec![]
        } else {
            parts[3]
                .split('/')
                .map(|r| {
                    let (ln, body) = r.split_once(':').expect("row needs a length prefix");
                    let ln: usize = ln.parse().unwrap();
                    let v: Vec<i64> = if body.is_empty() {
                        vec![]
                    } else {
                        body.split(',').map(|x| x.parse::<i64>().unwrap()).collect()
                    };
                    assert_eq!(v.len(), ln, "row length prefix mismatch");
                    v
                })
                .collect()
        };
        let expect = parts[4];
        n_cases += 1;
        let a = render(&force(&rows, n, &t0, p, &mut sc));
        let b = render(&force_fast(&rows, n, &t0, p, &mut sc2));
        if a != expect {
            bad_base += 1;
        }
        if b != expect {
            bad_fast += 1;
        }
        if a != b {
            bad_cross += 1;
        }
        if (a != expect || b != expect || a != b) && shown < 15 {
            shown += 1;
            println!("MISMATCH line={n_cases}\n  py   = {expect}\n  base = {a}\n  fast = {b}\n  in   = {line}");
        }
    }
    println!(
        "xdiff: {n_cases} cases | base!=py {bad_base} | fast!=py {bad_fast} | base!=fast {bad_cross}"
    );
    if bad_base + bad_fast + bad_cross > 0 {
        std::process::exit(1);
    }
}
