#!/bin/bash
# Fill the two UNSUPPORTED coverage-map rows at SAMPLED scope (critic item): pure-Python scan1.py vs the audited binary, seed 11 both sides.
K="/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya"; B="$K/rust/target/release/kakeya-search"; O="$K/rust/refute/search/r6-fill"
mask(){ sed -E 's/"seconds": [0-9.]+/"seconds": SEC/; s/\[[0-9.]+s\]/[Ns]/g'; }
run(){ id=$1; d=$2; pl=$3; mt=$4; tg=$5; lim=$6
  echo "== $id: d=$d pool=$pl max_t=$mt target=$tg limit=$lim seed=11  $(date -u +%H:%M:%SZ)"
  ( cd "$K/src" && KAKEYA_PURE_PY=1 /usr/bin/python3 -c "import fastcore; assert fastcore.force is fastcore._force_py" && KAKEYA_PURE_PY=1 /usr/bin/python3 scan1.py "$id" "$d" "$pl" "$mt" "$tg" "$lim" 1000000 ) > "$O/$id.py.txt" 2>&1; echo "EXIT=$?" >> "$O/$id.py.txt"
  "$B" scan --tag "$id" --d "$d" --pool "$pl" --max-t "$mt" --target "$tg" --limit "$lim" --seed 11 --threads 2 > "$O/$id.rs2.txt" 2>&1; echo "EXIT=$?" >> "$O/$id.rs2.txt"
  mask < "$O/$id.py.txt" > "$O/$id.py.norm"; mask < "$O/$id.rs2.txt" > "$O/$id.rs2.norm"
  if diff -q "$O/$id.py.norm" "$O/$id.rs2.norm" >/dev/null; then echo "   IDENTICAL ($(wc -l < "$O/$id.py.norm" | tr -d ' ') lines, $(grep -c '^HIT ' "$O/$id.py.txt") HIT)"; else echo "   DIFFER:"; diff "$O/$id.py.norm" "$O/$id.rs2.norm" | head -10; fi
  echo "   $(date -u +%H:%M:%SZ)"
}
echo "kernel switch check: $(cd "$K/src" && KAKEYA_PURE_PY=1 /usr/bin/python3 -c 'import fastcore; print(fastcore.force is fastcore._force_py)')"
echo "configs2.txt 2x2x2 lines: $(grep -E '2x2x2' "$K/rust/refute/search/configs2.txt" "$K/rust/refute/search/configs.txt" | head -3 | tr '\n' ';')"
run c12s 6 6 1 2 2000          # the --d 6 row's config (c12: 6 6 1 2 -) at --limit 2000
run s18s 2x2x2 4 1 7/4 2000    # the --d 2x2x2 row, sampled
echo "DONE $(date -u +%H:%M:%SZ)"
