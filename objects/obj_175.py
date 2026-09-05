"""The 1.75 object: Katz-Tao's trapezoid, SD(0,1/2,2/3,1 ; 7/4).

Katz-Tao, 'Recent progress on the Kakeya conjecture', Thm 3.2 (= [KT99]).
Dictionary between their proof and the constructible-graph formalism:

  their pi_t(a,b) = (1-t)a + tb   <->   x = (1-t, t) up to scaling
      t = 0    -> (1,0)      t = 1/2 -> (1,1)
      t = 2/3  -> (1,2)      t = 1   -> (0,1)      pi_- -> tau = (1,-1)

  vertices of G     = the four points g1,g2,g3,g4 of a trapezoid
  edges of G        = the gluing constraints pi_t(g_i) = pi_t(g_j)
                      (each edge costs one factor of N in the lower bound)
  |R|               = the projections recorded by the injective map f
                      (each costs one factor of N in the upper bound)
  |T|               = vertices allowed to be free (none here)
  score (m+r)/(n-t) = the exponent alpha in #G <= N^alpha

  trapezoid:  pi_0(g1)=pi_0(g2), pi_0(g3)=pi_0(g4),
              pi_1(g1)=pi_1(g3), pi_{2/3}(g2)=pi_{2/3}(g4)
              -> n = 4, m = 4
  injective f: (pi_{1/2}(g1), pi_{1/2}(g2), pi_1(g4))  -> r = 3
  score = (4+3)/(4-0) = 7/4.

Realising the trapezoid as a d_1 x d_2 = 2 x 2 constructible graph:
       g1 = (1,1)   g2 = (2,1)
       g3 = (1,2)   g4 = (2,2)
  f_1(1)   = (1,0)   -> the two pi_0 edges  g1-g2 and g3-g4   (bundle x d_2 = 2)
  f_2(1,1) = (0,1)   -> the pi_1 edge       g1-g3
  f_2(2,1) = (1,2)   -> the pi_{2/3} edge   g2-g4
"""

X = [(0, 0), (1, 0), (0, 1), (1, 1), (1, 2)]
d = [2, 2]
f = [
    {(1,): (1, 0)},                       # f_1 : the two pi_0 gluings
    {(1, 1): (0, 1), (2, 1): (1, 2)},     # f_2 : pi_1 and pi_{2/3}
]
T = []
R = [((1, 1), (1, 1)),      # pi_{1/2}(g1) recorded
     ((2, 1), (1, 1)),      # pi_{1/2}(g2) recorded
     ((2, 2), (0, 1))]      # pi_1(g4)     recorded
