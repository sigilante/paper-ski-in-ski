import sys
sys.setrecursionlimit(1000000)

# term = str leaf, or App node object with cached size
class Ap:
    __slots__=('f','x','n')
    def __init__(s,f,x):
        s.f=f; s.x=x
        s.n=(1 if isinstance(f,str) else f.n)+(1 if isinstance(x,str) else x.n)
def sz(t): return 1 if isinstance(t,str) else t.n

def spine(t):
    args=[]
    while not isinstance(t,str):
        args.append(t.x); t=t.f
    args.reverse(); return t,args
def app(h,args):
    for a in args: h=Ap(h,a)
    return h
def hstep(t):
    h,args=spine(t)
    la=len(args)
    if h=='I' and la>=1: return app(args[0],args[1:])
    if h=='K' and la>=2: return app(args[0],args[2:])
    if h=='S' and la>=3:
        x,y,z=args[0],args[1],args[2]
        return app(Ap(Ap(x,z),Ap(y,z)),args[3:])
    return None

LIM=20000; MAXS=200000
def to_whnf(t):
    n=0
    while True:
        s=hstep(t)
        if s is None: return 'WHNF',n
        t=s; n+=1
        if n>LIM: return 'LIMIT',n
        if sz(t)>MAXS: return 'SIZE',n
def to_nf(t):
    cnt=[0]
    def go(t):
        while True:
            s=hstep(t)
            if s is None: break
            t=s; cnt[0]+=1
            if cnt[0]>LIM: raise TimeoutError
            if sz(t)>MAXS: raise MemoryError
        h,args=spine(t)
        return app(h,[go(a) for a in args])
    try:
        go(t); return 'NF',cnt[0]
    except TimeoutError: return 'LIMIT',cnt[0]
    except MemoryError: return 'SIZE',cnt[0]
    except RecursionError: return 'DEPTH',cnt[0]

def gen(n):
    if n==1:
        for c in 'SKI': yield c
        return
    for i in range(1,n):
        for l in list(gen(i)):
            for r in list(gen(n-i)):
                yield Ap(l,r)
def show(t):
    if isinstance(t,str): return t
    fs=show(t.f); xs=show(t.x) if isinstance(t.x,str) else '('+show(t.x)+')'
    return fs+xs

for n in range(1,7):
    tot=0; bnf=[]; bwh=[]
    for t in gen(n):
        tot+=1
        st,_=to_nf(t)
        if st!='NF': bnf.append((show(t),st))
        st2,_=to_whnf(t)
        if st2!='WHNF': bwh.append((show(t),st2))
    print(f"n={n}: {tot} terms | no NF: {len(bnf)} | no WHNF: {len(bwh)}",flush=True)
    for b in bnf[:30]: print("     noNF  ",b,flush=True)
    for b in bwh[:30]: print("     noWHNF",b,flush=True)
