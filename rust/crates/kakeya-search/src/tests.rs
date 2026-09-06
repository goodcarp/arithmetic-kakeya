//! Unit gates for the pieces the end-to-end fixtures cannot localise:
//! golden vectors from `rust/GOLDEN-VECTORS.json`, the enumeration orders, the
//! Fraction comparisons, and CPython's MT19937.

use kakeya_core::{force_once, rank};

use crate::common::{alphabet_of, combinations, LabelSource};
use crate::frac::Frac;
use crate::graph::{
    build_rows, domains, gen_row, m_of_labels, slots_of, Graph, Label, POOL3, POOL4, POOL6, ZERO,
};
use crate::pyrandom::sample_labels;
use crate::search::{dir_choices, indep_dirs, local_requirement, LocalReqScratch, P};

#[test]
fn domains_match_the_golden_file() {
    let d23 = domains(&[2, 3]);
    assert_eq!(d23, vec![vec![vec![1usize]], vec![vec![1, 1], vec![1, 2], vec![2, 1], vec![2, 2]]]);
    let d222 = domains(&[2, 2, 2]);
    assert_eq!(
        d222,
        vec![
            vec![vec![1usize]],
            vec![vec![1, 1], vec![2, 1]],
            vec![vec![1, 1, 1], vec![1, 2, 1], vec![2, 1, 1], vec![2, 2, 1]],
        ]
    );
    assert_eq!(slots_of(&[2, 2]).len(), 3);
    assert_eq!(slots_of(&[2, 2, 2]).len(), 7);
    assert_eq!(slots_of(&[3, 3]).len(), 8);
    assert_eq!(slots_of(&[2, 2, 3]).len(), 11);
}

#[test]
fn vertex_order_and_index() {
    let v = Graph::vertices(&[2, 3]);
    assert_eq!(
        v,
        vec![
            vec![1, 1],
            vec![1, 2],
            vec![1, 3],
            vec![2, 1],
            vec![2, 2],
            vec![2, 3]
        ]
    );
    for (j, vv) in v.iter().enumerate() {
        assert_eq!(Graph::index(&[2, 3], vv), j);
    }
}

/// The certified 7/4 trapezoid, contract sec 8.3.
#[test]
fn trapezoid_7_4() {
    let d = [2usize, 2];
    let slots = slots_of(&d);
    // f_1(1) = (1,0); f_2(1,1) = (0,1); f_2(2,1) = (1,2)
    let labels: Vec<Label> = vec![(1, 0), (0, 1), (1, 2)];
    assert_eq!(slots.len(), labels.len());
    let g = Graph::from_labels(&d, &slots, &labels);
    assert_eq!(g.n, 4);
    assert_eq!(g.m, 4);
    assert_eq!(m_of_labels(&slots, &labels), 4);
    assert_eq!(
        g.edges,
        vec![
            (0, 2, (1, 0)),
            (1, 3, (1, 0)),
            (0, 1, (0, 1)),
            (2, 3, (1, 2)),
        ]
    );
    let mut rows = Vec::new();
    build_rows(&g, &mut rows);
    assert_eq!(
        rows,
        vec![
            vec![1, 0, 0, 0, -1, 0, 0, 0],
            vec![0, 0, 1, 0, 0, 0, -1, 0],
            vec![0, 1, 0, -1, 0, 0, 0, 0],
            vec![0, 0, 0, 0, 1, 2, -1, -2],
        ]
    );
    assert_eq!(rank(&rows, P).unwrap(), 4);
    assert_eq!(force_once(&rows, 4, &[], P).unwrap(), (false, vec![]));

    // with R = [((1,1),(1,1)), ((2,1),(1,1)), ((2,2),(0,1))] it forces
    rows.push(vec![1, 1, 0, 0, 0, 0, 0, 0]);
    rows.push(vec![0, 0, 0, 0, 1, 1, 0, 0]);
    rows.push(vec![0, 0, 0, 0, 0, 0, 0, 1]);
    assert_eq!(force_once(&rows, 4, &[], P).unwrap(), (true, vec![0, 1, 2, 3]));
    assert_eq!(Frac::new(4 + 3, 4).to_string(), "7/4");
}

/// The 11/6 record object, exactly as recorded in `rust/GOLDEN-VECTORS.json`
/// (`objects.config1_11_6`) and re-verified against the Python on this machine:
/// `d = [2,3]`, `n = 6`, `m = 7`, `rank(base_rows) = 7`, and with the four
/// certified generators it forces from empty `T` for a score of 11/6.
///
/// Note the golden file lists the level-2 edges in the order its hand-written
/// `f_2` dict was keyed ((1,1), (2,1), (1,2), (2,2)); `graph_from_labels`
/// rebuilds that dict in `domains` order ((1,1), (1,2), (2,1), (2,2)), so the
/// edge/row order here is the `domains` one.  Row order changes neither `rank`
/// nor `force` (contract sec 6), and both are asserted below.
#[test]
fn record_11_6() {
    let d = [2usize, 3];
    let slots = slots_of(&d);
    // f_1(1) = (1,0); f_2 = {(1,1):(0,1), (1,2):(1,1), (2,1):(0,1), (2,2):(0,1)}
    let labels: Vec<Label> = vec![(1, 0), (0, 1), (1, 1), (0, 1), (0, 1)];
    let g = Graph::from_labels(&d, &slots, &labels);
    assert_eq!(g.n, 6);
    assert_eq!(g.m, 7);
    assert_eq!(m_of_labels(&slots, &labels), 7);
    assert_eq!(
        g.edges,
        vec![
            (0, 3, (1, 0)),
            (1, 4, (1, 0)),
            (2, 5, (1, 0)),
            (0, 1, (0, 1)),
            (1, 2, (1, 1)),
            (3, 4, (0, 1)),
            (4, 5, (0, 1)),
        ]
    );
    let mut rows = Vec::new();
    build_rows(&g, &mut rows);
    assert_eq!(rows.len(), 7);
    assert_eq!(rank(&rows, P).unwrap(), 7);
    assert!(!force_once(&rows, 6, &[], P).unwrap().0);

    // R = [((1,2),(1,0)), ((2,1),(1,1)), ((1,1),(1,1)), ((1,3),(0,1))]
    // as generator rows on vertices 1, 3, 0, 2.
    for (j, s) in [(1usize, (1i64, 0i64)), (3, (1, 1)), (0, (1, 1)), (2, (0, 1))] {
        let mut r = Vec::new();
        gen_row(6, j, s, &mut r);
        rows.push(r);
    }
    assert_eq!(
        force_once(&rows, 6, &[], P).unwrap(),
        (true, vec![0, 1, 2, 3, 4, 5])
    );
    assert_eq!(Frac::new(7 + 4, 6).to_string(), "11/6");
}

#[test]
fn indep_dirs_caps_at_two() {
    let mut seen = Vec::new();
    assert_eq!(indep_dirs(&[], &mut seen), 0);
    assert_eq!(indep_dirs(&[ZERO, ZERO], &mut seen), 0);
    assert_eq!(indep_dirs(&[(1, 0), (2, 0)], &mut seen), 1);
    assert_eq!(indep_dirs(&[(1, 0), (0, 1), (1, 1)], &mut seen), 2);
    assert_eq!(seen, vec![(1, 0), (0, 1)]);
}

#[test]
fn dir_choices_p6() {
    assert!(dir_choices(&[], &POOL6, 2).is_empty());
    assert_eq!(dir_choices(&[], &POOL6, 0), vec![Vec::<Label>::new()]);
    // (1,0) and (2,0) are parallel, so (1,0) drops out of the k = 1 list
    let ch = dir_choices(&[(2, 0)], &POOL3, 1);
    assert_eq!(ch, vec![vec![(0, 1)], vec![(1, 1)]]);
}

#[test]
fn local_requirement_on_the_empty_graph() {
    let d = [2usize, 2];
    let slots = slots_of(&d);
    let g = Graph::from_labels(&d, &slots, &[ZERO, ZERO, ZERO]);
    let mut sc = LocalReqScratch::default();
    let mut out = Vec::new();
    let total = local_requirement(&g, 4, 0, &mut sc, &mut out);
    assert_eq!(total, 8);
    assert_eq!(out.len(), 4);
    assert!(out.iter().all(|m| m.need == 2));
}

#[test]
fn combinations_order() {
    assert_eq!(combinations(4, 0), vec![(0u64, vec![])]);
    let c = combinations(4, 2);
    let members: Vec<Vec<usize>> = c.iter().map(|(_, m)| m.clone()).collect();
    assert_eq!(
        members,
        vec![
            vec![0, 1],
            vec![0, 2],
            vec![0, 3],
            vec![1, 2],
            vec![1, 3],
            vec![2, 3]
        ]
    );
    assert_eq!(combinations(4, 1).len(), 4);
    assert_eq!(combinations(6, 2).len(), 15);
}

#[test]
fn exhaustive_enumeration_is_product_order() {
    let src = LabelSource::Exhaustive {
        alphabet: alphabet_of(&POOL3),
        nslots: 2,
    };
    assert_eq!(src.total(), 16);
    let mut got = Vec::new();
    let mut buf = Vec::new();
    for i in 0..16 {
        src.decode(i, &mut buf);
        got.push(buf.clone());
    }
    // last slot fastest
    assert_eq!(got[0], vec![ZERO, ZERO]);
    assert_eq!(got[1], vec![ZERO, (1, 0)]);
    assert_eq!(got[4], vec![(1, 0), ZERO]);
    assert_eq!(got[15], vec![(1, 1), (1, 1)]);
}

#[test]
fn fraction_semantics() {
    assert_eq!(Frac::new(8, 4).to_string(), "2");
    assert_eq!(Frac::new(7, 4).to_string(), "7/4");
    assert_eq!(Frac::parse("67/40").unwrap(), Frac::new(67, 40));
    assert_eq!(Frac::parse("2").unwrap(), Frac::new(2, 1));
    // int(target * den) at every worked value in the contract
    assert_eq!(Frac::new(67, 40).mul_int_floor(8), 13);
    assert_eq!(Frac::new(67, 40).mul_int_floor(7), 11);
    assert_eq!(Frac::new(67, 40).mul_int_floor(6), 10);
    assert_eq!(Frac::new(7, 4).mul_int_floor(4), 7);
    assert_eq!(Frac::new(11, 6).mul_int_floor(8), 14);
    assert_eq!(Frac::new(9, 5).mul_int_floor(6), 10);
    assert!(Frac::new(13, 8) < Frac::new(7, 4));
    assert!(!(Frac::new(7, 4) < Frac::new(7, 4)));
    assert!(Frac::new(7, 4) <= Frac::new(7, 4));
    assert!(!Frac::new(0, 5).is_truthy());
}

/// `g2_tall`'s strict-improvement cap: the largest integer with cap/q < 11/6.
/// `g2_tall.py`'s strict-improvement cap, checked against the table produced by
/// the Python itself:
///   `cap = int(Fraction(11,6)*q); if Fraction(cap,q) >= Fraction(11,6): cap -= 1`
/// This calls the driver's own `cap_for`, not a copy of it.
#[test]
fn g2_tall_cap_rule() {
    // (q, cap) for q = 1..=24, generated by the Python expression above.
    const PY: [(i64, i64); 24] = [
        (1, 1), (2, 3), (3, 5), (4, 7), (5, 9), (6, 10), (7, 12), (8, 14),
        (9, 16), (10, 18), (11, 20), (12, 21), (13, 23), (14, 25), (15, 27),
        (16, 29), (17, 31), (18, 32), (19, 34), (20, 36), (21, 38), (22, 40),
        (23, 42), (24, 43),
    ];
    for (q, want) in PY {
        assert_eq!(
            crate::drivers::g2_tall::cap_for(q),
            want,
            "cap_for({q}) should be {want}"
        );
        // and the defining property: cap/q is the largest value strictly below 11/6
        assert!(Frac::new(crate::drivers::g2_tall::cap_for(q), q) < Frac::new(11, 6));
        assert!(Frac::new(crate::drivers::g2_tall::cap_for(q) + 1, q) >= Frac::new(11, 6));
    }
}

/// CPython `random.Random(seed).choice` streams, contract sec 6.
#[test]
fn mt19937_matches_cpython() {
    let a3 = alphabet_of(&POOL3);
    let s = sample_labels(11u64, &a3, 9, 1);
    assert_eq!(
        s[0],
        vec![
            (1, 1),
            (1, 1),
            (1, 1),
            (1, 0),
            (1, 0),
            (1, 1),
            (1, 0),
            (0, 0),
            (1, 1)
        ]
    );
    let a4 = alphabet_of(&POOL4);
    let s = sample_labels(11u64, &a4, 7, 1);
    assert_eq!(
        s[0],
        vec![(1, 1), (1, 2), (1, 1), (1, 1), (1, 2), (1, 2), (1, 0)]
    );
    let a6 = alphabet_of(&POOL6);
    let s = sample_labels(0u64, &a6, 7, 1);
    assert_eq!(
        s[0],
        vec![(2, 1), (1, 1), (2, 1), (1, 1), (0, 0), (0, 1), (1, 2)]
    );
}

/// Every driver progress line that no recorded run exercises (they all report
/// `best null`, so the best-update branch never fires in the corpus).  The
/// expected strings on the right were produced by evaluating the drivers' own
/// f-strings under `/usr/bin/python3` with these exact arguments, so this pins
/// the Rust renderings to CPython's `repr`/`format` and not to a second copy of
/// the format string.
#[test]
fn driver_progress_lines_match_python() {
    use crate::drivers::{cycles8, g2_tall, rzero, scan, stacked};

    let gens: Vec<(usize, Label)> = vec![(0, (1, 0)), (3, (1, 2))];
    let labs: Vec<Label> = vec![(0, 0), (1, 1), (1, -2), (2, 1), (0, 1), (1, 3)];
    assert_eq!(
        g2_tall::progress_line(4, Frac::new(13, 8), 8, &gens, 1, &labs),
        "  [2x4] score 13/8 = 1.6250  m=8 r=2 t=1 \
         labels=((0, 0), (1, 1), (1, -2), (2, 1), (0, 1), (1, 3)) \
         gens=[(0, (1, 0)), (3, (1, 2))]"
    );

    let pattern: [u8; 7] = [0, 1, 1, 1, 1, 1, 1];
    let clabels: Vec<Label> = vec![(1, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 1)];
    assert_eq!(
        cycles8::progress_line(Frac::new(10, 6), &pattern, &clabels, 2, 0),
        "  new best 5/3 = 1.6667  pattern=(0, 1, 1, 1, 1, 1, 1) \
         labels=((1, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 1)) r=2 t=0"
    );

    let rlabels: Vec<Label> = vec![(2, 1), (1, 1), (2, 1), (1, 1), (0, 0), (0, 1), (1, 2)];
    assert_eq!(
        rzero::progress_line(6, 8, Frac::new(6, 8), &rlabels),
        "  generator-free forcing object! m=6 n=8 score=3/4 \
         labels=((2, 1), (1, 1), (2, 1), (1, 1), (0, 0), (0, 1), (1, 2))"
    );

    assert_eq!(
        scan::hit_line(Frac::new(7, 4), "[2, 2]", 4, 3, 0),
        "   HIT 7/4 (=1.7500)  d=[2, 2] m=4 r=3 t=0"
    );

    let slabs: Vec<Label> = vec![(0, 0), (1, 1), (1, -2), (2, 1)];
    assert_eq!(
        stacked::hit_line(Frac::new(13, 8), &slabs, 8, &gens, &[2, 5]),
        "       (Fraction(13, 8), ((0, 0), (1, 1), (1, -2), (2, 1)), 8, \
         [(0, (1, 0)), (3, (1, 2))], [2, 5])"
    );

    // the 1-tuple comma, which CPython's repr keeps
    assert_eq!(crate::fmt::tuple_labels(&[(1, 0)]), "((1, 0),)");
    assert_eq!(crate::fmt::tuple_u8(&[1]), "(1,)");
}

/// `cycles8`'s five 2-regular patterns split into three two-4-cycle graphs
/// and two single 8-cycles; cross-checked against `cycles8.build` in Python
/// (union-find over `ConstructibleGraph.edges()`), and pool-independent.
#[test]
fn cycles8_pattern_cycle_types() {
    use crate::drivers::cycles8::{cycle_lengths, regular_patterns};
    let good = regular_patterns(2, POOL6[0]);
    let types: Vec<Vec<usize>> = good.iter().map(|p| cycle_lengths(p, POOL6[0])).collect();
    assert_eq!(
        types,
        vec![vec![4, 4], vec![4, 4], vec![8], vec![8], vec![4, 4]]
    );
    for p in &good {
        assert_eq!(cycle_lengths(p, POOL3[0]), cycle_lengths(p, POOL6[0]));
    }
}

/// `--patterns` partitions the run: the two-4-cycle patterns and the 8-cycle
/// patterns together reproduce the unrestricted `tested`, `hits` and `best`.
#[test]
fn cycles8_pattern_selection_partitions_the_run() {
    use crate::drivers::cycles8::{run, CyclesCfg};
    let mk = |patterns: Option<Vec<usize>>| CyclesCfg {
        pool: POOL3.to_vec(),
        target: Frac::new(5, 4),
        deg: 2,
        tlimit: None,
        threads: 2,
        verbose: false,
        patterns,
    };
    let all = run(&mk(None));
    let a = run(&mk(Some(vec![0, 1, 4])));
    let b = run(&mk(Some(vec![2, 3])));
    assert!(all.tested > 0);
    assert_eq!(a.tested + b.tested, all.tested);
    assert_eq!(a.hits.len() + b.hits.len(), all.hits.len());
    let min = match (a.best, b.best) {
        (Some(x), Some(y)) => Some(if y < x { y } else { x }),
        (x, y) => x.or(y),
    };
    assert_eq!(all.best, min);
}

/// The g2_tall progress fields: a complete run walks every tuple, and the
/// pair count matches Fable's independent `count_pairs.py` for 2x3 (1587).
#[test]
fn g2_tall_progress_fields() {
    use crate::drivers::g2_tall::{run, TallCfg};
    let r = run(&TallCfg {
        rows: 3,
        max_t: 1,
        tlimit: None,
        threads: 2,
        verbose: false,
    });
    assert!(r.complete);
    assert_eq!((r.walked, r.total), (256, 256));
    assert_eq!(r.pairs, 1587);
}
