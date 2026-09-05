"""The 11/6 object: Katz-Tao's first configuration, omega({(1,0),(0,1),(1,1)}) <= 11/6.

This is the SUMS-DIFFERENCES record (Goal 2 of the Epoch problem: beat 11/6 with
X = {(1,0),(0,1),(1,1)}).  Taken from the Epoch write-up
`https://epoch.ai/files/open-problems/arithmetic-kakeya.pdf`, Figure 2:

        g4 --(1,0)-- g3
        |            |
      (0,1)        (0,1)
        |            |
        g1 --(1,0)-- g2
        |            |
      (1,1)        (0,1)
        |            |
        g6 --(1,0)-- g5

    n = 6, m = 7,  R = {(1,0)g1, (1,1)g3, (1,1)g4, (0,1)g6},  T = {} ,  score 11/6.

As a d_1 x d_2 = 2 x 3 box (coordinate 1 = column, coordinate 2 = row):
    g4=(1,1)  g3=(2,1)
    g1=(1,2)  g2=(2,2)
    g6=(1,3)  g5=(2,3)
f_1(1) = (1,0)  is the single level-1 bundle -- multiplicity d_2 = 3, i.e. the three
horizontal (1,0) edges at once.  f_2 carries the four vertical edges.

Katz-Tao's identity, which is what forces g5 first:
    (1,-1)g5 = (1,0)g1 - (0,1)g6 + (1,1)g4 - (1,1)g3.
"""

X = [(0, 0), (1, 0), (0, 1), (1, 1)]
d = [2, 3]
f = [
    {(1,): (1, 0)},                                  # the three horizontal edges
    {(1, 1): (0, 1), (2, 1): (0, 1),                 # g4-g1 , g3-g2
     (1, 2): (1, 1), (2, 2): (0, 1)},                # g1-g6 , g2-g5
]
T = []
R = [((1, 2), (1, 0)),      # (1,0) g1
     ((2, 1), (1, 1)),      # (1,1) g3
     ((1, 1), (1, 1)),      # (1,1) g4
     ((1, 3), (0, 1))]      # (0,1) g6
