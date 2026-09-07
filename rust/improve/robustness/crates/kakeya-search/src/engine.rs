//! Outer-loop parallelism with sequential-Python output.
//!
//! Every outer iteration carries its enumeration index.  Work is handed to
//! rayon in contiguous index chunks; results are merged strictly in index
//! order, and a score only counts as an improvement (and only then prints its
//! progress line) when it beats the *global* running minimum -- which is
//! exactly `if best is None or sc < best` in sequential order.  Ties therefore
//! go to the lowest enumeration index, whatever the thread count.
//!
//! Per chunk we keep only the chunk-local running-minimum improvements.  That
//! is lossless: the global running minimum is always <= the chunk-local one at
//! the same point, so anything the chunk filter drops could never have been a
//! global improvement either.

use std::collections::BTreeMap;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::Mutex;
use std::time::Instant;

use rayon::prelude::*;

use crate::frac::Frac;
use crate::graph::Label;

#[derive(Clone, Debug, Default)]
pub struct Witness {
    pub labels: Vec<Label>,
    pub m: i64,
    pub gens: Vec<(usize, Label)>,
    pub t0: Vec<usize>,
    pub t: usize,
}

#[derive(Clone, Debug)]
pub struct Improvement {
    pub index: u64,
    pub sc: Frac,
    /// Progress line to print when this improves the global running minimum.
    pub line: Option<String>,
    pub witness: Option<Witness>,
}

#[derive(Clone, Debug)]
pub struct HitRec {
    pub index: u64,
    /// Printed immediately, in enumeration order (`scan_dims`' HIT lines).
    pub progress: Option<String>,
    /// Printed after the RESULT line (HITOBJ / stacked's tail).
    pub obj: Option<String>,
}

#[derive(Default)]
pub struct ChunkOut {
    pub improvements: Vec<Improvement>,
    pub hits: Vec<HitRec>,
    /// `(enumeration index, count)` for drivers with a `tested` counter.
    pub tested: Vec<(u64, u64)>,
}

/// Shared deadline.  `should_stop` mirrors the Python check exactly: the item
/// that trips it is counted but not processed.
pub struct Stop {
    t0: Instant,
    tlimit: Option<f64>,
    stopped: AtomicBool,
    min_skipped: AtomicU64,
}

impl Stop {
    pub fn new(t0: Instant, tlimit: Option<f64>) -> Stop {
        Stop {
            t0,
            tlimit,
            stopped: AtomicBool::new(false),
            min_skipped: AtomicU64::new(u64::MAX),
        }
    }

    pub fn should_stop(&self, index: u64) -> bool {
        let lim = match self.tlimit {
            None => return false,
            Some(l) => l,
        };
        if !self.stopped.load(Ordering::Relaxed) {
            if self.t0.elapsed().as_secs_f64() <= lim {
                return false;
            }
            self.stopped.store(true, Ordering::Relaxed);
        }
        self.min_skipped.fetch_min(index, Ordering::Relaxed);
        true
    }

    pub fn tripped(&self) -> bool {
        self.tlimit.is_some() && self.stopped.load(Ordering::Relaxed)
    }

    pub fn first_skipped(&self) -> u64 {
        self.min_skipped.load(Ordering::Relaxed)
    }
}

#[derive(Default)]
pub struct Merged {
    pub best: Option<Frac>,
    pub bestobj: Option<Witness>,
    pub hits: Vec<HitRec>,
    pub tested: u64,
}

impl Merged {
    fn absorb(&mut self, c: &ChunkOut, stop_at: u64, print_improvements: bool, print_hits: bool) {
        for imp in &c.improvements {
            if imp.index >= stop_at {
                break;
            }
            if self.best.is_none() || imp.sc < self.best.expect("checked") {
                self.best = Some(imp.sc);
                if imp.witness.is_some() {
                    self.bestobj = imp.witness.clone();
                }
                if print_improvements {
                    if let Some(l) = &imp.line {
                        println!("{l}");
                    }
                }
            }
        }
        for h in &c.hits {
            if h.index >= stop_at {
                break;
            }
            if print_hits {
                if let Some(l) = &h.progress {
                    println!("{l}");
                }
            }
            self.hits.push(h.clone());
        }
        for &(i, k) in &c.tested {
            if i >= stop_at {
                break;
            }
            self.tested += k;
        }
    }
}

pub struct RunOpts {
    pub total: u64,
    pub tlimit: Option<f64>,
    pub threads: usize,
    pub print_improvements: bool,
    pub print_hits: bool,
}

pub struct RunOut {
    pub merged: Merged,
    /// Python's `count`: the number of outer items consumed, including the one
    /// that tripped the deadline.
    pub scanned: u64,
    pub stopped: bool,
    pub elapsed: f64,
}

/// Chunk size: enough chunks to keep every thread fed, small enough that the
/// deadline is honoured promptly and per-chunk buffers stay tiny.
fn chunk_size(total: u64, threads: usize) -> u64 {
    let want = (total / (threads.max(1) as u64 * 64)).max(1);
    want.min(4096)
}

/// Run `chunk_fn` over `0..total` in parallel and merge in enumeration order.
pub fn run<F>(opts: &RunOpts, t0: Instant, chunk_fn: F) -> RunOut
where
    F: Fn(u64, u64, &Stop) -> ChunkOut + Sync + Send,
{
    let stop = Stop::new(t0, opts.tlimit);
    let cs = chunk_size(opts.total, opts.threads);
    let nchunks = opts.total.div_ceil(cs).max(1);

    let pool = rayon::ThreadPoolBuilder::new()
        .num_threads(opts.threads)
        .build()
        .expect("thread pool");

    // Set by the deadline path to the smallest enumeration index that was
    // never processed; `u64::MAX` when no deadline tripped.
    let mut cut_out: u64 = u64::MAX;
    let merged = if opts.tlimit.is_none() {
        // No deadline: nothing can be retracted, so flush in order as we go.
        let state: Mutex<(u64, BTreeMap<u64, ChunkOut>, Merged)> =
            Mutex::new((0, BTreeMap::new(), Merged::default()));
        pool.install(|| {
            (0..nchunks).into_par_iter().for_each(|ci| {
                let start = ci * cs;
                let end = ((ci + 1) * cs).min(opts.total);
                let out = chunk_fn(start, end, &stop);
                let mut st = state.lock().expect("merger lock");
                st.1.insert(ci, out);
                loop {
                    let next = st.0;
                    let c = match st.1.remove(&next) {
                        None => break,
                        Some(c) => c,
                    };
                    st.2
                        .absorb(&c, u64::MAX, opts.print_improvements, opts.print_hits);
                    st.0 += 1;
                }
            });
        });
        state.into_inner().expect("merger lock").2
    } else {
        // Deadline path, streaming.  Chunks are dispatched in strictly
        // increasing order, `wave` chunks at a time, and each wave is absorbed
        // as soon as it joins.  Nothing proportional to the index space is ever
        // allocated, and no chunk past the deadline is ever visited -- so
        // `--tlimit` is a real wall-clock bound and a huge index space returns
        // a RESULT instead of aborting on the chunk vector.
        //
        // Ordering and tie-breaks are unchanged.  The cut-off `stop_at` is the
        // smallest enumeration index that was never processed.  A wave that
        // joins with `stop.tripped()` still false skipped nothing, so every one
        // of its indices is strictly below any future cut-off and can be
        // absorbed (and printed) immediately -- that is why the old
        // buffer-everything-until-the-end step is not needed for those waves.
        // The wave in which the deadline trips is absorbed against
        // `min(stop.first_skipped(), frontier)`, where `frontier` is the first
        // index of the first chunk we then decline to dispatch: every chunk we
        // did dispatch is visited (rayon runs the whole wave), so a skipped
        // chunk records its own start index exactly as before, and the chunks
        // we never dispatch all start at or after `frontier`.  That min is
        // therefore the same number the eager version computed.
        let mut m = Merged::default();
        let mut ci: u64 = 0;
        let mut cut: u64 = u64::MAX;
        let threads = opts.threads.max(1) as u64;
        let mut wave: u64 = threads * 4;
        let max_wave: u64 = threads * 256;
        while ci < nchunks {
            let hi = ci.saturating_add(wave).min(nchunks);
            let outs: Vec<ChunkOut> = pool.install(|| {
                (ci..hi)
                    .into_par_iter()
                    .map(|c| {
                        let start = c * cs;
                        let end = ((c + 1) * cs).min(opts.total);
                        chunk_fn(start, end, &stop)
                    })
                    .collect()
            });
            ci = hi;
            if stop.tripped() {
                let frontier = ci.saturating_mul(cs).min(opts.total);
                cut = stop.first_skipped().min(frontier);
                for c in &outs {
                    m.absorb(c, cut, opts.print_improvements, opts.print_hits);
                }
                break;
            }
            for c in &outs {
                m.absorb(c, u64::MAX, opts.print_improvements, opts.print_hits);
            }
            wave = wave.saturating_mul(2).min(max_wave);
        }
        cut_out = cut;
        m
    };

    let stopped = stop.tripped();
    let scanned = if stopped {
        cut_out
            .min(stop.first_skipped())
            .saturating_add(1)
            .min(opts.total)
    } else {
        opts.total
    };
    RunOut {
        merged,
        scanned,
        stopped,
        elapsed: t0.elapsed().as_secs_f64(),
    }
}
