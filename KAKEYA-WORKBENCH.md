# Arithmetic Kakeya — workbench

Seat: rebuild-the-objects (prerequisite pass, no search mandate).
Date: 2026-08-24. Folder: `~/Desktop/FrontierMath Open Problems/arithmetic-kakeya/`.

**Seat result.** The formalism is implemented and unit-tested; **both** published
Katz–Tao objects are rebuilt and certified in exact rational arithmetic — the `7/4`
trapezoid (Goal 1's starting point) and the `11/6` configuration (the sums-differences
record, Goal 2) — each matching Epoch's own figure vertex for vertex, with the engine
independently forcing the same vertex first as the published hand derivation. Along the
way: the record `1.675...` is shown to be a *limit* that no finite object attains, so the
Epoch target lies strictly outside the published family; and ten structure lemmas
(Lemma 1, P1–P9, Theorem 2) are proved, four of them new and one of them a 6x search reduction.
Everything below is either machine-checked or a citation.

---

## 0. One-paragraph orientation

The Epoch problem asks for a single finite combinatorial object whose *score*
— an exact rational number — is at most 1.675. The score of an object is a
provable upper bound for the arithmetic Kakeya exponent. The published record is
`gamma = 1.6751309...`, the largest root of `x^3 - 4x + 2`. **`gamma` is a limit,
not the score of any object**: it is the fixed point of an iteration whose finite
stages have scores `2, 7/4, 171/101, 101863/60652, ...`, decreasing to `gamma`
strictly from above. The Epoch target `1.675` sits `1.31e-4` *below* that limit.
So the problem is not "go one rung deeper on the published ladder" — no rung ever
gets there. It asks for an object outside the published family.

---

## 1. The formalism (the "Verifiable Set-up", restated in working terms)

**Slopes.** `X` is a finite subset of `Z^2` with `(0,0) in X`, and `a+b != 0` for
every other `(a,b) in X`. Read `(a,b)` as the projection `pi_r(g_1,g_2) = a g_1 + b g_2`,
i.e. as the slope `r = b/a` on the projective line (`(0,1)` is `r = infinity`).
The condition `a+b != 0` says: the target slope `tau = (1,-1)` (i.e. `r = -1`, the
difference map) is never itself a label. `X` costs nothing — it does not enter the
score — so the only real choice is *which slopes get used*.

**The graph.** An `X`-constructible graph is a box `d_1 x ... x d_k` of vertices
`e = (e_1,...,e_k)`, `1 <= e_i <= d_i`, together with label functions
`f_i : d_1 x ... x d_{i-1} x (d_i - 1) -> X`. The bundle `f_i(a_1..a_i) = x` puts
an edge labelled `x` between `(a_1..a_i, c)` and `(a_1..a_i + 1, c)` for **every
common suffix** `c` in `d_{i+1} x ... x d_k`. Hence
```
n(G) = d_1 ... d_k          m(G) = sum_i sum_{e in dom f_i} [f_i(e) != 0] * d_{i+1}...d_k
```
Reading of the levels: coordinate `k` is the *outermost*, i.e. the most recent
gluing stage; `f_i` depends on the inner coordinates `e_1..e_{i-1}` (which vertex of
the graph built so far) and on `e_i` (which pair of consecutive copies), and is
constant in the outer coordinates — that is exactly why a level-`i` bundle carries
`d_{i+1}...d_k` edges. This is the iterative definition ("take `d_i` copies of `H`,
glue a chosen subset of vertices with chosen labels") written in coordinates.

*Ambiguity flagged.* Operation 1 in the problem text says only that `e_1` and `e_2`
agree in their first `i` coordinates; taken literally the suffixes could differ,
which would produce `(d_{i+1}...d_k)^2` pairs per bundle instead of the
`d_{i+1}...d_k` that `m(G)` charges for. The matching-suffix reading is the one
consistent with `m(G)` and with the intuitive definition, and it is the *weaker*
operation set, so any object valid under it is valid under either reading. The
library implements matching-suffix by default and has a `permissive=True` switch
for exploration only.

**The forcing pair.** `R` is a list of single-support functions (a vertex `w` and a
nonzero label `x`, meaning `delta_w (x) x`), `T` a list of vertices. Let `M` be the
`Z`-module spanned by the edge functions `delta_u (x) x - delta_v (x) x` and by `R`.
A vertex `v` outside `T` joins `T` when some `f in M` is supported inside
`T u {v}` and has `f(v) = (a,-a)` with `a != 0`. Iterate to `T = V`.

**Score.** `S = (m(G) + |R|) / (n(G) - |T|)`. Note `|T|` is the *initial* free set,
so a larger `T` shrinks the denominator and *hurts*.

**Working over Q is legitimate.** `M` is a `Z`-module and we only need *some*
nonzero multiple of `tau`; a rational witness clears denominators back into `M`.
All the linear algebra below is over a field.

### The reformulation the engine runs on

> **Lemma 1 (row-space test).** Let `W` be the `Q`-span of the generator rows inside
> `Q^{2n}`, let `T` be the currently forced set and `U = V \ T`. Then
> `v in U` can be forced **iff** `delta_v (x) tau` lies in `W|_U`, the image of `W`
> under restriction to the coordinates of `U`.

(`=>` lift the witness; `<=` the lift vanishes on `U \ {v}`, so its support is inside
`T u {v}`, and its value at `v` is `tau`.) One row reduction of an
`(m+r) x 2|U|` matrix per round answers the question for *every* candidate at once,
instead of one elimination per candidate. This is what makes the verifier cheap.

### Structure lemmas (all used as search pruning; all proved, several machine-checked)

Write `psi(a,b) = a+b`, so `psi(x) != 0` for every label and `psi(tau) = 0`.

> **P1.** A generator sitting at a vertex already in `T` is useless: if `w in T` and
> `f = g + lambda delta_w x` is supported in `T u {e}`, then so is `g`.

> **P2.** Two non-parallel generators at one vertex force it outright; a third, or a
> parallel duplicate, adds nothing. So: at most two generators per vertex, never
> parallel.

> **P3 (rank).** Each forcing step consumes a fresh dimension of `M` (the witness for
> `v_j` is nonzero at `v_j`, where all earlier witnesses vanish), so
> `dim W >= n - |T|`, hence `m + r >= n - |T|` and `S >= 1`.

> **P4 (local necessity).** Every generator row is supported on at most two vertices,
> with value `+/- x` there. So the `v`-component of any `f in M` lies in the span of
> {labels of edges incident to `v`} u {labels of generators at `v`}. Since no label is
> parallel to `tau`, that span must have rank 2. **Every vertex outside `T` must see
> two non-parallel directions.** This both lower-bounds `r` by
> `sum_v max(0, 2 - indep(v))` and *pins the positions* of the mandatory generators.

> **P5 (canonical pair).** Two non-parallel generators at `v` contribute exactly
> `delta_v (x) Q^2` to the module — the span does not depend on *which* independent
> pair is chosen. So a vertex needing two generators presents one case, not
> `C(|pool|,2)`.

> **P6 (T beats a double generator).** Putting `v` into `T` is *equivalent* to adding
> `delta_v (x) Q^2` to the module: if `f` is supported in `T u {v} u {e}` then
> `f - delta_v (x) f(v)` is supported in `T u {e}` and lies in `M + delta_v (x) Q^2`,
> and conversely. But the two cost differently — two generators cost 2 in the
> numerator, `v in T` costs 1 in the denominator — and
> `(p-2)/(q-1) < p/q  <=>  p < 2q  <=>  score < 2`.
> **So in any object with score below 2, every vertex carries at most one generator,
> and `r <= n`.** A vertex with no incident edge label must simply be put in `T`.
> Machine-checked on 419 random forcing objects with a double-generator vertex
> (`tests/test_p6_swap.py`): the swap never breaks forcing and always improves the
> score. Restricting the search to one generator per vertex is a 6x speedup at
> `n = 4` and loses nothing.

> **P7/P8 (the cut lemma — the general form of P4).** For `A` a subset of `V` write
> `Sigma_A(f) = sum_{u in A} f(u)`. An edge function has `Sigma_A = 0` unless the edge
> crosses the cut `(A, V\A)`, in which case it is `+/- x`; a generator contributes its
> label iff it sits inside `A`. So for every `f in M`
> ```
> Sigma_A(f)  in  span{labels crossing the cut}  +  span{generator labels inside A}
> ```
> If `f` witnesses the forcing of `v in A` then
> `Sigma_A(f) = tau + sum_{u in T_0 ∩ A} f(u)`. Two specialisations:
> * `A = {v}` gives back **P4**.
> * `A = V` with `T_0` empty gives **P7: `tau` must lie in the span of the GENERATOR
>   labels alone.** Since no single label is parallel to `tau`, *any object with `T`
>   empty needs at least two generators, of two different slopes* — however large and
>   however well connected it is. In particular **a generator-free object with `T` empty
>   can never force a single vertex**, so `r = 0` forces `|T| >= 1`. (Checked: 515 random
>   forcing objects with `T` empty, no violations, `tests/test_cut_lemma.py`; and an
>   exhaustive `r = 0` sweep of `d = [2,2]` over six slopes finds nothing,
>   `logs/rzero.log`.)
>
> P8 is a whole family of necessary conditions, one per cut, interpolating between the
> local rule and the global one. It is the natural place to look for the `3/2` barrier:
> the barrier is a statement that these cut conditions cannot all be met cheaply.

> **P9 (nested-cut chain — the sharpest necessary condition found here).** Let
> `v_1, ..., v_q` be the order in which vertices are forced (`q = n - |T|`) and put
> `A_j = {v_j, v_{j+1}, ..., v_q}`, so `A_1 = V \ T_0` and `A_q = {v_q}`. The witness
> `f_j` is supported inside `T_0 u {v_1..v_j}`, so within `A_j` only `v_j` carries mass
> and `Sigma_{A_j}(f_j) = tau` exactly. By P8, **for every `j`**
> ```
> tau  in  span{labels crossing (A_j, V\A_j)}  +  span{generator labels inside A_j}
> ```
> i.e. *every* member of a nested chain of `q` cuts, from `V \ T_0` down to a single
> vertex, must be crossed with rank 2. `j = q` is P4 at the last vertex; `j = 1` is P7.
> An object is therefore a labelled graph admitting a **rank-2 elimination ordering**.
> This is a purely combinatorial certificate condition, it is checkable in
> `O(q * (m+r))` once an order is guessed, and it is the obvious candidate objective to
> optimise against.

> **Theorem 2 (two slopes are never enough).** If all labels used lie in only two
> slope classes, then any object that forces has score `>= 2`.
> *Proof.* With `x, y` independent, `f = c^x (x) x + c^y (x) y`, and vanishing outside
> `T u {e}` forces `c^x, c^y` to vanish there. `tau = alpha x + beta y` with both
> coefficients nonzero, so `c^x_e != 0`. The `x`-edge module is exactly the vectors
> summing to zero on each connected component of `G_x` (relaxed on components carrying
> an `x`-generator), so the `G_x`-component of `e` must contain a `T`-vertex or an
> `x`-generator — and the same for `y`. Liveness of a component therefore depends only
> on `T_0` and the generators: **forcing never cascades in the two-slope case.** Hence
> every component of `G_x` and of `G_y` is live, giving
> `m >= (n-a) + (n-b)` and `r >= max(0,a-t) + max(0,b-t)` with `a, b` the component
> counts, and in every case `m + r >= 2(n-t)`. []
>
> Machine-checked on 445 random successful two-slope objects (`tests/test_two_slope_theorem.py`).

**Consequence — where the whole subject lives.** Three or more slopes are necessary,
and the gain over the trivial bound 2 comes entirely from the *linear relations among
three or more slopes*: with `|X'| >= 3` the kernel `K = ker(Q^{X'} -> Q^2)` is nonzero,
so unforced vertices may carry nonzero coefficient vectors lying in `K` and cancel out.
Every good object is a way of arranging such a cancellation.

---

## 2. What is rebuilt and certified

### The trivial object, `AK(2)`
`k = 0` (one vertex), `X = {(0,0),(1,0),(0,1)}`, `R` = two generators at that vertex,
`T` empty. `(n,m,r,t) = (1,0,2,0)`, score exactly **2**. `tests/test_basic.py`.

### The easy published construction, score **7/4** — CERTIFIED
This is Katz–Tao's trapezoid (`Recent progress on the Kakeya conjecture`,
math/0010069, Theorem 3.2 = `SD(0, 1/2, 2/3, 1; 2 - 1/4)`; in Tao's 2025
normalisation, `SD({0,1,2,infinity}; -1) <= 2 - 1/4`).

The dictionary that makes the translation mechanical:

| Katz–Tao | constructible-graph object |
|---|---|
| `pi_t(a,b) = (1-t)a + tb` | label `x = (1-t, t)` up to scale |
| `pi_-` (the difference map) | `tau = (1,-1)` |
| points `g_1..g_4` of the configuration | the `n` vertices |
| a gluing constraint `pi_t(g_i) = pi_t(g_j)` | an edge labelled `x`; costs one factor of `N` in the Cauchy–Schwarz lower bound | 
| a projection recorded by the injective map | an element of `R`; costs one factor of `N` in the upper bound |
| points allowed to stay free | `T` |
| the exponent `alpha` in `#G <= N^alpha` | `(m + |R|) / (n - |T|)` |

Katz–Tao's trapezoid: `pi_0(g1)=pi_0(g2)`, `pi_0(g3)=pi_0(g4)`, `pi_1(g1)=pi_1(g3)`,
`pi_{2/3}(g2)=pi_{2/3}(g4)` gives `#T >= (#G)^4 / N^4` (so `n = 4`, `m = 4`), and the
injective map `((g1,g2),(g3,g4)) -> (pi_{1/2}(g1), pi_{1/2}(g2), pi_1(g4))` gives
`#T <= N^3` (so `r = 3`). Score `(4+3)/(4-0) = 7/4`.

As a `2 x 2` box — in **Katz–Tao's** vertex naming, `g1=(1,1), g2=(2,1), g3=(1,2),
g4=(2,2)` (Epoch's figure names the same four points differently; see below, where
`g1=(2,1), g2=(1,1)`):
```
score = 7/4   m = 4, |R| = 3, n = 4, |T| = 0
X   = [[0,0],[1,0],[0,1],[1,1],[1,2]]
d   = [2, 2]
f   = [{(1,): (1,0)},  {(1,1): (0,1), (2,1): (1,2)}]
T   = []
R   = [{(1,1): (1,1)}, {(2,1): (1,1)}, {(2,2): (0,1)}]
```
Verification (`tests/test_175.py`): forcing succeeds; the **first** vertex forced is
`(1,2)`, which is `g3` in **both** namings — exactly the vertex Katz–Tao's identity
`pi_-(g3) = -2 pi_{1/2}(g1) + 4 pi_{1/2}(g2) - 2 pi_1(g4)` (their eq. 12) determines,
i.e. the linear-algebra step the whole method turns on. The remaining three fall to the local rule. Confirmed
by four independent engine configurations (per-candidate vs. row-space, exact `Q` vs.
mod `p`), and the object is emitted verbatim in Epoch's six-line answer format.

### Cross-check against Epoch's own write-up
The full write-up behind the problem page is at
`https://epoch.ai/files/open-problems/arithmetic-kakeya.pdf` (mirrored as
`papers/epoch-ak.pdf`). It contains the two Katz–Tao configurations drawn out. **The
object rebuilt above is theirs, vertex for vertex**: their Figure 3 is
`g1-g2` and `g4-g3` labelled `(1,0)`, `g4-g1` labelled `(1,2)`, `g3-g2` labelled
`(0,1)`, with `R = {(1,1)g1, (1,1)g2, (0,1)g4}` and `T` empty — which is the `2 x 2`
box above under `g1=(2,1), g2=(1,1), g3=(1,2), g4=(2,2)`. Their derivation forces `g3` first, by
`(1,-1)g3 = (2,2)g1 - (1,1)g2 - (0,2)g4`; **our engine also forces `(1,2) = g3` first**,
finding its own witness and knowing nothing of theirs. Independent agreement on the score, the
parameters, and the forcing order.

### The second published object, score **11/6** — ALSO CERTIFIED
Epoch's Figure 2 is Katz–Tao's other configuration, and it is the record for the
**sums-differences** problem — Goal 2 of the Epoch page, `X = {(1,0),(0,1),(1,1)}`
(three slopes only), best known bound `11/6`:
```
score = 11/6   m = 7, |R| = 4, n = 6, |T| = 0
X   = [[0,0],[1,0],[0,1],[1,1]]
d   = [2, 3]
f   = [{(1,): (1,0)},
       {(1,1): (0,1), (2,1): (0,1), (1,2): (1,1), (2,2): (0,1)}]
T   = []
R   = [{(1,2): (1,0)}, {(2,1): (1,1)}, {(1,1): (1,1)}, {(1,3): (0,1)}]
```
`objects/obj_11_6.py`, `tests/test_11_6.py`. Certified in exact rational arithmetic, and
the first vertex forced is `g5` — exactly Katz–Tao's identity
`(1,-1)g5 = (1,0)g1 - (0,1)g6 + (1,1)g4 - (1,1)g3`. The single level-1 bundle
`f_1(1) = (1,0)` carries all three horizontal edges at once (multiplicity `d_2 = 3`),
which is the cleanest illustration of how bundles work.

### Optimality of 7/4 at `n = 4`
Exhaustive over every label assignment on `d = [2,2]` and `d = [4]`, four-slope alphabet
`{0, infinity, 1, 2}`, `T` empty: **best score `7/4`, attained by 16 labelled objects**
(the trapezoid and its symmetric variants); `d = [4]` (a path) produces nothing at all
`<= 7/4`. Rerun exhaustively on `d = [2,2]` with a **six-slope** alphabet
`{0, infinity, 1, 2, 3, 1/2}` and `|T| <= 1` (343 graphs, complete): **best still `7/4`**,
120 witnesses (`logs/n4_p6_t1.log`). The trapezoid is the 4-vertex optimum over
everything tried.

---

## 3. Score algebra — how the published constructions compose

Both published improvements are *iterations*: a gadget plus an application of the
inductive hypothesis to a fibre. Katz–Tao, `New bounds for Kakeya problems`
(arXiv:math/0102135):

* **Corollary 3.5 (vertical line segments, pairs `(g,g')` glued along `pi_{r_0}`):**
  `SD(beta) => SD((4 beta - 1) / (2 beta))`.
  On object parameters `beta = p/q = (m+|R|)/(n-|T|)`: `(p,q) -> (4p - q, 2p)`.
  Fixed point `1 + sqrt(2)/2 = 1.70710678...`.
* **Theorem 4.1 (corners, triples `g1 ~_{r1} g2 ~_{r2} g3`):**
  `SD(beta) => SD((3 beta^2 + 2 beta - 2) / (beta^2 + 3 beta - 2))`.
  On object parameters: `(p,q) -> (3p^2 + 2pq - 2q^2, p^2 + 3pq - 2q^2)`.
  Fixed point: `beta(beta^2+3beta-2) = 3beta^2+2beta-2`, i.e. **`beta^3 - 4beta + 2 = 0`**.

Both start at the trivial object `(p,q) = (2,1)`; one corner step already gives
`(14,8) = 7/4`, which is why the trapezoid is "depth 1" on both ladders.
`src/ladder.py` computes these in exact arithmetic:

```
segment ladder:  2, 7/4, 12/7, 41/24, 70/41, 239/140, ...      -> 1.7071067811
corner  ladder:  2, 7/4, 171/101, 101863/60652,
                    36127271451/21553324589, ...               -> 1.6751308706
Epoch target 1.675 < gamma:  True   (gap 1.309e-4)
```

Two facts fall straight out of this table and are the operative facts for the campaign:

1. **The record has no witness object.** Every finite object has a rational score; the
   corner ladder's scores decrease to `gamma` but never reach it, and `1.675 < gamma`.
   Beating 1.675 therefore cannot be done by iterating deeper — it needs a construction
   outside both published schemes.
2. **The published objects are enormous almost immediately.** Depth 2 on the corner
   ladder already needs `n - |T| = 101` vertices with `m + |R| = 171` (score
   `171/101 = 1.6931`); depth 3 needs `60,652`; depth 4 needs `2.16 x 10^10`. Nobody has
   ever written these down as explicit constructible graphs — the papers work with the
   exponents, not the objects.

---

## 4. The 1.675 attempt — how far, and the blocker

**How far.** The two ladders were decoded, verified against the source, and reduced to
exact integer maps on `(p,q)`; the depth-1 object (7/4) was built and certified; the
depth-2 corner object's exact parameters (`n-|T| = 101`, `m+|R| = 171`) were computed.

**The blocker, stated precisely.** There are two, and the first is fatal to the literal
reading of the task:

* **B1 — no finite object attains `gamma`, let alone 1.675.** `gamma = 1.6751309` is the
  fixed point of the corner recursion, approached strictly from above. The Epoch target
  is set `1.31e-4` below it, deliberately (the problem's own prompt says the best known
  value is "slightly greater than 1.675"). So the task is *not* "reconstruct the record
  object"; there is no record object. The task is "find a finite object that beats the
  entire published family". This reframing is the main deliverable of this section.
* **B2 — the depth-2 object is a 101-vertex construction that has to be built by hand
  from the corner gadget.** Theorem 4.1's proof is *heuristic in the source* (Katz–Tao
  say so explicitly; the rigorous version in their section 4.2 buys uniformity by
  swapping slope sets `M` times and losing an epsilon each time). Unrolling it into an
  explicit `d_1 x ... x d_k` box with explicit labels is a genuine construction job — the
  fibring step (`mu`, `nu`, the refinement `G'_{nu_0}`) is not a plain graph substitution,
  which is why one corner step turns `4` vertices into `101` rather than into a product.
  That job was **not** completed here; it is the natural next seat (see §6).

**A negative result that limits one obvious route.** The most natural way to try to beat
a block's own score is to chain copies: take a good block `H` and glue `D` copies with a
small interface at each gap. That cannot work by itself:

> **Chain remark.** If the copies are forced one at a time (copy `c` fully forced before
> copy `c+1`), then an interface edge from the fully-forced copy `c` to a vertex `v` of
> copy `c+1` acts *exactly* like a generator `delta_v (x) x` — the other endpoint is in
> `T`, so it contributes nothing else. Hence the minimum interface size equals `H`'s own
> minimum `|R|`, and the chain score `(D m_H + (D-1) r_H + r_0)/(D n_H)` converges to
> `H`'s own standalone score from above. Chaining is score-neutral.

So every improvement has to come from **forcing orders that interleave copies** — global
cancellations spanning several blocks, exactly like the trapezoid, where the first vertex
forced (`g3`) needs a witness spread over all four vertices at once. That is the single
sharpest piece of design guidance this seat produces.

---

## 5. What is in the folder

```
src/kakeya.py         the formalism: ConstructibleGraph, m/n, edges, the module,
                      two forcing engines (per-candidate and row-space), exact-Q and
                      mod-p backends, scorer, Epoch six-line serialiser AND parser
                      (`verify_answer(text, bound)` independently re-checks a
                      submitted answer string end to end; round-trip tested)
src/fastcore.py       small-matrix mod-p forcing engine (pure Python; ~2x numpy here)
src/search.py         object search: label enumeration, P1-P4 pruning, min-|R| solver
src/run_scan.py       scan driver (writes machine-readable RESULT/HITOBJ lines)
src/ladder.py         the two Katz-Tao ladders in exact arithmetic
objects/obj_175.py    the certified 7/4 object, with the KT dictionary in the docstring
objects/obj_11_6.py   the certified 11/6 object (the sums-differences record, Goal 2)
tests/test_basic.py            13 checks: X-validity, AK(2)=2, m-multiplicity, negatives
tests/test_175.py              certifies 7/4 in exact Q, four engine configurations
tests/test_11_6.py             certifies 11/6 and its forcing order (g5 first)
tests/test_engines_agree.py    300 random instances, all engines agree
tests/test_two_slope_theorem.py  445 successful two-slope objects, none below 2
tests/test_p6_swap.py          419 double-generator objects, swap never breaks forcing
tests/test_cut_lemma.py        515 objects forcing from empty T, P7 never violated
src/rzero.py          generator-free sweep (a direct check of P7)
src/cycles8.py        exhaustive 2-regular objects on the 2x2x2 box
src/schemes.py        Route B: one-level scheme exponents and their fixed points
papers/               epoch-ak.pdf  <- the problem's own write-up, with both objects
                      kt.txt (math/0010069), newbounds.txt (math/0102135),
                      1712.02108 (Green-Ruzsa), 2511.15135 (Tao 2025), tao3b.html
logs/                 scan output
```
All tests pass. Reproduce with `python3 tests/test_basic.py` etc. from the folder root.

---

## 6. Search-strategy sketch — how to beat 1.675

### 6.0 There are TWO prizes, and the second one is much softer
The Epoch write-up states two goals:
* **Goal 1** — a constructible proof of `omega(X) < 1.67513...` for some finite `X`.
  That is the headline problem, and §4 explains why it is hard.
* **Goal 2** — a constructible proof of `omega({(1,0),(0,1),(1,1)}) < 11/6`, i.e. beat
  the sums-differences bound using **only three slopes**. The page says "any improvement
  is probably at least moderately interesting"; the bound is Katz–Tao 1999 and has stood
  since. The lower bound is `1.77898` (Lemm 2015, sharpened in the eighth decimal place
  by AlphaEvolve), so there is a real gap of `0.054` to work in.

**Goal 2 is where a small-object search has the best odds**, for a reason that is
arithmetic rather than optimistic: the alphabet is fixed at three slopes, so the label
space is `4^(number of bundles)` instead of `5^` or `7^`, and the objects at play are
tiny (the record is `n = 6`). `d = [2,2,2]` is 16384 labelled graphs; `d = [3,3]` is
65536. Both are inside reach of even the current Python engine. The reachable-fraction
table for `11/6` is generous too: `n = 8, |T| = 0, m + |R| = 14` already gives
`14/8 = 1.75 < 11/6`, and `n = 9, m+|R| = 16` gives `16/9 = 1.778`.
Scans for this were launched but had not returned when this seat closed — see
`logs/g2_*.log` and §7.

**Goal 2's reachable-fraction table** (largest `m+|R|` strictly below `11/6` for each
`q = n - |T|`):

| `q` | max `m+\|R\|` | score |
|---|---|---|
| 4 | 7 | 7/4 = 1.7500 |
| 5 | 9 | 9/5 = 1.8000 |
| 6 | 10 | 5/3 = 1.6667 |
| 7 | 12 | 12/7 = 1.7143 |
| 8 | 14 | 7/4 = 1.7500 |
| 9 | 16 | 16/9 = 1.7778 |
| 10 | 18 | 9/5 = 1.8000 |
| 11 | 20 | 20/11 = 1.8182 |
| 12 | 21 | 7/4 = 1.7500 |
| 13 | 23 | 23/13 = 1.7692 |
| 14 | 25 | 25/14 = 1.7857 |

The gentlest targets are the larger `q`: `q = 11` needs only `20/11 = 1.8182`, `q = 10`
needs `9/5 = 1.8`. At the small end the jump is brutal — `q = 6` (the size of the record
object) demands `10/6 = 5/3`, better than the Goal 1 target. So **Goal 2 wants objects
somewhat bigger than the record, not smaller**: `n = 10, 11, 12` with `|T| <= 1`.
*The right universal cutoff for Goal 2 is `20/11 = 1.8182`: `floor(20q/11)` reproduces
the whole column above for every `q` in range. This seat's first Goal-2 battery used
`9/5` instead, which is correct for every `q` except `q = 11`; the later `[2,5]`/`[5,2]`
runs use `20/11`.*

### 6.1 The target is coarser than it looks
Score `= p/q` with `q = n - |T|`. Tabulating the largest `p/q <= 1.675` for each `q`:

| `q` | best score `<= 1.675` | | `q` | best |
|---|---|---|---|---|
| 3 | 5/3 = 1.6667 | | 14 | 23/14 = 1.6429 |
| 4 | 3/2 = 1.5 | | 17 | 28/17 = 1.6471 |
| 5 | 8/5 = 1.6 | | 20 | 33/20 = 1.65 |
| 8 | 13/8 = 1.625 | | 29 | 48/29 = 1.6552 |
| 11 | 18/11 = 1.6364 | | 40 | **67/40 = 1.675** |

**`q = 40` is the first denominator at which 1.675 is reachable exactly.** Every object
with fewer than 40 forced vertices that beats the record automatically achieves
`<= 5/3 = 1.6667` — a margin of `8.5e-3` over `gamma`, sixty-five times the target gap.
So: small objects must be *substantially* better, not marginally. That is either a
reason for pessimism about small `n`, or the reason nobody has looked.

### 6.2 Two independent routes

**Route A — direct object search.** Enumerate `(d_1..d_k, labels, T, R)` and score.
Live now; speed is the bottleneck.

*Calibration (the check that matters).* Handed only the **shape** of the published 11/6
object — the `2 x 3` box with its seven edges and their labels, and no generators at all —
the generator search returns minimum `|R| = 4` in 2.4 s, i.e. it independently
rediscovers the record's exact cost, with a generator set of its own choosing
(`(1,1)g4, (1,0)g3, (0,1)g1, (1,1)g2` rather than Katz–Tao's four). Likewise the `n = 4`
sweep rediscovers the 7/4 trapezoid from nothing but the box dimensions. The search finds
what is there.
* *Parametrisation.* Choose the box `d`, then one label from `X u {0}` per bundle
  (level `i` has `d_1...d_{i-1}(d_i - 1)` bundles), then `T`, then `R`.
* *Symmetry.* The problem is invariant under the projective transformations of the slope
  line fixing `-1` (Tao 2025 §1.1); that group is 2-transitive on the other slopes, so
  two of the labels used may always be normalised to `(1,0)` and `(0,1)`. `X` is free, so
  only the *number and cross-ratios* of the slopes used matter.
* *Pruning.* P1 (no generator on a forced vertex), P2/P5/P6 (**at most one**
  generator per vertex once score `< 2`; double-generator vertices belong in `T`),
  P3 (`r >= (n-t) - rank(edge rows)`), P4 (mandatory generator *positions* are pinned by
  the local rank-2 condition — this is the one that collapses the search), plus the
  budget `r <= floor(target*(n-t)) - m`.
* *Heuristic on shape.* P4 gives `2m + r >= 2(n-t)`, so `S >= 2 - m/(n-t)`; together with
  `S >= m/(n-t)` this is minimised at `m ~ n - t`. The certified 7/4 object sits exactly
  there (`m = n = 4`). Search graphs with `m` close to `n - |T|` first.
* *Where to look — Goal 1.* `n = 8` (`d = [2,2,2]`) and `n = 12, 16` with
  `|T| in {0,1,2}`. Note `n = 16, |T| = 2, m + r = 23` gives `23/14 = 1.6429`;
  `n = 16, |T| = 0, m + r = 26` gives `13/8 = 1.625`. Both are in the reachable table.
* *Where to look — Goal 2 (the better bet).* Three slopes only, so the label space is
  `4^bundles`. Aim at `q = n - |T|` of 10, 11, 12: `d = [2,5]`, `[5,2]`, `[2,2,3]`,
  `[3,4]`, `[2,6]`, `[3,2,2]` with `|T| in {0,1}`, cutoff `20/11 = 1.8182`. The record
  object is `d = [2,3]` with `m = 7, r = 4`; the natural next rungs are the same shape
  one or two rows taller, where an extra row costs `1` level-1 edge plus at most `2`
  level-2 edges and may cost no extra generators at all.
* *Engine requirement.* The Python engine costs ~1.3 ms per closure at `n = 4` and the
  min-`|R|` DFS dominates; `n >= 12` needs the row-space reduction in C or in packed
  `numpy` batches (batch many candidate objects into one elimination). Budget a real
  engineering day for this before a serious sweep. **Do not run a large sweep on the
  current Python engine — it is a correctness reference, not a search engine.**

**Route B — a better gadget recursion.** The published exponents come from exactly two
gadgets (pairs, then triples-with-a-corner) and each yields a rational map `g(beta)` whose
fixed point is the record. The map is produced mechanically from the gadget: a
Cauchy–Schwarz lower bound on the number of configurations, an injectivity upper bound,
and one application of `SD(beta)` to a fibre. **Enumerate gadgets and compute their
`g`, then ask for a fixed point below 1.675.** The two known data points are
```
pairs   : g(beta) = (4b - 1) / (2b)                      fixed point 1.70710678
corners : g(beta) = (3b^2 + 2b - 2) / (b^2 + 3b - 2)     fixed point 1.67513087
```
The improvement from pairs to corners is one extra vertex in the gadget. Katz–Tao say
in as many words that they "have certainly not exhausted all the possibilities of this
approach", and this is a *symbolic* search over small rational maps — cheap, and
independent of the object-search engineering.

**A general formula for one-level schemes** (`src/schemes.py`, derived here by stripping
Corollary 3.5 to its counting skeleton). A scheme is four exponents:
`c` copies of `G` in the gadget, `e` gluing constraints (so `#Gadget >= #G^c/N^e`),
a fibre bound `#fibre <= N^u`, and a popularity exponent `w` in
`N* = #fibre / (#Gadget/N^w)`. Chaining the three steps gives
```
g(beta) = ( e + w + u (beta - 1)/beta ) / c        fixed point:  c b^2 - (e+u+w) b + u = 0
```
The map depends only on `(c, u, e+w)`. Checks:
* pairs `(c,e,u,w) = (2,1,1,2)`: `g = 2 - 1/(2 beta)`, `2b^2 - 4b + 1 = 0`,
  fixed point `1 + sqrt2/2`. That is Corollary 3.5 exactly.
* the *naive one-level* analysis of the corner gadget, `(3,2,1,2)`, gives
  `3b^2 - 5b + 1 = 0`, fixed point `1.4343` — **below the 3/2 barrier, hence not
  realisable.** That is precisely why Katz–Tao could not use corners at one level and
  had to feed the pair result back in, producing a cubic instead of a quadratic. The
  formula reproduces both the published scheme and the reason the obvious next one fails.

**The shopping list.** Sweeping integer `(c,e,u,w)` with `c <= 8`, **199 counting
skeletons have fixed point strictly inside `(3/2, 1.675]`**, the smallest gadget size
admitting one being `c = 3`:
```
(c,e,u,w) = (3,1,2,3) / (3,2,2,2) / (3,3,2,1)  ->  1.577350
(c,e,u,w) = (3,1,5,2)                          ->  1.666667
(c,e,u,w) = (4,1,1,5) ...                      ->  1.593070
(c,e,u,w) = (5,1,2,6) ...                      ->  1.540312
```
Note `(3,2,2,2)` is the corner gadget with `u = 2` instead of `u = 1` — i.e. a fibre
bound of `N^2` rather than `N`. **The open half of Route B is realisability: which of
these 199 skeletons corresponds to an actual configuration and fibering.** That is a
paper-sized question, but it is a *finite, enumerated* one, and it is the same kind of
question that produced every published improvement in this area.

### 6.3 The composition rule to exploit (and the trap to avoid)
* Nesting `H` inside a box multiplies: `n_G = n_H n_B`, `m_G = n_B m_H + (interface)`.
  The interface may depend on the inner vertex (that is what `f_{k+1}(e_1..e_k, e_{k+1})`
  buys), so gluing can be applied at a *chosen subset* of `H`'s vertices.
* **Trap:** copy-by-copy forcing makes interface edges exactly as expensive as
  generators (Chain remark, §4), so it is score-neutral. Any candidate design has to be
  checked for whether its forcing order *interleaves* blocks — i.e. whether some block
  is left partly unforced while another is entered. The engine's forcing log prints the
  order, so this is a one-line diagnostic. Both certified objects pass it: the 7/4
  trapezoid forces `g3` first (a witness spread over all four vertices at once), and the
  11/6 object forces in the order `g5 -> g4 -> g1 -> g6 -> g3 -> g2`, which crosses
  between the three rows of the `2 x 3` box four times.

### 6.4 Open items for the next seat
1. Read and reproduce the `3/2` barrier: it is **Nets Hawk Katz, "Elementary proofs and
   the sums differences problem", Collectanea Math. 57 (2006), 275–280** (reference [5] of
   the Epoch write-up) — "AK(3/2) is the limit of this kind of elementary argument". Not
   fetched this seat. (Epoch states the method cannot work below `3/2`;
   P3 + P4 only give `S >= 1` here). **Start from P8**: the cut lemma is a family of
   necessary conditions indexed by subsets of `V`, and the barrier ought to be the
   statement that they cannot all be satisfied for less than `1.5(n - |T|)`. The barrier
   proof will name the quantity that has to be pushed and probably hands over the right
   objective function for the search.)
2. Build the depth-2 corner object explicitly and certify `171/101` with this scorer —
   the first check that the formalism really does carry the published family, and the
   only way to see what an "intricate" object looks like in coordinates.
3. Port the row-space engine to C / batched numpy; then sweep `n = 8, 12, 16`.
4. Run Route B (symbolic gadget → rational map → fixed point) — it is cheap and it is
   where the published progress actually came from.
5. Resolve the operation-1 suffix ambiguity with Epoch's verifier if a candidate ever
   depends on it. Nothing here does.

### 6.5 A measured note on the engine's ceiling
The generator search is a depth-first search whose depth is the generator budget
`floor(target*(n-|T|)) - m`. That budget is small when `m` is large (good) and large
when `m` is small (bad), and the candidate list is `|unforced vertices| x |slopes|`. At
`n = 8` with a six-slope alphabet and budget 7 the DFS is `C(48, 7)` in the worst case
and does not terminate on the current engine — one diagnostic run (the cost of a single
constructible 8-cycle) had to be abandoned for exactly this reason. The fix is not
cleverness, it is arithmetic speed: the row-space reduction is a `(m+r) x 2|U|`
elimination over `F_p` and should be a few microseconds, not ~1.3 ms. Port `fastcore.py`
before the next sweep.

---

### 6.6 Size of the label space, by box and alphabet
The number of labelled graphs on a box is `(|slopes|+1)^(number of bundles)`, and the
bundle count is `sum_i d_1...d_{i-1}(d_i - 1)`:

| box | `n` | bundles | 3 slopes | 4 slopes | 6 slopes |
|---|---|---|---|---|---|
| `[2,2]`   | 4  | 3  | 64 | 125 | 343 |
| `[2,3]`   | 6  | 5  | 1 024 | 3 125 | 16 807 |
| `[2,2,2]` | 8  | 7  | 16 384 | 78 125 | 823 543 |
| `[2,4]`   | 8  | 7  | 16 384 | 78 125 | 823 543 |
| `[3,3]`   | 9  | 8  | 65 536 | 390 625 | 5 764 801 |
| `[2,5]`   | 10 | 9  | 262 144 | 1 953 125 | 40 353 607 |
| `[2,2,3]` | 12 | 11 | 4 194 304 | 48 828 125 | 2.0e9 |
| `[2,2,2,2]`| 16 | 15 | 1.07e9 | 3.05e10 | 4.7e12 |

Multiply by the `|T|` choices (`1 + n + C(n,2)` for `|T| <= 2`) and by the generator
search. At the current ~0.2–0.5 s per graph, three-slope `[2,4]` and `[2,2,2]` are an
hour each; three-slope `[3,3]` is a day; anything beyond needs the C port. The
three-slope column is the reason Goal 2 is the tractable target.


## 7. Search runs from this seat

Everything below used the four/six-slope alphabets for Goal 1 and the three-slope
alphabet `{(1,0),(0,1),(1,1)}` for Goal 2. "complete" means the whole label space for
that box was enumerated; otherwise the run was sampled or time-capped and **absence of a
hit proves nothing**. Machine-readable records: `results.json` (`scans` key) and
`logs/*.log` (one `RESULT` line per job, `HITOBJ` lines for any hit).

| job | box | slopes | max \|T\| | target | scanned / total | complete | best | hits |
|---|---|---|---|---|---|---|---|---|
| `cycles8` | `` | 6 | - | r=0 | None / None | no | (none) | 0 |
| `g2_222_t1` | `2x2x2` | 3 | 1 | 9/5 | 864 / 16384 | no | (none) | 0 |
| `g2_23_t1` | `2x3` | 3 | 1 | 9/5 | 1024 / 1024 | **yes** | (none) | 0 |
| `g2_24_t1` | `2x4` | 3 | 1 | 9/5 | 1887 / 16384 | no | (none) | 0 |
| `g2_25_t1` | `2x5` | 3 | 1 | 20/11 | 9 / 40000 | no | (none) | 0 |
| `g2_32_t1` | `3x2` | 3 | 1 | 9/5 | 1024 / 1024 | **yes** | (none) | 0 |
| `g2_33_t1` | `3x3` | 3 | 1 | 9/5 | 1691 / 65536 | no | (none) | 0 |
| `g2_42_t1` | `4x2` | 3 | 1 | 9/5 | 867 / 16384 | no | (none) | 0 |
| `g2_tall_2x4` | `2x4` | 3 | 1 | <11/6 | None / None | no | (none) | 0 |
| `g2_tall_2x5` | `2x5` | 3 | 1 | <11/6 | None / None | no | (none) | 0 |
| `g2_tall_2x6` | `2x6` | 3 | 1 | <11/6 | None / None | no | (none) | 0 |
| `n4_p6_t1` | `2x2` | 6 | 1 | 7/4 | 343 / 343 | **yes** | 7/4 | 120 |
| `n6a2_23_t1` | `2x3` | 4 | 1 | 67/40 | 1392 / 3125 | no | (none) | 0 |
| `n6a_23_t1` | `2x3` | 4 | 1 | 67/40 | 1535 / 3125 | no | (none) | 0 |
| `n6b2_32_t1` | `3x2` | 4 | 1 | 67/40 | 1104 / 3125 | no | (none) | 0 |
| `n6b_32_t1` | `3x2` | 4 | 1 | 67/40 | 1203 / 3125 | no | (none) | 0 |
| `n6c2_6_t1` | `6` | 4 | 1 | 67/40 | 1619 / 3125 | no | (none) | 0 |
| `n6c_6_t1` | `6` | 4 | 1 | 67/40 | 1700 / 3125 | no | (none) | 0 |
| `n6d_23_t2` | `2x3` | 4 | 2 | 67/40 | 1492 / 3125 | no | (none) | 0 |
| `n8a_222_t0` | `2x2x2` | 4 | 0 | 67/40 | 207 / 40000 | no | (none) | 0 |
| `n8b_222_t1` | `2x2x2` | 4 | 1 | 67/40 | 173 / 15000 | no | (none) | 0 |
| `n8c_24_t1` | `2x4` | 4 | 1 | 67/40 | 166 / 15000 | no | (none) | 0 |
| `rzero` | `2x2` | 6 | - | r=0 | 343 / 343 | **yes** | (none) | 0 |
| `rzero` | `2x2x2` | 4 | - | r=0 | 78125 / 78125 | **yes** | (none) | 0 |
| `rzero` | `2x3` | 4 | - | r=0 | 3125 / 3125 | **yes** | (none) | 0 |
| `rzero` | `3x2` | 4 | - | r=0 | 3125 / 3125 | **yes** | (none) | 0 |
| `rzero` | `2x2x2` | 6 | - | r=0 | 60000 / 60000 | no | (none) | 0 |
| `rzero` | `2x2x2x2` | 4 | - | r=0 | 59201 / 60000 | no | (none) | 0 |

### Reading of these runs — what is and is not proved
**Complete sweeps (these are results):**
* `n = 4`, box `[2,2]` and `[4]`, four slopes, `|T| = 0`: best score `7/4`, 16 witnesses.
* `n = 4`, box `[2,2]`, **six** slopes, `|T| <= 1`, 343 graphs: best still `7/4`,
  120 witnesses. The trapezoid is the 4-vertex optimum over everything tried.
* **Goal 2, `n = 6`, boxes `[2,3]` and `[3,2]`, three slopes, `|T| <= 1`, 1024 graphs
  each: nothing below `9/5`.** So the sums-differences record cannot be beaten inside its
  own box shape — a small but genuine negative.
* Generator-free objects (`R` empty, `T` empty): none force, at every box swept
  (`[2,2]` six-slope, `[2,3]`, `[3,2]`, `[2,2,2]` four-slope, all complete). This is P7
  in action.

**Incomplete sweeps (these prove nothing):** everything else. Two cautions on reading
them:
1. The label enumeration is `itertools.product` order, so a truncated run covers a
   *prefix*, not a random sample — it varies the last bundle fastest and barely moves the
   first. A 49%-scanned box has not seen half the space in any useful sense.
2. Re-launching a timed-out job re-walks the same prefix. The `n6a2/n6b2/n6c2` rows are
   re-runs of `n6a/n6b/n6c` and add **no** coverage; they are in the table only because
   they are in the logs. Randomise the seed or shard the space next time.

The `n = 8` Goal-1 rows (166–207 graphs of 15 000–40 000) are essentially untouched;
they were run against six to fifteen sibling processes on a twelve-core machine and the
per-graph cost at that budget is seconds, not milliseconds.

**Net:** nothing found below `1.675`, and nothing found below `11/6`. The search has been
started, calibrated against two published objects, and stopped at the engine's ceiling.

### The `X` alphabets used
```
POOL3 = (1,0) (0,1) (1,1)                          slopes 0, oo, 1      [Goal 2]
POOL4 = POOL3 + (1,2)                              adds slope 2
POOL6 = POOL4 + (1,3) + (2,1)                      adds slopes 3, 1/2
```
Two of the slopes used may always be normalised to `(1,0)` and `(0,1)` by the projective
symmetry fixing `-1`, so `POOL4` is a one-parameter family and `POOL6` a three-parameter
one; enlarging the pool past that is not free, it is a real widening of the search.

---

## Addendum (appended 2026-09-06, from the Rust-port verification sweep; §1 text above unchanged)

**On the Operation-1 ambiguity flagged in §1 — the negative-side sentence the argument there lacks.** §1 justifies the matching-suffix reading by noting it is the *weaker* operation set, so any object valid under it is valid under either reading. That transfers **hits** across the readings; it says nothing about **0-hit results**, and every negative in this tree (stacked POOL4/POOL6, cycles8 POOL6 at every t, g2_tall at t ≤ 1, the scan sweeps) is a matching-suffix statement. The two readings do separate: on `d = [2,2]`, 456 of 8,320 enumerated configurations are invalid under matching-suffix and valid under the permissive (full `t1 × t2`) reading at an identical score (`kakeya.edges(permissive=True)` is a strict superset; `m(G)` never sees the flag). The disposal is that the smallest separating object,
`f = [{(1,): (1,0)}, {(1,1): (0,1), (2,1): (0,1)}]`, `T = [(2,1)]`, `R = [((1,1),(0,1))]`,
is permissive-valid at score **5/3 = 1.6667 on four vertices** — below the Epoch target 1.675 and below γ = 1.6751309…. If the permissive reading were the intended one, the Epoch problem would be solved by a 2×2 box and the Katz–Tao 7/4 and 11/6 objects would not be records. So the matching-suffix reading is the only one consistent with the problem being open, and the negatives stand under it without needing a permissive re-run. Evidence and scripts: `rust/refute/adjudicate/r5/FINDING-04-VERDICT.md` (`separator.py`, `best.py`; exact-rational Python, no Rust kernel involved).

**Scope note on the drivers, same sweep.** `cycles8` searches `t ∈ {0,1,2}` and `g2_tall` searches `t ∈ {0,1}` by hardcoded loops in both implementations; at POOL6 / 67/40 the `t = 3, r = 0` phase of cycles8 (score 8/5) was never searched by any run until 2026-09-06, when it was closed by enumeration (1,692,000 pairs, 0 hits); `g2_tall`'s `t = 2, 3, 4` lie inside the 11/6 cap and its negatives are `t ≤ 1` statements. `rzero` cannot find an object by P7 (its hit line is unreachable — a self-check of the theorem, which is what it was written to be). Details: `rust/crates/kakeya-search/PROGRESS.md`, `rust/refute/SWEEP-2026-09-06.md`.
