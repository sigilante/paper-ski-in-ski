import sys
sys.setrecursionlimit(100000)
# BCKW + I reducer, normal order
def sp(t):
    a=[]
    while isinstance(t,tuple): a.append(t[1]); t=t[0]
    a.reverse(); return t,a
def ap(h,args):
    for x in args: h=(h,x)
    return h
def hstep(t):
    h,a=sp(t); n=len(a)
    if h=='I' and n>=1: return ap(a[0],a[1:])
    if h=='K' and n>=2: return ap(a[0],a[2:])
    if h=='B' and n>=3: return ap((a[0],(a[1],a[2])),a[3:])
    if h=='C' and n>=3: return ap(((a[0],a[2]),a[1]),a[3:])
    if h=='W' and n>=2: return ap(((a[0],a[1]),a[1]),a[2:])
    return None
def nf(t,lim=2_000_000):
    c=[0]
    def go(t):
        while True:
            s=hstep(t)
            if s is None: break
            t=s; c[0]+=1
            if c[0]>lim: raise TimeoutError
        h,a=sp(t)
        return ap(h,[go(x) for x in a])
    return go(t)
def show(t):
    if isinstance(t,str): return t
    f,x=t
    return show(f)+(x if isinstance(x,str) else '('+show(x)+')')
def Wc(t):
    return (1 if t=='W' else 0) if isinstance(t,str) else Wc(t[0])+Wc(t[1])

two=('W',(('B',('C','B')),'I'))     # BCKW abstraction of Church 2, W=1
print("two =",show(two),"  W atoms =",Wc(two))
def church_str(n):
    b='x'
    for _ in range(n): b=('f',b)
    return show(b)
for name,term in [("2",two),("2 2",(two,two)),("2(2 2)",(two,(two,two))),("(2 2)2",((two,two),two))]:
    r=nf(((term,'f'),'x'))
    # which church numeral?
    s=show(r)
    k=s.count('f')
    print(f"  {name:8s} W atoms={Wc(term):2d}  normal form = f^{k} x   (matches Church {k}: {s==church_str(k)})")
