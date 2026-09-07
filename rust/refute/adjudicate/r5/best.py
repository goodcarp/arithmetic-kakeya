import sys, itertools
sys.path.insert(0, "/Users/spaceman/Desktop/FrontierMath Open Problems/arithmetic-kakeya/src")
from kakeya import score, ConstructibleGraph, ForcingProblem
X = [(0,0),(1,0),(0,1),(1,1)]
NZ = [x for x in X if x != (0,0)]
d=[2,2]; verts=list(itertools.product(range(1,3),range(1,3)))
best=None
for lab1 in X:
 for l21 in X:
  for l22 in X:
   f=[{(1,):lab1},{(1,1):l21,(2,1):l22}]
   for rsize in (0,1):
    for R in itertools.combinations([(v,x) for v in verts for x in NZ], rsize):
     for tsize in (1,2):
      for T in itertools.combinations(verts,tsize):
       a=score(X,d,f,list(T),list(R),backend="exact",permissive=False)
       b=score(X,d,f,list(T),list(R),backend="exact",permissive=True)
       if a.get("errors"): continue
       if (not a["ok"]) and b["ok"]:
        if best is None or b["score"]<best[0]: best=(b["score"],f,list(T),list(R),a,b)
print("BEST SEPARATOR")
print(" score:", best[0], float(best[0]))
print(" f:", best[1]); print(" T:", best[2]); print(" R:", best[3])
print(" matching-suffix: ok=",best[4]["ok"]," m=",best[4]["m"]," r=",best[4]["r"]," n=",best[4]["n"]," t=",best[4]["t"], " score=",best[4]["score"])
print(" permissive     : ok=",best[5]["ok"]," m=",best[5]["m"]," r=",best[5]["r"]," n=",best[5]["n"]," t=",best[5]["t"], " score=",best[5]["score"])
G=ConstructibleGraph(X,d,best[1])
print(" edges matching :", G.edges(False))
print(" edges permissive:", G.edges(True))
print(" log matching   :", best[4]["log"])
print(" log permissive :", best[5]["log"])
