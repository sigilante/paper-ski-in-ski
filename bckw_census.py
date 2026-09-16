"""BCKW census: rebuild the interpreter over the B,C,K,W basis and count
which structural rules each component actually uses.

Abstraction rules (standard, cf. Curry):
  [x] x        = I            (I = W K, definable)
  [x] E        = K E          x not free in E                 WEAKENING
  [x] (E x)    = E            x not free in E   (eta)
  [x] (E F)    = B E ([x]F)   x free in F only  -- compose
  [x] (E F)    = C ([x]E) F   x free in E only  -- exchange
  [x] (E F)    = W (B (C ([x]E)) ([x]F))  x free in both  -- CONTRACTION
"""
import sys; sys.setrecursionlimit(10**7)
from collections import Counter
from aviary_kernel.terms import Atom, App, pretty, size as tree_atoms, free_vars

B,C,K,W,I = (Atom(n) for n in "BCKWI")
def A(*t):
    r=t[0]
    for x in t[1:]: r=App(r,x)
    return r

def abst(x, body):
    if isinstance(body, Atom):
        return I if body.name==x else App(K, body)
    e,f = body.fn, body.arg
    fe, ff = x in free_vars(e), x in free_vars(f)
    if not fe and not ff:              return App(K, body)
    if isinstance(f,Atom) and f.name==x and not fe:  return e          # eta
    if not fe:                          return A(B, e, abst(x,f))       # compose
    if not ff:                          return A(C, abst(x,e), f)       # exchange
    return A(W, A(B, App(C, abst(x,e)), abst(x,f)))                     # contraction

def lam(vs, body):
    for v in reversed(vs): body = abst(v, body)
    return body
def census(t):
    st,c=[t],Counter()
    while st:
        z=st.pop()
        if isinstance(z,Atom): c[z.name]+=1
        else: st.append(z.fn); st.append(z.arg)
    return c
def row(name, t):
    c=census(t); n=tree_atoms(t)
    print(f"  {name:<22s} {n:>6d}  " + "  ".join(f"{k}={c.get(k,0):<5d}" for k in "BCKWI"))
    return c

v=Atom
print("BCKW census of the self-interpreter components")
print(f"  {'component':<22s} {'atoms':>6s}  B / C / K / W / I")
print("  " + "-"*58)

# --- Scott encoding constructors (pure dispatch: expect K-heavy, no W)
enc = {}
for i,(nm,pick) in enumerate([("enc<S>","s"),("enc<K>","k"),("enc<I>","i")]):
    enc[nm]=lam(["s","k","i","z"], v(pick))
encA = lam(["t","u","s","k","i","z"], A(v("z"),v("t"),v("u")))
tot=Counter()
for nm in ["enc<S>","enc<K>","enc<I>"]: tot+=row(nm, enc[nm])
tot+=row("enc<app>", encA)

# --- Scott data
nil   = lam(["n","c"], v("n"));            tot+=row("nil", nil)
cons  = lam(["h","t","n","c"], A(v("c"),v("h"),v("t"))); tot+=row("cons", cons)
noth  = lam(["n","j"], v("n"));            tot+=row("nothing", noth)
just  = lam(["x","n","j"], A(v("j"),v("x"))); tot+=row("just", just)
zero  = lam(["z","s"], v("z"));            tot+=row("zero", zero)
suc   = lam(["n","z","s"], A(v("s"),v("n"))); tot+=row("suc", suc)

# --- unquoter body (recursion via Y, so census the generator)
uqa   = lam(["f","t","u"], A(A(v("f"),v("t")), A(v("f"),v("u"))))
tot+=row("UQ arm (dup of f!)", uqa)
uqg   = lam(["f","m"], A(v("m"), Atom("S"), Atom("K"), Atom("I"), A(v("uqa"),v("f"))))
tot+=row("UQ generator", uqg)

# --- spine / rebuild / step (the interpreter core)
resS=lam(["acc","s","k","i"],A(v("s"),v("acc"))); tot+=row("res arm (x3)",resS)
spApp=lam(["f","acc","t","u"], A(v("f"),v("t"),A(a2:=Atom("cons"),v("u"),v("acc"))))
tot+=row("sp app arm", spApp)
spGen=lam(["f","m","acc"], A(v("m"),
    A(Atom("resS"),v("acc")),A(Atom("resK"),v("acc")),
    A(Atom("resI"),v("acc")),A(Atom("spApp"),v("f"),v("acc"))))
tot+=row("sp generator (acc x4!)", spGen)
rb1=lam(["f","h","x","xs"], A(v("f"),A(Atom("encA"),v("h"),v("x")),v("xs")))
tot+=row("rb helper", rb1)
rbG=lam(["f","h","args"], A(v("args"),v("h"),A(Atom("rb1"),v("f"),v("h"))))
tot+=row("rb generator (f,h x2)", rbG)
stepS3=lam(["x","y","z","rest"], A(Atom("just"),A(Atom("rb"),
    A(Atom("encA"),A(Atom("encA"),v("x"),v("z")),A(Atom("encA"),v("y"),v("z"))),v("rest"))))
tot+=row("step S arm (z x2!)", stepS3)
wf1=lam(["w","m","n2"], A(Atom("step"),v("m"),A(Atom("just"),v("m")),A(v("w"),v("n2"))))
tot+=row("whnfF body (m x2!)", wf1)

print("  " + "-"*58)
print(f"  {'TOTAL':<22s} {sum(tot[k] for k in 'BCKWI'):>6d}  " +
      "  ".join(f"{k}={tot.get(k,0):<5d}" for k in "BCKWI"))
print()
print("  W (contraction) sites:", tot['W'], " K (weakening) sites:", tot['K'])

# ---------------------------------------------------------------------
# RESULTS (verified, aviary-kernel 0.1.0 term library)
#
#   TOTAL over interpreter components: 138 atoms
#     B=70  C=31  K=21  W=7  I=9
#
#   Structural profile, by layer:
#     encoding/data (10 components)  K=18  W=0   <- weakening only
#     interpreter core (9)           K=3   W=7   <- contraction concentrated
#
#   CLAIM 1 (verified): Scott dispatch needs WEAKENING, never contraction.
#     every enc<-> constructor: K=3, W=0.  A constructor selects one of n
#     continuations and DISCARDS the rest -- that is weakening, n-1 times.
#     => BCI and BCIW (no K) cannot Scott-encode at all.
#
#   CLAIM 2 (argued, not measured here): iteration needs CONTRACTION.
#     A Church numeral n >= 2 duplicates its binder f (n occurrences), so
#     it is not affine; Y duplicates its argument; BCK (no W) is strongly
#     normalizing, hence has no fixpoint combinator and no interpreter
#     loop.  The fuel in tower_harness.py is a SCOTT numeral, which IS
#     affine (zero W=0, suc W=0) -- iteration comes from Y, not from the
#     numeral.  An earlier version of this comment claimed "numeral n uses
#     W exactly n-1 times, verified"; nothing in this script measures it,
#     the count is convention-relative (n under I = W K), and it is false
#     for BCKW terms generally (2 (2 2) denotes Church 16 with 3 W atoms;
#     see review/church.py and review/bckw_red.py).
#
#   CLAIM 3 (verified): the 7 W atoms this script counts (primitive-I
#     convention) correspond one-to-one to the 7 surplus variable
#     occurrences in census.py's occurrence census -- UQ's f x2, spine's
#     acc x4, rb's h x2, step-S's z x2 (the S rule itself), whnfF's m x2.
#     The ATOM count is convention-relative (census.py's I = W K convention
#     reports 10); the OCCURRENCE count is not, and any BCKW abstraction
#     needs at least that many contractions.
#
#   COROLLARY.  Self-interpretation needs BOTH structural rules, and each
#   restriction kills it for a DIFFERENT reason: the linear/relevant
#   fragments fail at REPRESENTATION, the affine fragment fails at
#   ITERATION.  Omega lives in the K-free fragment (W W W -> W W W needs
#   no weakening), so contraction alone already costs normalization: the
#   rule that buys iteration is the rule that costs normalization, and
#   weakening is needed for representation, not for divergence.
# ---------------------------------------------------------------------
