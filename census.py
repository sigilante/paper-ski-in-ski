#!/usr/bin/env python3
"""Structural census of a combinatory self-interpreter.

TWO MEASUREMENTS, and the distinction matters:

  1. OCCURRENCE CENSUS (primary, invariant).  Measures the LAMBDA term.
     A term requires contraction in ANY BCKW abstraction iff some bound
     variable occurs more than once; it requires weakening iff some bound
     variable occurs zero times.  These are properties of the term, so
     the result is independent of the abstraction algorithm AND of how
     the identity is derived (W K, C K K, or primitive I).  This is the
     measurement to cite.

  2. ATOM CENSUS (secondary, algorithm-relative).  Measures the
     COMBINATOR term after abstraction.  Useful for comparing what each
     basis costs, but the numbers move if the abstraction algorithm or
     the identity encoding changes.  Label it as such.

Requires: pip install aviary-kernel==0.1.0
"""
from __future__ import annotations
import sys
from collections import Counter

sys.setrecursionlimit(10_000_000)

from aviary_kernel.terms import Atom, App, pretty, free_vars, size as tree_atoms
from aviary_kernel.abstraction import bracket_abstract
from aviary_kernel.environment import Environment
from aviary_kernel.reduce import reduce

B, C, K, W, S, I = (Atom(n) for n in "BCKWSI")
SKI_BASIS = frozenset("SKI")
BCKW_BASIS = frozenset("BCKW")


def A(*ts):
    r = ts[0]
    for t in ts[1:]:
        r = App(r, t)
    return r


v = Atom
env = Environment()

# --------------------------------------------------------------- purity

class ImpureTerm(Exception):
    pass


def check_purity(term, basis, *, allow=frozenset()):
    """Every atom must lie in `basis` (or in `allow`, for free names).

    A census over a mixed-basis term is meaningless: S bundles
    composition, exchange and contraction, so counting W in a term that
    also contains S understates contraction.  Refuse rather than report.
    """
    seen, stack = set(), [term]
    while stack:
        x = stack.pop()
        if isinstance(x, Atom):
            seen.add(x.name)
        else:
            stack.append(x.fn)
            stack.append(x.arg)
    bad = seen - set(basis) - set(allow)
    if bad:
        raise ImpureTerm(
            f"atoms {sorted(bad)} outside basis {sorted(basis)}"
        )
    return True


# ------------------------------------------------- abstraction (BCKW)
# Identity: W K, Curry's classical derivation and the aviary-kernel
# convention for --basis=bckw.  C K K is also an identity and is
# contraction-free; the choice shifts the ATOM census but cannot affect
# the OCCURRENCE census, which is why the latter is primary.
IDENT_WK = A(W, K)
IDENT_CKK = A(C, K, K)


def bckw_abstract(x, body, ident=IDENT_WK):
    if isinstance(body, Atom):
        return ident if body.name == x else App(K, body)
    e, f = body.fn, body.arg
    fe, ff = x in free_vars(e), x in free_vars(f)
    if not fe and not ff:
        return App(K, body)                                  # weakening
    if isinstance(f, Atom) and f.name == x and not fe:
        return e                                             # eta
    if not fe:
        return A(B, e, bckw_abstract(x, f, ident))           # compose
    if not ff:
        return A(C, bckw_abstract(x, e, ident), f)           # exchange
    return A(W, A(B, App(C, bckw_abstract(x, e, ident)),
                  bckw_abstract(x, f, ident)))               # contraction


def lam(vs, body, alg):
    for u in reversed(vs):
        body = alg(u, body)
    return body


# ------------------------------------------------------- the components
# (name, binders, body).  Free atoms name other combinators.
ENCODING = [
    ("enc<S>",   ["s", "k", "i", "z"], v("s")),
    ("enc<K>",   ["s", "k", "i", "z"], v("k")),
    ("enc<I>",   ["s", "k", "i", "z"], v("i")),
    ("enc<app>", ["t", "u", "s", "k", "i", "z"], A(v("z"), v("t"), v("u"))),
    ("nil",      ["n", "c"], v("n")),
    ("cons",     ["h", "t", "n", "c"], A(v("c"), v("h"), v("t"))),
    ("nothing",  ["n", "j"], v("n")),
    ("just",     ["x", "n", "j"], A(v("j"), v("x"))),
    ("zero",     ["z", "s"], v("z")),
    ("suc",      ["n", "z", "s"], A(v("s"), v("n"))),
]

CORE = [
    ("UQ arm",       ["f", "t", "u"], A(A(v("f"), v("t")), A(v("f"), v("u")))),
    ("res arm",      ["acc", "s", "k", "i"], A(v("s"), v("acc"))),
    ("sp app arm",   ["f", "acc", "t", "u"],
     A(v("f"), v("t"), A(Atom("cons"), v("u"), v("acc")))),
    ("sp generator", ["f", "m", "acc"],
     A(v("m"), A(Atom("rS"), v("acc")), A(Atom("rK"), v("acc")),
       A(Atom("rI"), v("acc")), A(Atom("spA"), v("f"), v("acc")))),
    ("rb helper",    ["f", "h", "x", "xs"],
     A(v("f"), A(Atom("eA"), v("h"), v("x")), v("xs"))),
    ("rb generator", ["f", "h", "args"],
     A(v("args"), v("h"), A(Atom("rb1"), v("f"), v("h")))),
    ("step S arm",   ["x", "y", "z", "rest"],
     A(Atom("just"), A(Atom("rb"),
       A(Atom("eA"), A(Atom("eA"), v("x"), v("z")),
         A(Atom("eA"), v("y"), v("z"))), v("rest")))),
    ("whnfF body",   ["w", "m", "n2"],
     A(Atom("step"), v("m"), A(Atom("just"), v("m")), A(v("w"), v("n2")))),
]


def occurrences(body):
    st, c = [body], Counter()
    while st:
        x = st.pop()
        if isinstance(x, Atom):
            c[x.name] += 1
        else:
            st.append(x.fn)
            st.append(x.arg)
    return c


# ---------------------------------------------------------------- report

def occurrence_census():
    print("1. OCCURRENCE CENSUS  (invariant: property of the lambda term)")
    print("   needs W iff some binder occurs >1;  needs K iff some binder occurs 0\n")
    totals = {}
    for label, group in (("ENCODING / DATA", ENCODING), ("INTERPRETER CORE", CORE)):
        print(f"   -- {label}")
        affine = 0
        for nm, vs, body in group:
            c = occurrences(body)
            counts = [c.get(u, 0) for u in vs]
            mx = max(counts + [0])
            dup = [f"{u}x{c[u]}" for u in vs if c.get(u, 0) > 1]
            drop = sum(1 for n in counts if n == 0)
            affine += (mx <= 1)
            verdict = "affine (no W)" if mx <= 1 else "needs W: " + " ".join(dup)
            print(f"   {nm:<15s} max-occ={mx}  discards={drop}  {verdict}")
        totals[label] = (affine, len(group))
        print(f"   => {affine}/{len(group)} affine\n")
    return totals


def atom_census():
    print("2. ATOM CENSUS  (algorithm-relative: depends on abstraction + identity)")
    print("   BCKW identity = W K (Curry / aviary-kernel convention)\n")
    print(f"   {'component':<15s} {'SKI':>5s} | {'BCKW':>5s}   B     C     K     W")
    grand = {"SKI": 0, "BCKW": 0}
    for label, group in (("ENCODING / DATA", ENCODING), ("INTERPRETER CORE", CORE)):
        print(f"   -- {label}")
        sub = Counter()
        sski = sbck = 0
        for nm, vs, body in group:
            t_ski = lam(vs, body, bracket_abstract)
            t_bck = lam(vs, body, bckw_abstract)
            c = occurrences(t_bck)
            sub += c
            sski += tree_atoms(t_ski)
            sbck += tree_atoms(t_bck)
            print(f"   {nm:<15s} {tree_atoms(t_ski):>5d} | {tree_atoms(t_bck):>5d}   "
                  + "  ".join(f"{c.get(k, 0):<4d}" for k in "BCKW"))
        grand["SKI"] += sski
        grand["BCKW"] += sbck
        print(f"   {'subtotal':<15s} {sski:>5d} | {sbck:>5d}   "
              + "  ".join(f"{sub.get(k, 0):<4d}" for k in "BCKW"))
    print(f"\n   {'TOTAL':<15s} {grand['SKI']:>5d} | {grand['BCKW']:>5d}")
    return grand


def differential_check():
    """The atom census is only meaningful if both abstractions agree."""
    print("3. DIFFERENTIAL CHECK  (SKI vs BCKW abstraction, free-variable args)")
    args = [v("p"), v("q"), v("r"), v("s0"), v("t0"), v("u0")]

    def nf(t):
        return pretty(reduce(t, env, max_steps=200_000, max_size=10 ** 7).term)

    bad = 0
    for nm, vs, body in ENCODING + CORE:
        ap = args[:len(vs)]
        a1 = nf(A(lam(vs, body, bracket_abstract), *ap))
        a2 = nf(A(lam(vs, body, bckw_abstract), *ap))
        if a1 != a2:
            bad += 1
            print(f"   {nm:<15s} MISMATCH  {a1}  vs  {a2}")
    n = len(ENCODING) + len(CORE)
    print(f"   {n - bad}/{n} agree" + ("" if bad == 0 else "  *** FAILURE ***"))
    return bad == 0


def purity_check():
    print("4. PURITY GUARD  (a census over a mixed basis is meaningless)")
    ok = True
    pure = lam(["x", "y", "z"], A(v("x"), v("z"), A(v("y"), v("z"))), bckw_abstract)
    try:
        check_purity(pure, BCKW_BASIS)
        print("   pure BCKW term          accepted   OK")
    except ImpureTerm as e:
        ok = False
        print(f"   pure BCKW term          REJECTED   *** {e} ***")
    mixed = App(pure, S)                       # negative control
    try:
        check_purity(mixed, BCKW_BASIS)
        ok = False
        print("   mixed term (contains S) accepted   *** GUARD FAILED ***")
    except ImpureTerm as e:
        print(f"   mixed term (contains S) rejected   OK  ({e})")
    return ok


if __name__ == "__main__":
    print(__doc__.split("Requires:")[0].rstrip() + "\n")
    occurrence_census()
    atom_census()
    print()
    d = differential_check()
    print()
    p = purity_check()
    print()
    sys.exit(0 if (d and p) else 1)

# ---------------------------------------------------------------------
# VERIFIED RESULTS  (aviary-kernel 0.1.0)
#
# 1. OCCURRENCE CENSUS -- invariant, cite this
#      encoding / data     10/10 affine   (no binder occurs twice)
#      interpreter core     3/8  affine   contraction at:
#                                           UQ arm        f x2
#                                           sp generator  acc x4
#                                           rb generator  h x2
#                                           step S arm    z x2
#                                           whnfF body    m x2
#
# 2. ATOM CENSUS -- algorithm-relative, BCKW identity = W K
#      encoding / data     SKI  88  |  BCKW  47   (B15 C6  K22 W4)
#      interpreter core    SKI 161  |  BCKW 104   (B54 C21 K5  W10)
#      TOTAL               SKI 249  |  BCKW 151
#
#    NOTE the two censuses disagree on the encoding layer: occurrence
#    says 10/10 affine, atoms say W=4.  That gap IS the W K identity --
#    every [x]x contributes a contraction the source term never asked
#    for.  Deriving I as C K K closes it (encoding W=0) at +8 atoms.
#    The disagreement is why the occurrence census is primary.
#
# 3. DIFFERENTIAL CHECK    18/18 SKI and BCKW abstractions agree
# 4. PURITY GUARD          accepts pure BCKW, rejects a term containing S
#
#    Negative controls (both exit 1, verified):
#      swap the compose/exchange cases  -> 4/18 agree, FAILURE
#      disable the purity guard         -> GUARD FAILED
#
# FINDING.  The representation layer is affine: it lives in BCK.
# Contraction appears only in the interpreter core.  Self-interpretation
# needs both structural rules, and each restriction kills it differently
# -- BCI/BCIW cannot Scott-encode (no weakening, hence no dispatch);
# BCK cannot iterate (no contraction: BCK is strongly normalizing, so no
# fixpoint combinator and no loop).  Note the asymmetry: Omega needs
# contraction only -- (SII)(SII) contains no K, and W W W -> W W W -- so
# contraction alone already costs normalization; weakening is needed for
# representation, not for divergence.
# ---------------------------------------------------------------------
