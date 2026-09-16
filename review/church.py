import sys; sys.setrecursionlimit(10**7)
sys.path.insert(0,'/Users/neal/ski-in-ski')
from collections import Counter
from aviary_kernel.terms import Atom, App, size as tree_atoms, free_vars
B,C,K,W,I=(Atom(n) for n in "BCKWI")
def A(*t):
    r=t[0]
    for x in t[1:]: r=App(r,x)
    return r
def abst_eta(x,body,ident=I):
    if isinstance(body,Atom): return ident if body.name==x else App(K,body)
    e,f=body.fn,body.arg
    fe,ff=x in free_vars(e), x in free_vars(f)
    if not fe and not ff: return App(K,body)
    if isinstance(f,Atom) and f.name==x and not fe: return e
    if not fe: return A(B,e,abst_eta(x,f,ident))
    if not ff: return A(C,abst_eta(x,e,ident),f)
    return A(W,A(B,App(C,abst_eta(x,e,ident)),abst_eta(x,f,ident)))
def abst_noeta(x,body,ident=I):
    if isinstance(body,Atom): return ident if body.name==x else App(K,body)
    e,f=body.fn,body.arg
    fe,ff=x in free_vars(e), x in free_vars(f)
    if not fe and not ff: return App(K,body)
    if not fe: return A(B,e,abst_noeta(x,f,ident))
    if not ff: return A(C,abst_noeta(x,e,ident),f)
    return A(W,A(B,App(C,abst_noeta(x,e,ident)),abst_noeta(x,f,ident)))
def cnt(t):
    st,c=[t],Counter()
    while st:
        z=st.pop()
        if isinstance(z,Atom): c[z.name]+=1
        else: st.append(z.fn); st.append(z.arg)
    return c
def church(n):
    b=Atom("x")
    for _ in range(n): b=App(Atom("f"),b)
    return b
IDENT_WK=A(W,K); IDENT_CKK=A(C,K,K)
print(" n | eta,I  | eta,WK | eta,CKK| noeta,I")
for n in range(0,9):
    row=[]
    for alg,ident in ((abst_eta,I),(abst_eta,IDENT_WK),(abst_eta,IDENT_CKK),(abst_noeta,I)):
        t=alg("f",alg("x",church(n),ident),ident)
        row.append(cnt(t)['W'])
    print(f"{n:2d} | "+" | ".join(f"W={w:<4d}" for w in row))
# also: Scott numerals used as actual fuel in tower_harness
print()
print("Scott numerals (what tower_harness actually uses as fuel):")
zero=abst_eta("z",abst_eta("s",Atom("z"),I),I)
suc =abst_eta("n",abst_eta("z",abst_eta("s",App(Atom("s"),Atom("n")),I),I),I)
print("  zero W =",cnt(zero)['W'],"  suc W =",cnt(suc)['W'])
