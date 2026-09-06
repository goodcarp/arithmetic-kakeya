#!/bin/bash
K="/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya"
R="$K/rust/refute/search/r3"; O="$R/out"; B="$K/rust/target/release/kakeya-search"
id=$1; d=$2; pl=$3; lim=$4; seed=$5
( cd "$K/src" && KAKEYA_PURE_PY=1 /usr/bin/python3 "$K/rust/refute/search/rzero_one.py" "$d" "$pl" "$lim" "$seed" 1000000000 ) > "$O/$id.py.txt" 2>&1; echo "EXIT=$?" >> "$O/$id.py.txt"
LA=(); [ "$lim" != "-" ] && LA=(--limit "$lim")
for T in 1 12; do
  "$B" rzero --d "$d" --pool "$pl" "${LA[@]}" --seed "$seed" --threads $T > "$O/$id.rs$T.txt" 2>&1; echo "EXIT=$?" >> "$O/$id.rs$T.txt"
done
"$R/compare.sh" "$id"
