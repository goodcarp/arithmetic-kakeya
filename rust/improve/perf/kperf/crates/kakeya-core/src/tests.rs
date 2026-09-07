//! Generated from the S1 edge-case list by evaluating the real
//! `src/fastcore.py` under /usr/bin/python3 with `_INV.clear()` before each
//! call.  Do not hand-edit expectations.
use super::*;

fn sorted(mut v: Vec<i64>) -> Vec<i64> {
    v.sort_unstable();
    v
}

#[test]
fn case_00() {
    // force([], 0, set())
    // n=0: loop guard len(T)<0 is false, returns True with no work
    let rows: Vec<Vec<i64>> = vec![];
    let t0: Vec<i64> = vec![];
    let (ok, t) = force_once(&rows, 0, &t0, 2147483647).unwrap();
    assert!(ok);
    assert_eq!(sorted(t), vec![]);
}

#[test]
fn case_01() {
    // force([], 1, set())
    // no rows at all: B empty, piv empty, nothing forceable
    let rows: Vec<Vec<i64>> = vec![];
    let t0: Vec<i64> = vec![];
    let (ok, t) = force_once(&rows, 1, &t0, 2147483647).unwrap();
    assert!(!ok);
    assert_eq!(sorted(t), vec![]);
}

#[test]
fn case_02() {
    // force([], 2, {0,1})
    // T0 already covers range(n), zero rounds run
    let rows: Vec<Vec<i64>> = vec![];
    let t0: Vec<i64> = vec![0, 1];
    let (ok, t) = force_once(&rows, 2, &t0, 2147483647).unwrap();
    assert!(ok);
    assert_eq!(sorted(t), vec![0, 1]);
}

#[test]
fn case_03() {
    // force([], 2, {0,5})
    // out-of-range index counts toward len(T) and short-circuits the loop
    let rows: Vec<Vec<i64>> = vec![];
    let t0: Vec<i64> = vec![0, 5];
    let (ok, t) = force_once(&rows, 2, &t0, 2147483647).unwrap();
    assert!(ok);
    assert_eq!(sorted(t), vec![0, 5]);
}

#[test]
fn case_04() {
    // force([], 2, {-1,0})
    // negative index in T0 likewise counts toward len(T)
    let rows: Vec<Vec<i64>> = vec![];
    let t0: Vec<i64> = vec![-1, 0];
    let (ok, t) = force_once(&rows, 2, &t0, 2147483647).unwrap();
    assert!(ok);
    assert_eq!(sorted(t), vec![-1, 0]);
}

#[test]
fn case_05() {
    // force([[1,-1,0,0]], 2, {5})
    // returns True with vertex 1 never forced -- the sharpest accident
    let rows: Vec<Vec<i64>> = vec![vec![1, -1, 0, 0]];
    let t0: Vec<i64> = vec![5];
    let (ok, t) = force_once(&rows, 2, &t0, 2147483647).unwrap();
    assert!(ok);
    assert_eq!(sorted(t), vec![0, 5]);
}

#[test]
fn case_06() {
    // force([[1,-1,0,0,0,0],[0,0,1,-1,0,0],[0,0,0,0,1,-1]], 3, set())
    // baseline: all three force, ascending
    let rows: Vec<Vec<i64>> = vec![vec![1, -1, 0, 0, 0, 0], vec![0, 0, 1, -1, 0, 0], vec![0, 0, 0, 0, 1, -1]];
    let t0: Vec<i64> = vec![];
    let (ok, t) = force_once(&rows, 3, &t0, 2147483647).unwrap();
    assert!(ok);
    assert_eq!(sorted(t), vec![0, 1, 2]);
}

#[test]
fn case_07() {
    // force([[1,-1,0,0,0,0],[0,0,1,-1,0,0],[0,0,0,0,1,-1]], 3, {9})
    // ascending scan order becomes OBSERVABLE: vertex 2 never forced
    let rows: Vec<Vec<i64>> = vec![vec![1, -1, 0, 0, 0, 0], vec![0, 0, 1, -1, 0, 0], vec![0, 0, 0, 0, 1, -1]];
    let t0: Vec<i64> = vec![9];
    let (ok, t) = force_once(&rows, 3, &t0, 2147483647).unwrap();
    assert!(ok);
    assert_eq!(sorted(t), vec![0, 1, 9]);
}

#[test]
fn case_08() {
    // force([[1,-1,0,0,0,0],[0,0,1,-1,0,0],[0,0,0,0,1,-1]], 3, {-1,-2})
    // two junk entries: only vertex 0 gets forced
    let rows: Vec<Vec<i64>> = vec![vec![1, -1, 0, 0, 0, 0], vec![0, 0, 1, -1, 0, 0], vec![0, 0, 0, 0, 1, -1]];
    let t0: Vec<i64> = vec![-2, -1];
    let (ok, t) = force_once(&rows, 3, &t0, 2147483647).unwrap();
    assert!(ok);
    assert_eq!(sorted(t), vec![-2, -1, 0]);
}

#[test]
fn case_09() {
    // force([[1,-1,0,0]], 2, set())
    // partial success then stuck: (False, {0}) -- failure still returns the closure
    let rows: Vec<Vec<i64>> = vec![vec![1, -1, 0, 0]];
    let t0: Vec<i64> = vec![];
    let (ok, t) = force_once(&rows, 2, &t0, 2147483647).unwrap();
    assert!(!ok);
    assert_eq!(sorted(t), vec![0]);
}

#[test]
fn case_10() {
    // force([[0,0,0,0]], 2, set())
    // the sole row is dropped by the nz filter, B is empty
    let rows: Vec<Vec<i64>> = vec![vec![0, 0, 0, 0]];
    let t0: Vec<i64> = vec![];
    let (ok, t) = force_once(&rows, 2, &t0, 2147483647).unwrap();
    assert!(!ok);
    assert_eq!(sorted(t), vec![]);
}

#[test]
fn case_11() {
    // force([[0,0,0,0],[1,0,0,0],[0,1,0,0]], 2, {1})
    // zero row mixed with real ones; nz filter must not shift piv/B indices
    let rows: Vec<Vec<i64>> = vec![vec![0, 0, 0, 0], vec![1, 0, 0, 0], vec![0, 1, 0, 0]];
    let t0: Vec<i64> = vec![1];
    let (ok, t) = force_once(&rows, 2, &t0, 2147483647).unwrap();
    assert!(ok);
    assert_eq!(sorted(t), vec![0, 1]);
}

#[test]
fn case_12() {
    // force([[1,0,0,0],[1,0,0,0],[0,1,0,0],[0,1,0,0]], 2, {1})
    // duplicate rows; exercises the rk>=nB early break
    let rows: Vec<Vec<i64>> = vec![vec![1, 0, 0, 0], vec![1, 0, 0, 0], vec![0, 1, 0, 0], vec![0, 1, 0, 0]];
    let t0: Vec<i64> = vec![1];
    let (ok, t) = force_once(&rows, 2, &t0, 2147483647).unwrap();
    assert!(ok);
    assert_eq!(sorted(t), vec![0, 1]);
}

#[test]
fn case_13() {
    // force([[1,0,0,0],[0,1,0,0],[1,0,-1,0]], 2, set())
    // two independent gens force v0, one edge is not enough for v1
    let rows: Vec<Vec<i64>> = vec![vec![1, 0, 0, 0], vec![0, 1, 0, 0], vec![1, 0, -1, 0]];
    let t0: Vec<i64> = vec![];
    let (ok, t) = force_once(&rows, 2, &t0, 2147483647).unwrap();
    assert!(!ok);
    assert_eq!(sorted(t), vec![0]);
}

#[test]
fn case_14() {
    // force([[1,0,0,0],[0,1,0,0],[1,0,-1,0],[0,1,0,-1]], 2, set())
    // full cascade to success across two rounds
    let rows: Vec<Vec<i64>> = vec![vec![1, 0, 0, 0], vec![0, 1, 0, 0], vec![1, 0, -1, 0], vec![0, 1, 0, -1]];
    let t0: Vec<i64> = vec![];
    let (ok, t) = force_once(&rows, 2, &t0, 2147483647).unwrap();
    assert!(ok);
    assert_eq!(sorted(t), vec![0, 1]);
}

#[test]
fn case_15() {
    // force([[1,0,0,0],[0,1,0,0],[1,0,-1,0],[0,1,0,-1]], 2, {0})
    // warm start from nonempty T0 must give the same closure
    let rows: Vec<Vec<i64>> = vec![vec![1, 0, 0, 0], vec![0, 1, 0, 0], vec![1, 0, -1, 0], vec![0, 1, 0, -1]];
    let t0: Vec<i64> = vec![0];
    let (ok, t) = force_once(&rows, 2, &t0, 2147483647).unwrap();
    assert!(ok);
    assert_eq!(sorted(t), vec![0, 1]);
}

#[test]
fn case_16() {
    // force([[1,1,0,0],[0,0,1,1]], 2, set(), 2)
    // p=2 collapses (1,1) onto (1,-1): succeeds only mod 2
    let rows: Vec<Vec<i64>> = vec![vec![1, 1, 0, 0], vec![0, 0, 1, 1]];
    let t0: Vec<i64> = vec![];
    let (ok, t) = force_once(&rows, 2, &t0, 2).unwrap();
    assert!(ok);
    assert_eq!(sorted(t), vec![0, 1]);
}

#[test]
fn case_17() {
    // force([[1,1,0,0],[0,0,1,1]], 2, set(), 2147483647)
    // same rows at the default p fail -- pins p-sensitivity
    let rows: Vec<Vec<i64>> = vec![vec![1, 1, 0, 0], vec![0, 0, 1, 1]];
    let t0: Vec<i64> = vec![];
    let (ok, t) = force_once(&rows, 2, &t0, 2147483647).unwrap();
    assert!(!ok);
    assert_eq!(sorted(t), vec![]);
}

#[test]
fn case_18() {
    // force([[3,-3,0,0],[0,0,1,-1]], 2, set())
    // pivot value 3 goes through _inv; this is the case whose answer FLIPS under _INV cross-p contamination
    let rows: Vec<Vec<i64>> = vec![vec![3, -3, 0, 0], vec![0, 0, 1, -1]];
    let t0: Vec<i64> = vec![];
    let (ok, t) = force_once(&rows, 2, &t0, 2147483647).unwrap();
    assert!(ok);
    assert_eq!(sorted(t), vec![0, 1]);
}

#[test]
fn case_19() {
    // force([[2147483647,2147483647,0,0],[0,0,1,-1]], 2, set())
    // entries equal to p reduce to 0, row is dropped, v0 unforceable
    let rows: Vec<Vec<i64>> = vec![vec![2147483647, 2147483647, 0, 0], vec![0, 0, 1, -1]];
    let t0: Vec<i64> = vec![];
    let (ok, t) = force_once(&rows, 2, &t0, 2147483647).unwrap();
    assert!(!ok);
    assert_eq!(sorted(t), vec![1]);
}

#[test]
fn case_20() {
    // force([[2147483648,-2147483646,0,0]], 1, set())
    // entries just past +/-2^31 both reduce to 1, giving (1,1) not (1,-1)
    let rows: Vec<Vec<i64>> = vec![vec![2147483648, -2147483646, 0, 0]];
    let t0: Vec<i64> = vec![];
    let (ok, t) = force_once(&rows, 1, &t0, 2147483647).unwrap();
    assert!(!ok);
    assert_eq!(sorted(t), vec![]);
}

#[test]
fn case_21() {
    // force([[1099511627777,-1099511627777,0,0],[0,0,1,-1]], 2, set())
    // 2^40-scale entries must be floor-reduced before anything else
    let rows: Vec<Vec<i64>> = vec![vec![1099511627777, -1099511627777, 0, 0], vec![0, 0, 1, -1]];
    let t0: Vec<i64> = vec![];
    let (ok, t) = force_once(&rows, 2, &t0, 2147483647).unwrap();
    assert!(ok);
    assert_eq!(sorted(t), vec![0, 1]);
}

#[test]
fn case_22() {
    // force([[1,-1,9,9]], 1, set())
    // row longer than 2n: trailing columns are never read
    let rows: Vec<Vec<i64>> = vec![vec![1, -1, 9, 9]];
    let t0: Vec<i64> = vec![];
    let (ok, t) = force_once(&rows, 1, &t0, 2147483647).unwrap();
    assert!(ok);
    assert_eq!(sorted(t), vec![0]);
}

#[test]
fn case_23() {
    // force([[1,0]], 2, set())
    // row shorter than 2n raises IndexError
    let rows: Vec<Vec<i64>> = vec![vec![1, 0]];
    let t0: Vec<i64> = vec![];
    assert_eq!(force_once(&rows, 2, &t0, 2147483647), Err(KErr::Index));
}

#[test]
fn case_24() {
    // force([[1,0,0,0],[0,1]], 2, set())
    // ragged rows raise IndexError
    let rows: Vec<Vec<i64>> = vec![vec![1, 0, 0, 0], vec![0, 1]];
    let t0: Vec<i64> = vec![];
    assert_eq!(force_once(&rows, 2, &t0, 2147483647), Err(KErr::Index));
}

#[test]
fn case_25() {
    // force([[True,False,False,False],[False,True,False,False]], 2, set())
    // bools are ints at the boundary
    let rows: Vec<Vec<i64>> = vec![vec![1, 0, 0, 0], vec![0, 1, 0, 0]];
    let t0: Vec<i64> = vec![];
    let (ok, t) = force_once(&rows, 2, &t0, 2147483647).unwrap();
    assert!(!ok);
    assert_eq!(sorted(t), vec![0]);
}

#[test]
fn case_26() {
    // force([[1,0,0,0],[0,1,0,0],[1,0,-1,0],[0,1,0,-1]], 2, [0,0])
    // T0 as a list with a duplicate
    let rows: Vec<Vec<i64>> = vec![vec![1, 0, 0, 0], vec![0, 1, 0, 0], vec![1, 0, -1, 0], vec![0, 1, 0, -1]];
    let t0: Vec<i64> = vec![0];
    let (ok, t) = force_once(&rows, 2, &t0, 2147483647).unwrap();
    assert!(ok);
    assert_eq!(sorted(t), vec![0, 1]);
}

#[test]
fn case_27() {
    // force([[1,0,0,0],[0,1,0,0],[1,0,-1,0],[0,1,0,-1]], 2, frozenset({0}))
    // T0 as a frozenset
    let rows: Vec<Vec<i64>> = vec![vec![1, 0, 0, 0], vec![0, 1, 0, 0], vec![1, 0, -1, 0], vec![0, 1, 0, -1]];
    let t0: Vec<i64> = vec![0];
    let (ok, t) = force_once(&rows, 2, &t0, 2147483647).unwrap();
    assert!(ok);
    assert_eq!(sorted(t), vec![0, 1]);
}

#[test]
fn case_28() {
    // force(((1,0,0,0),(0,1,0,0),(1,0,-1,0),(0,1,0,-1)), 2, (0,))
    // rows as a tuple of tuples, T0 as a tuple
    let rows: Vec<Vec<i64>> = vec![vec![1, 0, 0, 0], vec![0, 1, 0, 0], vec![1, 0, -1, 0], vec![0, 1, 0, -1]];
    let t0: Vec<i64> = vec![0];
    let (ok, t) = force_once(&rows, 2, &t0, 2147483647).unwrap();
    assert!(ok);
    assert_eq!(sorted(t), vec![0, 1]);
}

#[test]
fn case_29() {
    // force([[1,0,0,0],[0,1,0,0],[1,0,-1,0],[0,1,0,-1]], 2, {True})
    // bool in T0 aliases index 1; returned set is == {0,1}
    let rows: Vec<Vec<i64>> = vec![vec![1, 0, 0, 0], vec![0, 1, 0, 0], vec![1, 0, -1, 0], vec![0, 1, 0, -1]];
    let t0: Vec<i64> = vec![1];
    let (ok, t) = force_once(&rows, 2, &t0, 2147483647).unwrap();
    assert!(ok);
    assert_eq!(sorted(t), vec![0, 1]);
}

#[test]
fn case_30() {
    // force([[1,0,0,0]], 0, {7})
    // n=0 with junk T0: returns True carrying the junk through
    let rows: Vec<Vec<i64>> = vec![vec![1, 0, 0, 0]];
    let t0: Vec<i64> = vec![7];
    let (ok, t) = force_once(&rows, 0, &t0, 2147483647).unwrap();
    assert!(ok);
    assert_eq!(sorted(t), vec![7]);
}

#[test]
fn case_31() {
    // force([[1,-1]], -1, set())
    // negative n: loop never runs
    let rows: Vec<Vec<i64>> = vec![vec![1, -1]];
    let t0: Vec<i64> = vec![];
    let (ok, t) = force_once(&rows, -1, &t0, 2147483647).unwrap();
    assert!(ok);
    assert_eq!(sorted(t), vec![]);
}

#[test]
fn case_32() {
    // force([[1,-1,0,0],[0,0,1,-1]], 2, set(), 1000000007)
    // a different large prime p
    let rows: Vec<Vec<i64>> = vec![vec![1, -1, 0, 0], vec![0, 0, 1, -1]];
    let t0: Vec<i64> = vec![];
    let (ok, t) = force_once(&rows, 2, &t0, 1000000007).unwrap();
    assert!(ok);
    assert_eq!(sorted(t), vec![0, 1]);
}

#[test]
fn case_33() {
    // force([[3,1,0,0],[1,3,0,0]], 1, set(), 4)
    // composite p: pow(a,p-2,p) is not an inverse, must reproduce the garbage
    let rows: Vec<Vec<i64>> = vec![vec![3, 1, 0, 0], vec![1, 3, 0, 0]];
    let t0: Vec<i64> = vec![];
    let (ok, t) = force_once(&rows, 1, &t0, 4).unwrap();
    assert!(!ok);
    assert_eq!(sorted(t), vec![]);
}

#[test]
fn case_34() {
    // force([[1,0,0,0]], 1, set(), 0)
    // p=0 raises ZeroDivisionError from the first % p
    let rows: Vec<Vec<i64>> = vec![vec![1, 0, 0, 0]];
    let t0: Vec<i64> = vec![];
    assert_eq!(force_once(&rows, 1, &t0, 0), Err(KErr::ZeroDivision));
}

#[test]
fn case_35() {
    // force([[1,0,0,0,-1,0,0,0],[0,0,1,0,0,0,-1,0],[0,1,0,-1,0,0,0,0],[0,0,0,0,1,2,-1,-2],[0,1,0,0,0,0,0,0],[0,0,1,0,0,0,0,0],[0,0,0,0,1,1,0,0]], 4, set())
    // a real 7x8 build_rows matrix from d=[2,2] with POOL4 labels
    let rows: Vec<Vec<i64>> = vec![vec![1, 0, 0, 0, -1, 0, 0, 0], vec![0, 0, 1, 0, 0, 0, -1, 0], vec![0, 1, 0, -1, 0, 0, 0, 0], vec![0, 0, 0, 0, 1, 2, -1, -2], vec![0, 1, 0, 0, 0, 0, 0, 0], vec![0, 0, 1, 0, 0, 0, 0, 0], vec![0, 0, 0, 0, 1, 1, 0, 0]];
    let t0: Vec<i64> = vec![];
    let (ok, t) = force_once(&rows, 4, &t0, 2147483647).unwrap();
    assert!(!ok);
    assert_eq!(sorted(t), vec![1]);
}

#[test]
fn case_36() {
    // rank([])
    // falsy container short-circuits to 0
    let rows: Vec<Vec<i64>> = vec![];
    assert_eq!(rank(&rows, 2147483647), Ok(0));
}

#[test]
fn case_37() {
    // rank(())
    // empty tuple is falsy too
    let rows: Vec<Vec<i64>> = vec![];
    assert_eq!(rank(&rows, 2147483647), Ok(0));
}

#[test]
fn case_38() {
    // rank([[]])
    // one empty row: not rows is False, w=0, returns 0
    let rows: Vec<Vec<i64>> = vec![vec![]];
    assert_eq!(rank(&rows, 2147483647), Ok(0));
}

#[test]
fn case_39() {
    // rank([[0,0],[0,0]])
    // all-zero rows are KEPT by rank (no nz filter) but never pivot
    let rows: Vec<Vec<i64>> = vec![vec![0, 0], vec![0, 0]];
    assert_eq!(rank(&rows, 2147483647), Ok(0));
}

#[test]
fn case_40() {
    // rank([[1,2],[2,4]])
    // dependent rows
    let rows: Vec<Vec<i64>> = vec![vec![1, 2], vec![2, 4]];
    assert_eq!(rank(&rows, 2147483647), Ok(1));
}

#[test]
fn case_41() {
    // rank([[1,2],[2,4],[0,1]])
    // rank 2 with the dependent pair first
    let rows: Vec<Vec<i64>> = vec![vec![1, 2], vec![2, 4], vec![0, 1]];
    assert_eq!(rank(&rows, 2147483647), Ok(2));
}

#[test]
fn case_42() {
    // rank([[-1,-2],[1,2]])
    // negative entries reduce onto the same line
    let rows: Vec<Vec<i64>> = vec![vec![-1, -2], vec![1, 2]];
    assert_eq!(rank(&rows, 2147483647), Ok(1));
}

#[test]
fn case_43() {
    // rank([[2147483647,4294967294],[3,0]])
    // entries congruent to 0 mod p
    let rows: Vec<Vec<i64>> = vec![vec![2147483647, 4294967294], vec![3, 0]];
    assert_eq!(rank(&rows, 2147483647), Ok(1));
}

#[test]
fn case_44() {
    // rank([[1,2,3],[1,2]])
    // w comes from rows[0]; a shorter later row raises IndexError
    let rows: Vec<Vec<i64>> = vec![vec![1, 2, 3], vec![1, 2]];
    assert_eq!(rank(&rows, 2147483647), Err(KErr::Index));
}

#[test]
fn case_45() {
    // rank([[1,2],[1,2,3]])
    // w comes from rows[0]; a longer later row is silently truncated
    let rows: Vec<Vec<i64>> = vec![vec![1, 2], vec![1, 2, 3]];
    assert_eq!(rank(&rows, 2147483647), Ok(1));
}

#[test]
fn case_46() {
    // rank([[1,0],[0,1]], 1)
    // p=1 makes every entry 0, no pivots, rank 0
    let rows: Vec<Vec<i64>> = vec![vec![1, 0], vec![0, 1]];
    assert_eq!(rank(&rows, 1), Ok(0));
}

#[test]
fn case_47() {
    // rank([[1,0]], 0)
    // p=0 raises ZeroDivisionError
    let rows: Vec<Vec<i64>> = vec![vec![1, 0]];
    assert_eq!(rank(&rows, 0), Err(KErr::ZeroDivision));
}

#[test]
fn case_48() {
    // rank([[2,2]], 2)
    // reduces to the zero row mod 2
    let rows: Vec<Vec<i64>> = vec![vec![2, 2]];
    assert_eq!(rank(&rows, 2), Ok(0));
}

#[test]
fn case_49() {
    // rank([[1,1]], 2)
    // nonzero mod 2, rank 1
    let rows: Vec<Vec<i64>> = vec![vec![1, 1]];
    assert_eq!(rank(&rows, 2), Ok(1));
}

#[test]
fn case_50() {
    // rank([[3,1],[1,3]], 4)
    // composite p with the Fermat pseudo-inverse
    let rows: Vec<Vec<i64>> = vec![vec![3, 1], vec![1, 3]];
    assert_eq!(rank(&rows, 4), Ok(2));
}

#[test]
fn case_51() {
    // rank([[True,False],[False,True]])
    // bool rows
    let rows: Vec<Vec<i64>> = vec![vec![1, 0], vec![0, 1]];
    assert_eq!(rank(&rows, 2147483647), Ok(2));
}

#[test]
fn case_52() {
    // rank([(1,2),(2,4)])
    // tuple rows
    let rows: Vec<Vec<i64>> = vec![vec![1, 2], vec![2, 4]];
    assert_eq!(rank(&rows, 2147483647), Ok(1));
}

#[test]
fn case_53() {
    // rank([[1,2,3]]*40)
    // 40 identical rows, exercises the rk>=nB break
    let rows: Vec<Vec<i64>> = vec![vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3], vec![1, 2, 3]];
    assert_eq!(rank(&rows, 2147483647), Ok(1));
}

#[test]
fn case_55() {
    // rank([[-9223372036854775808,1],[1,0]])
    // entry -2^63, the i64 boundary
    let rows: Vec<Vec<i64>> = vec![vec![i64::MIN, 1], vec![1, 0]];
    assert_eq!(rank(&rows, 2147483647), Ok(2));
}

#[test]
fn case_56() {
    // rank([[1,0,0,0,-1,0,0,0],[0,0,1,0,0,0,-1,0],[0,1,0,-1,0,0,0,0],[0,0,0,0,1,2,-1,-2],[0,1,0,0,0,0,0,0],[0,0,1,0,0,0,0,0],[0,0,0,0,1,1,0,0]])
    // the same real 7x8 build_rows matrix, full rank 7
    let rows: Vec<Vec<i64>> = vec![vec![1, 0, 0, 0, -1, 0, 0, 0], vec![0, 0, 1, 0, 0, 0, -1, 0], vec![0, 1, 0, -1, 0, 0, 0, 0], vec![0, 0, 0, 0, 1, 2, -1, -2], vec![0, 1, 0, 0, 0, 0, 0, 0], vec![0, 0, 1, 0, 0, 0, 0, 0], vec![0, 0, 0, 0, 1, 1, 0, 0]];
    assert_eq!(rank(&rows, 2147483647), Ok(7));
}

// --- hand-written: the four documented divergences and buffer reuse --------

#[test]
fn divergence_negative_p_is_value_error() {
    // Python: rank([[1,0],[0,1]], -5) == 2 (works by accident)
    assert!(matches!(
        rank(&[vec![1, 0], vec![0, 1]], -5),
        Err(KErr::Value(_))
    ));
    assert!(matches!(
        force_once(&[vec![1, -1]], 1, &[], -5),
        Err(KErr::Value(_))
    ));
}

#[test]
fn divergence_huge_p_is_value_error() {
    assert!(matches!(
        rank(&[vec![1, 0], vec![0, 1]], 1i64 << 32),
        Err(KErr::Value(_))
    ));
}

#[test]
fn divergence_huge_n_is_value_error() {
    assert!(matches!(force_once(&[], MAX_N + 1, &[], 2147483647), Err(KErr::Value(_))));
}

#[test]
fn no_state_leaks_between_moduli() {
    // The Python `_INV` memo is keyed on `a` alone, so a p=7 call poisons the
    // next p=P call and flips its answer.  The port must not.
    let rows = vec![vec![3, -3, 0, 0], vec![0, 0, 1, -1]];
    let before = force_once(&rows, 2, &[], 2147483647).unwrap();
    assert_eq!(rank(&[vec![3, 1], vec![1, 3]], 7).unwrap(), 2);
    let after = force_once(&rows, 2, &[], 2147483647).unwrap();
    assert_eq!(before, after);
    assert!(before.0);
    assert_eq!(sorted(before.1.clone()), vec![0, 1]);
}

#[test]
fn scratch_reuse_matches_fresh_scratch() {
    let mut sc = ForceScratch::new();
    let cases: Vec<(Vec<Vec<i64>>, i64, Vec<i64>)> = vec![
        (vec![vec![1, 0, 0, 0], vec![0, 1, 0, 0], vec![1, 0, -1, 0], vec![0, 1, 0, -1]], 2, vec![]),
        (vec![vec![1, -1, 0, 0]], 2, vec![5]),
        (vec![], 3, vec![9]),
        (vec![vec![1, -1, 0, 0, 0, 0], vec![0, 0, 1, -1, 0, 0], vec![0, 0, 0, 0, 1, -1]], 3, vec![]),
        (vec![vec![0, 0, 0, 0], vec![1, 0, 0, 0], vec![0, 1, 0, 0]], 2, vec![1]),
    ];
    for _ in 0..3 {
        for (rows, n, t0) in &cases {
            let a = force(rows, *n, t0, 2147483647, &mut sc);
            let b = force_once(rows, *n, t0, 2147483647);
            assert_eq!(a, b);
        }
    }
}

#[test]
fn warm_start_monotonicity() {
    // search.min_generators feeds the returned T2 straight back in.
    let rows0: Vec<Vec<i64>> = vec![vec![1, 0, 0, 0], vec![0, 1, 0, 0]];
    let mut rows = rows0.clone();
    rows.push(vec![1, 0, -1, 0]);
    rows.push(vec![0, 1, 0, -1]);
    let (_, t2) = force_once(&rows0, 2, &[], 2147483647).unwrap();
    let cold = force_once(&rows, 2, &[], 2147483647).unwrap();
    let warm = force_once(&rows, 2, &t2, 2147483647).unwrap();
    assert_eq!(sorted(cold.1), sorted(warm.1));
    assert_eq!(cold.0, warm.0);
}
