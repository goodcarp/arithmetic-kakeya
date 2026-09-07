//! The arithmetic-Kakeya search drivers, in Rust.
//!
//! `kakeya-core` supplies the bit-exact `force`/`rank` kernel; this crate adds
//! everything the Python drivers need from `kakeya.py` and `search.py`, plus
//! outer-loop parallelism whose output does not depend on the thread count.

pub mod check;
pub mod common;
pub mod drivers;
pub mod engine;
pub mod fmt;
pub mod frac;
pub mod graph;
pub mod pyrandom;
pub mod search;

#[cfg(test)]
mod tests;
