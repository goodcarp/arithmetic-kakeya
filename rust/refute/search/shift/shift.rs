// Reproduces the exact expression kakeya-search uses for its vertex bitmasks.
fn mask_of(js: &[usize]) -> u64 { let mut m = 0u64; for &j in js { m |= 1u64 << j; } m }
fn main() {
    let n = 65usize;
    // common.rs combinations(n, 1): one mask per vertex
    let m0 = mask_of(&[0]);
    let m64 = mask_of(&[64]);
    println!("mask({{0}})  = {m0:#x}");
    println!("mask({{64}}) = {m64:#x}");
    println!("aliased = {}", m0 == m64);
    // search.rs min_generators: `if t0_mask & (1u64 << j) != 0 {{ continue }}`
    let t0 = m0;
    let excluded: Vec<usize> = (0..n).filter(|&j| t0 & (1u64 << j) != 0).collect();
    println!("with T0={{0}}, vertices excluded from `cand`: {excluded:?}");
}
