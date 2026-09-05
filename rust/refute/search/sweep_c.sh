#!/bin/bash
# Differential sweep: scan1.py (pure Python) vs kakeya-search scan, whole stdout
# modulo the "seconds" field, at --threads 1 and --threads 12.
SRC="/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/src"
B="/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/rust/target/release/kakeya-search"
R="/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/rust/refute/search"
OUT="$R/sweep"; mkdir -p "$OUT"
pass=0; fail=0
while read -r name d pool maxt target limit; do
  [ -z "$name" ] && continue
  case "$name" in \#*) continue;; esac
  ( cd "$SRC" && KAKEYA_PURE_PY=1 /usr/bin/python3 scan1.py "$name" "$d" "$pool" "$maxt" "$target" "$limit" 1000000 ) > "$OUT/$name.py.txt" 2>&1
  "$B" scan --tag "$name" --d "$d" --pool "$pool" --max-t "$maxt" --target "$target" --limit "$limit" --seed 11 --threads 1  > "$OUT/$name.rs1.txt" 2>&1
  "$B" scan --tag "$name" --d "$d" --pool "$pool" --max-t "$maxt" --target "$target" --limit "$limit" --seed 11 --threads 12 > "$OUT/$name.rs12.txt" 2>&1
  for k in py rs1 rs12; do /usr/bin/python3 "$R/norm.py" "$OUT/$name.$k.txt" > "$OUT/$name.$k.norm"; done
  if diff -q "$OUT/$name.py.norm" "$OUT/$name.rs1.norm" >/dev/null && diff -q "$OUT/$name.rs1.norm" "$OUT/$name.rs12.norm" >/dev/null; then
    echo "PASS $name  ($(grep -c . "$OUT/$name.py.norm") lines)"; pass=$((pass+1))
  else
    echo "FAIL $name"; diff "$OUT/$name.py.norm" "$OUT/$name.rs1.norm" | head -20
    diff "$OUT/$name.rs1.norm" "$OUT/$name.rs12.norm" | head -10
    fail=$((fail+1))
  fi
done < "$R/configs2.txt"
echo "SWEEP pass=$pass fail=$fail"
