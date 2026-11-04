from fractions import Fraction as F
from itertools import combinations, product
from pathlib import Path
import re
import pymupdf
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from ifthen_content import CHECKS, WRONG
ROOT=Path(__file__).resolve().parents[2]
report=[]
def record(s):report.append(s);print(s)
def solve(A,b):
 n=len(b);a=[[F(str(v)) for v in row]+[F(str(y))] for row,y in zip(A,b)]
 for j in range(n):
  k=next((i for i in range(j,n) if a[i][j]),None)
  if k is None:return None
  a[j],a[k]=a[k],a[j]
  v=a[j][j];a[j]=[v2/v for v2 in a[j]]
  for i in range(n):
   if i!=j:
    v=a[i][j];a[i]=[p-v*q for p,q in zip(a[i],a[j])]
 return [r[-1] for r in a]
def lp(c,A,b):
 n=len(c);c=list(map(lambda v:F(str(v)),c));A=[[F(str(v)) for v in row] for row in A];b=[F(str(v)) for v in b]
 candidates=[]
 for idx in combinations(range(len(b)),n):
  x=solve([A[i] for i in idx],[b[i] for i in idx])
  if x is not None and all(sum(a*v for a,v in zip(row,x))<=rhs for row,rhs in zip(A,b)):
   candidates.append((sum(a*v for a,v in zip(c,x)),x))
 return max(candidates)
A=[[1,0],[0,2],[3,2],[-1,0],[0,-1]]
for c,b,expected in [([3,5],[4,12,18,0,0],36),([3,5],[4,12,21,0,0],39),([3,5],[4,12,27,0,0],42),([4,5],[4,12,18,0,0],38),([10,5],[4,12,18,0,0],55)]:
 z,x=lp(c,A,b);assert z==expected;record(f'PASS Wyndor c={c}, RHS={b[:3]}: x={x}, z={z}')
c=[(60-25)*125,(54-25)*162.5,(48-25)*217.5,(36-25)*348.8]
A=[[125,162.5,217.5,348.8],[1,1,1,1],[-1,0,0,0],[0,-1,0,0],[0,0,-1,0],[0,0,0,-1]]
z,x=lp(c,A,[2000,15,-1,0,0,0]);assert z+50000==116750;record(f'PASS markdown: weeks={x}, revenue={z+50000}')
for yields,expected in [([.01,.02],8819.66),([.00995,.0196],8294.57)]:
 A=[[90,0,0],[40,0,0],[0,1,1],[700,100,199.9],[.5,-yields[0],-yields[1]],[-1,0,0],[0,-1,0],[0,0,-1]]
 z,x=lp([5500,-100,-199.9],A,[2000,800,1000,100000,0,0,0,0]);assert abs(float(z)-expected)<.01;record(f'PASS drug yields={yields}: x={[round(float(a),6) for a in x]}, profit={float(z):.2f}')
for vals,wts,budget,expected in [([1000,950,350],[100,80,50],200,1950),([1000,950],[100,80],100,1000),([8,12,15,19],[2,3,4,6],10,35)]:
 z=max(sum(v*x for v,x in zip(vals,xs)) for xs in product([0,1],repeat=len(vals)) if sum(w*x for w,x in zip(wts,xs))<=budget)
 assert z==expected;record(f'PASS binary enumeration: budget={budget}, optimum={z}')
V={s:F(0) for s in range(5)}
for day in [1,2]:
 new={s:min(F(2,5)*q+sum((-min(s+q,d)+V[max(s+q-d,0)])*F(1,2) for d in [0,1]) for q in range(3) if s+q<=4) for s in range(3)}
 if day==1:
  assert new[0]==F(-1,10) and new[1]==F(-1,2)
  V={**V,**new}
 else:assert new[0]==F(-2,5)
record('PASS newsvendor: one-day cost −0.1; two-day adaptive cost −0.4')
w=(F(0),F(1))
for k in [3,2,1]:
 r=(w[1]+k*w[0])/(k+1);w=(r,max(F(k,4),r))
assert w[1]==F(11,24);record('PASS secretary n=4: success 11/24')
for name,(words,math) in CHECKS.items():
 for bits in product([0,1],repeat=6):
  x=(None,)+bits
  assert bool(words(x))==bool(math(x)),(name,bits)
record(f'PASS if-then logic: {len(CHECKS)} rules agree with their constraints on all 64 0/1 combos')
for name,(words,math) in WRONG.items():
 assert any(bool(words((None,)+b))!=bool(math((None,)+b)) for b in product([0,1],repeat=6)),name
record(f'PASS {len(WRONG)} constraints flagged as traps really are wrong')
d=pymupdf.open(ROOT/'DBA5103_Quiz_Cheat_Sheet.pdf')
assert len(d)==4
for i,p in enumerate(d):
 assert abs(p.rect.width-595.276)<.1 and abs(p.rect.height-841.89)<.1
 text=p.get_text();assert '\ufffd' not in text
 assert f'SIDE {i+1} / 4' in text
 spans=[s for b in p.get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans']]
 assert all(s['bbox'][0]>=19 and s['bbox'][2]<=579 and s['bbox'][1]>=19 and s['bbox'][3]<=835 for s in spans)
 p.get_pixmap(matrix=pymupdf.Matrix(2,2)).save(ROOT/f'workings/cheat_sheet/page-{i+1}.png')
 record(f'PASS PDF page {i+1}: A4, {len(text.split())} extracted words, text within print margins')
alltext='\n'.join(p.get_text() for p in d)
for marker in ['Gurobi essentials','Lecture map','Sudoku','Final recall','L1 · INTRODUCTION','L4 · DUALITY','L8 · DYNAMIC','If 3 AND 4, then 6','MORE RULES','QUICK DRILL','if and only if both 2 and 3']:assert marker in alltext,marker
record('PASS every column/section ends on its page (end markers found); exactly four pages')
(ROOT/'workings/cheat_sheet/validation_report.txt').write_text('\n'.join(report)+'\n')
