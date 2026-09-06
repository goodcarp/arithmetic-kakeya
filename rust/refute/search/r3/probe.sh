#!/bin/bash
# probe <id> <d> <pool> <maxt> <target> <limit|-> [seed]
K="/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya"
B="$K/rust/target/release/kakeya-search"
R="$K/rust/refute/search/r3"; O="$R/out"
id=$1; d=$2; pl=$3; mt=$4; tg=$5; lim=$6; seed=${7:-11}
( cd "$K/src" && KAKEYA_PURE_PY=1 /usr/bin/python3 scan1.py "$id" "$d" "$pl" "$mt" "$tg" "$lim" 1000000 ) > "$O/$id.py.txt" 2>&1; echo "EXIT=$?" >> "$O/$id.py.txt"
LA=(); [ "$lim" != "-" ] && LA=(--limit "$lim" --seed "$seed")
"$B" scan --tag "$id" --d "$d" --pool "$pl" --max-t "$mt" --target "$tg" "${LA[@]}" --threads 1  > "$O/$id.rs1.txt" 2>&1; echo "EXIT=$?" >> "$O/$id.rs1.txt"
"$B" scan --tag "$id" --d "$d" --pool "$pl" --max-t "$mt" --target "$tg" "${LA[@]}" --threads 12 > "$O/$id.rs12.txt" 2>&1; echo "EXIT=$?" >> "$O/$id.rs12.txt"
"$R/compare.sh" "$id"
