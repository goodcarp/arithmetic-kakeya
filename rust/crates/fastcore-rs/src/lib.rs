//! PyO3 boundary for the bit-exact `fastcore` kernel.
//!
//! Exposes `force(rows, n, T0, p=2147483647) -> (bool, set)` and
//! `rank(rows, p=2147483647) -> int` with the argument tolerance the S1
//! contract found at the call sites: any sequence of sequences for `rows`,
//! any iterable for `T0`, `bool` accepted anywhere an `int` is.
#![allow(non_snake_case)]

use std::cell::RefCell;

use kakeya_core::{self as core, ForceScratch, KErr};
use pyo3::exceptions::{PyIndexError, PyValueError, PyZeroDivisionError};
use pyo3::prelude::*;
use pyo3::types::{PyAnyMethods, PyList, PySet, PyTuple};

fn map_err(e: KErr) -> PyErr {
    match e {
        KErr::Index => PyIndexError::new_err("list index out of range"),
        KErr::ZeroDivision => {
            PyZeroDivisionError::new_err("integer division or modulo by zero")
        }
        KErr::Value(m) => PyValueError::new_err(m),
    }
}

/// Per-thread reusable buffers: `force` is called once per DFS node, so the
/// boundary must not allocate a fresh row matrix on every call.
struct Buffers {
    rows: Vec<Vec<i64>>,
    t0: Vec<i64>,
    scratch: ForceScratch,
}

thread_local! {
    static BUFS: RefCell<Buffers> = RefCell::new(Buffers {
        rows: Vec::new(),
        t0: Vec::new(),
        scratch: ForceScratch::new(),
    });
}

#[inline]
fn extract_i64(o: &Bound<'_, PyAny>) -> PyResult<i64> {
    // `bool` subclasses `int`, so this accepts True/False the way Python does.
    o.extract::<i64>()
}

/// Fill `row` from any Python sequence/iterable of ints.
fn fill_row(item: &Bound<'_, PyAny>, row: &mut Vec<i64>) -> PyResult<()> {
    row.clear();
    if let Ok(l) = item.cast::<PyList>() {
        row.reserve(l.len());
        for e in l.iter() {
            row.push(extract_i64(&e)?);
        }
    } else if let Ok(t) = item.cast::<PyTuple>() {
        row.reserve(t.len());
        for e in t.iter() {
            row.push(extract_i64(&e)?);
        }
    } else {
        for e in item.try_iter()? {
            row.push(extract_i64(&e?)?);
        }
    }
    Ok(())
}

/// Materialise `rows` into `buf` (reusing its inner allocations) and return the
/// row count.  Only `buf[..count]` is meaningful afterwards.
///
/// Mirrors `for r in rows: ... r[2*j]`: any iterable of iterables works.
/// Entries outside `i64` raise `OverflowError` and non-integers raise
/// `TypeError` (documented divergences; every driver entry is in -3..3).
fn extract_rows_into(rows: &Bound<'_, PyAny>, buf: &mut Vec<Vec<i64>>) -> PyResult<usize> {
    let mut count = 0usize;
    {
        let mut take = |item: Bound<'_, PyAny>, buf: &mut Vec<Vec<i64>>| -> PyResult<()> {
            if count == buf.len() {
                buf.push(Vec::new());
            }
            fill_row(&item, &mut buf[count])?;
            count += 1;
            Ok(())
        };
        if let Ok(l) = rows.cast::<PyList>() {
            for item in l.iter() {
                take(item, buf)?;
            }
        } else if let Ok(t) = rows.cast::<PyTuple>() {
            for item in t.iter() {
                take(item, buf)?;
            }
        } else {
            for item in rows.try_iter()? {
                take(item?, buf)?;
            }
        }
    }
    Ok(count)
}

fn extract_ints_into(it: &Bound<'_, PyAny>, buf: &mut Vec<i64>) -> PyResult<()> {
    buf.clear();
    for e in it.try_iter()? {
        buf.push(extract_i64(&e?)?);
    }
    Ok(())
}

#[pyfunction]
#[pyo3(signature = (rows, n, T0, p = 2147483647))]
fn force<'py>(
    py: Python<'py>,
    rows: &Bound<'py, PyAny>,
    n: i64,
    T0: &Bound<'py, PyAny>,
    p: i64,
) -> PyResult<(bool, Bound<'py, PySet>)> {
    let res = BUFS.with(|b| -> Option<PyResult<(bool, Vec<i64>)>> {
        // A Python-level iterable could re-enter; fall back if it does.
        let mut b = b.try_borrow_mut().ok()?;
        let b = &mut *b;
        let nrows = match extract_rows_into(rows, &mut b.rows) {
            Ok(k) => k,
            Err(e) => return Some(Err(e)),
        };
        if let Err(e) = extract_ints_into(T0, &mut b.t0) {
            return Some(Err(e));
        }
        let Buffers { rows, t0, scratch } = b;
        let out = py.detach(|| core::force(&rows[..nrows], n, t0, p, scratch));
        Some(out.map_err(map_err))
    });
    let (ok, t) = match res {
        Some(r) => r?,
        None => {
            let mut rows_v: Vec<Vec<i64>> = Vec::new();
            let nrows = extract_rows_into(rows, &mut rows_v)?;
            let mut t0_v: Vec<i64> = Vec::new();
            extract_ints_into(T0, &mut t0_v)?;
            py.detach(|| core::force_once(&rows_v[..nrows], n, &t0_v, p))
                .map_err(map_err)?
        }
    };
    // A fresh set object every call: callers hand the same T2 to many siblings.
    let set = PySet::new(py, t.iter())?;
    Ok((ok, set))
}

#[pyfunction]
#[pyo3(signature = (rows, p = 2147483647))]
fn rank(py: Python<'_>, rows: &Bound<'_, PyAny>, p: i64) -> PyResult<i64> {
    // `if not rows: return 0` -- Python container truthiness, before anything
    // else is looked at.
    if !rows.is_truthy()? {
        return Ok(0);
    }
    let res = BUFS.with(|b| -> Option<PyResult<i64>> {
        let mut b = b.try_borrow_mut().ok()?;
        let b = &mut *b;
        let nrows = match extract_rows_into(rows, &mut b.rows) {
            Ok(k) => k,
            Err(e) => return Some(Err(e)),
        };
        let rows_ref: &[Vec<i64>] = &b.rows[..nrows];
        let out = py.detach(|| core::rank(rows_ref, p));
        Some(out.map_err(map_err))
    });
    match res {
        Some(r) => r,
        None => {
            let mut rows_v: Vec<Vec<i64>> = Vec::new();
            let nrows = extract_rows_into(rows, &mut rows_v)?;
            py.detach(|| core::rank(&rows_v[..nrows], p)).map_err(map_err)
        }
    }
}

#[pymodule]
fn fastcore_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("P", (1i64 << 31) - 1)?;
    m.add_function(wrap_pyfunction!(force, m)?)?;
    m.add_function(wrap_pyfunction!(rank, m)?)?;
    Ok(())
}
