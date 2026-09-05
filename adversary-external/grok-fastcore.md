  » order                          
  ⇢ route           grok-cli       — kind=code; ranked 1 ready; chose grok-cli (cost_class 1)
  → invoke          grok-cli       
  ▣ deposit         grok-cli       (2112 chars, 332.461s, sha b229cf0126)

────────────────────────────────────────────────────────────────────────
negative entries and Python %: rank([[-1]]) -> 1
(-1)%P == 2147483646, not -1. force([[-1, 1]], 1, []) -> (True, {0})

non-prime p: rank([[2]], 4) -> 1
Fermat “inverse” pow(2,2,4)==0 zeros the row and still counts a pivot. force([[2, 2]], 1, [], 4) -> (False, set())

inverse of zero via pow(a,p-2,p): rank([[2]], 4) -> 1
_inv(2)=pow(2,2,4)==0; row becomes [0], rk still 1. (pow(0,P-2,P)==0 if 0 were inverted.) _INV keys only on a, not p: after that call, force([[2, 0], [0, 2]], 1, []) -> (False, set()); on a fresh interpreter it is (True, {0}).

overflow of a*b near 2^62: rank([[1, 2147483646], [2147483646, 2147483646]]) -> 2
elim does (a - fac*b)%P with fac=b=2147483646, product 4611686014132420608; Python bigint then % (Rust i32/wrapping or signed % differ).

entries >= p: rank([[2147483647]]) -> 0
P%P==0, no pivot. rank([[2147483648]]) -> 1. force([[2147483647, 2147483647]], 1, []) -> (False, set())

pivot and found-vertex scan order: rank([[2, 1], [0, 2]], 4) -> 2
cols left-to-right, first i>=rk with B[i][c] truthy (right-to-left cols give 1). force([[0, 0, 1, -1]], 2, []) -> (False, {1})
U = [j for j in range(n) if j not in T]; first j whose reduced (1,P-1) is zero.

T0 out-of-range or duplicates: force([[1, -1]], 1, [2, 2]) -> (True, {2})
set(T0) drops dups; while len(T)<n is skipped, so junk indices can “succeed”. force([], 2, [0, 0, 7]) -> (True, {0, 7}). force([[1, -1]], 1, [-1]) -> (True, {-1})

empty / all-zero / ragged rows: rank([]) -> 0
rank([[0, 0], [0, 0]]) -> 0 (zeros never pivot). rank([[]]) -> 0. force([], 0, []) -> (True, set()). force([[0, 0]], 1, []) -> (False, set()) (nz rows dropped). rank([[1, 2], [3]]) raises IndexError (w=len(B[0]), later short row). force([[1]], 1, []) raises IndexError on r[1].

mutation of inputs: force([[1, -1]], 1, s) with s=set() -> (True, {0}), and s is still set()
T=set(T0) is a new set; rows are only read (rank copies via x%p). Returned T is never T0.

return types: force([[1, -1]], 1, [0]) -> (True, {0})
tuple of bool and set (not list/frozenset; T0 list is converted). rank([]) -> 0 (Python int). rank([[1, 1], [1, 1]]) -> 1.
────────────────────────────────────────────────────────────────────────
  1 deposit(s) · 0 molt(s) · 332.8s · verify: ✔ · head 62442e34a96a
EXIT=0
