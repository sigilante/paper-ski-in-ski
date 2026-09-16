# confirm the five 6-atom terms genuinely have no WHNF: show head-reduction
# never terminates by exhibiting the reduct sequence's head-spine growth.
import sys
sys.setrecursionlimit(100000)
def sp(t):
    a=[]
    while isinstance(t,tuple): a.append(t[1]); t=t[0]
    a.reverse(); return t,a
def ap(h,args):
    for x in args: h=(h,x)
    return h
def st(t):
    h,a=sp(t); n=len(a)
    if h=='I' and n>=1: return ap(a[0],a[1:])
    if h=='K' and n>=2: return ap(a[0],a[2:])
    if h=='S' and n>=3: return ap(((a[0],a[2]),(a[1],a[2])),a[3:])
    return None
def show(t):
    if isinstance(t,str): return t
    f,x=t
    return show(f)+(x if isinstance(x,str) else '('+show(x)+')')
def P(s):
    # tiny parser for the printed forms
    i=[0]
    def atom():
        c=s[i[0]]
        if c=='(':
            i[0]+=1; t=expr()
            assert s[i[0]]==')'; i[0]+=1; return t
        i[0]+=1; return c
    def expr():
        t=atom()
        while i[0]<len(s) and s[i[0]]!=')':
            t=(t,atom())
        return t
    return expr()
for src in ['SII(SII)','S(SI)(SI)I','SSS(SI)I','SSI(SI)I','S(SS)SII']:
    t=P(src); seen={}
    n=0; mx=0
    while n<3000:
        k=show(t)
        if k in seen:
            print(f"  {src:12s} CYCLE: state repeats at step {n} (first seen {seen[k]})"); break
        seen[k]=n
        s2=st(t)
        if s2 is None:
            print(f"  {src:12s} reached WHNF at step {n}"); break
        t=s2; n+=1
        mx=max(mx,len(show(t)))
    else:
        print(f"  {src:12s} no WHNF in 3000 head steps; max printed length {mx} (strictly growing)")
