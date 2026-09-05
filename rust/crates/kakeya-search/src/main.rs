//! `kakeya-search` -- the arithmetic-Kakeya drivers in Rust.
//!
//! Subcommands: `scan` (search.scan_dims / scan1.py), `g2-tall`, `cycles8`,
//! `stacked`, `rzero`, and `check` (the cheap fixture gate).
//!
//! Every subcommand prints exactly what its Python original prints, so logs
//! diff cleanly modulo the `seconds` field.  Parallelism is over the outermost
//! enumeration only, and results are merged by enumeration index, so output is
//! byte-identical for any `--threads`.

use std::collections::HashMap;
use std::process::ExitCode;

use kakeya_search::frac::Frac;
use kakeya_search::graph::{pool_by_size, Label};
use kakeya_search::{check, drivers};

const USAGE: &str = "\
usage: kakeya-search <subcommand> [options]

  scan     --tag T --d 2x2 --pool 6 --max-t 1 --target 7/4
           [--limit N] [--seed 11] [--tlimit S] [--threads N] [--quiet]
  g2-tall  [--rows 4,5,6] [--max-t 1] [--tlimit S] [--threads N]
  cycles8  [--pool 6] [--target 67/40] [--deg 2] [--tlimit S] [--threads N]
  stacked  [--pool 4,6] [--max-t 2] [--target 7/4] [--tlimit S] [--threads N]
  rzero    [--d 2x2 --pool 6 [--limit N] [--seed 0]] [--tlimit S] [--threads N]
  check    [--threads N]

--tlimit is the Python drivers' wall-clock cap; omit it to run to completion.
--threads defaults to the machine's parallelism; output does not depend on it.
";

struct Args {
    sub: String,
    opts: HashMap<String, String>,
    flags: Vec<String>,
}

fn parse_args() -> Result<Args, String> {
    let mut it = std::env::args().skip(1);
    let sub = it.next().ok_or_else(|| USAGE.to_string())?;
    let mut opts = HashMap::new();
    let mut flags = Vec::new();
    let rest: Vec<String> = it.collect();
    let mut i = 0;
    while i < rest.len() {
        let a = &rest[i];
        if let Some(name) = a.strip_prefix("--") {
            if name == "quiet" {
                flags.push(name.to_string());
                i += 1;
                continue;
            }
            let v = rest
                .get(i + 1)
                .ok_or_else(|| format!("option --{name} needs a value"))?;
            opts.insert(name.to_string(), v.clone());
            i += 2;
        } else {
            return Err(format!("unexpected argument {a:?}\n{USAGE}"));
        }
    }
    Ok(Args { sub, opts, flags })
}

impl Args {
    fn get(&self, k: &str) -> Option<&str> {
        self.opts.get(k).map(|s| s.as_str())
    }
    fn req(&self, k: &str) -> Result<&str, String> {
        self.get(k).ok_or_else(|| format!("missing --{k}"))
    }
    fn has_flag(&self, k: &str) -> bool {
        self.flags.iter().any(|f| f == k)
    }
    fn usize_or(&self, k: &str, dflt: usize) -> Result<usize, String> {
        match self.get(k) {
            None => Ok(dflt),
            Some(v) => v.parse().map_err(|e| format!("bad --{k} {v:?}: {e}")),
        }
    }
    fn u64_or(&self, k: &str, dflt: u64) -> Result<u64, String> {
        match self.get(k) {
            None => Ok(dflt),
            Some(v) => v.parse().map_err(|e| format!("bad --{k} {v:?}: {e}")),
        }
    }
    fn tlimit(&self) -> Result<Option<f64>, String> {
        match self.get("tlimit") {
            None | Some("-") | Some("none") => Ok(None),
            Some(v) => v
                .parse::<f64>()
                .map(Some)
                .map_err(|e| format!("bad --tlimit {v:?}: {e}")),
        }
    }
    fn limit(&self) -> Result<Option<usize>, String> {
        match self.get("limit") {
            None | Some("-") | Some("none") => Ok(None),
            Some(v) => v
                .parse::<usize>()
                .map(Some)
                .map_err(|e| format!("bad --limit {v:?}: {e}")),
        }
    }
    fn threads(&self) -> Result<usize, String> {
        match self.get("threads") {
            None => Ok(std::thread::available_parallelism().map_or(1, |p| p.get())),
            Some(v) => {
                let n: usize = v.parse().map_err(|e| format!("bad --threads {v:?}: {e}"))?;
                if n == 0 {
                    Ok(std::thread::available_parallelism().map_or(1, |p| p.get()))
                } else {
                    Ok(n)
                }
            }
        }
    }
}

fn parse_dims(s: &str) -> Result<Vec<usize>, String> {
    s.split('x')
        .map(|p| {
            p.parse::<usize>()
                .map_err(|e| format!("bad dims {s:?}: {e}"))
        })
        .collect()
}

fn parse_pool(s: &str) -> Result<Vec<Label>, String> {
    let k: usize = s.parse().map_err(|e| format!("bad pool {s:?}: {e}"))?;
    pool_by_size(k)
        .map(|p| p.to_vec())
        .ok_or_else(|| format!("no POOL{k} (have 3, 4, 5, 6, 8)"))
}

fn run() -> Result<i32, String> {
    let args = parse_args()?;
    let threads = args.threads()?;
    match args.sub.as_str() {
        "scan" => {
            let cfg = drivers::scan::ScanCfg {
                tag: args.req("tag")?.to_string(),
                d: parse_dims(args.req("d")?)?,
                pool: parse_pool(args.req("pool")?)?,
                max_t: args.usize_or("max-t", 0)?,
                target: Frac::parse(args.req("target")?)?,
                limit: args.limit()?,
                seed: args.u64_or("seed", 11)?,
                tlimit: args.tlimit()?,
                threads,
                verbose: !args.has_flag("quiet"),
            };
            let r = drivers::scan::run(&cfg);
            drivers::scan::emit(&cfg, &r);
            Ok(0)
        }
        "g2-tall" => {
            let rows: Vec<usize> = match args.get("rows") {
                None => vec![4, 5, 6],
                Some(v) => v
                    .split(',')
                    .map(|p| p.parse::<usize>().map_err(|e| format!("bad --rows: {e}")))
                    .collect::<Result<_, _>>()?,
            };
            for r_ in rows {
                let cfg = drivers::g2_tall::TallCfg {
                    rows: r_,
                    max_t: args.usize_or("max-t", 1)?,
                    tlimit: args.tlimit()?,
                    threads,
                    verbose: !args.has_flag("quiet"),
                };
                let r = drivers::g2_tall::run(&cfg);
                drivers::g2_tall::emit(&cfg, &r);
            }
            Ok(0)
        }
        "cycles8" => {
            let cfg = drivers::cycles8::CyclesCfg {
                pool: parse_pool(args.get("pool").unwrap_or("6"))?,
                target: Frac::parse(args.get("target").unwrap_or("67/40"))?,
                deg: args.usize_or("deg", 2)?,
                tlimit: args.tlimit()?,
                threads,
                verbose: !args.has_flag("quiet"),
            };
            let r = drivers::cycles8::run(&cfg);
            drivers::cycles8::emit(&cfg, &r);
            Ok(0)
        }
        "stacked" => {
            let pools: Vec<usize> = match args.get("pool") {
                None => vec![4, 6],
                Some(v) => v
                    .split(',')
                    .map(|p| p.parse::<usize>().map_err(|e| format!("bad --pool: {e}")))
                    .collect::<Result<_, _>>()?,
            };
            let mut code = 0;
            for k in pools {
                let cfg = drivers::stacked::StackedCfg {
                    name: format!("POOL{k}"),
                    pool: parse_pool(&k.to_string())?,
                    max_t: args.usize_or("max-t", 2)?,
                    target: Frac::parse(args.get("target").unwrap_or("7/4"))?,
                    tlimit: args.tlimit()?,
                    threads,
                };
                let r = drivers::stacked::run(&cfg);
                if !drivers::stacked::emit(&cfg, &r) {
                    code = 1;
                }
            }
            Ok(code)
        }
        "rzero" => {
            let tlimit = args.tlimit()?;
            let jobs: Vec<(Vec<usize>, usize, Option<usize>)> = match args.get("d") {
                Some(d) => vec![(
                    parse_dims(d)?,
                    args.req("pool")?
                        .parse()
                        .map_err(|e| format!("bad --pool: {e}"))?,
                    args.limit()?,
                )],
                None => vec![
                    (vec![2, 2], 6, None),
                    (vec![2, 2, 2], 4, None),
                    (vec![2, 3], 4, None),
                    (vec![3, 2], 4, None),
                    (vec![2, 2, 2], 6, Some(60000)),
                    (vec![2, 2, 2, 2], 4, Some(60000)),
                ],
            };
            for (d, pk, lim) in jobs {
                let cfg = drivers::rzero::RzeroCfg {
                    d,
                    pool: parse_pool(&pk.to_string())?,
                    limit: lim,
                    seed: args.u64_or("seed", 0)?,
                    tlimit,
                    threads,
                    verbose: !args.has_flag("quiet"),
                };
                let r = drivers::rzero::run(&cfg);
                drivers::rzero::emit(&cfg, &r);
            }
            Ok(0)
        }
        "check" => {
            let (lines, failed) = check::run(threads);
            for l in &lines {
                println!("{l}");
            }
            println!(
                "CHECK {} ({} failed)",
                if failed == 0 { "PASS" } else { "FAIL" },
                failed
            );
            Ok(if failed == 0 { 0 } else { 1 })
        }
        "help" | "--help" | "-h" => {
            print!("{USAGE}");
            Ok(0)
        }
        other => Err(format!("unknown subcommand {other:?}\n{USAGE}")),
    }
}

fn main() -> ExitCode {
    match run() {
        Ok(0) => ExitCode::SUCCESS,
        Ok(_) => ExitCode::FAILURE,
        Err(e) => {
            eprintln!("kakeya-search: {e}");
            ExitCode::FAILURE
        }
    }
}
