#!/usr/bin/env python3
"""Follow-on to tower_harness.py: a nonlocal scry site for the SKI emulator,
analogous to Nock's opcode 12 (`.^`).

This file does not modify tower_harness.py. It loads that file's definitions
(same technique pipeline.py already uses) and adds a SEPARATE, parallel
5-symbol encoding {S, K, I, App, Scry} with its own spine-walker, rebuilder,
step function, and fueled loop -- all suffixed "Q" so nothing here can
collide with tower_harness.py's names or its T3 (Err) extension.

THE DESIGN, in one paragraph: `Scry` is a new *leaf* of the object language
(arity 1, like `I`), so `Scry p` is a redex once it has its one argument.
The interpreter's fueled loop `wfQ` is extended with a third parameter, an
ORACLE `E` -- a Scott-encoded partial function `path -> Maybe value` -- and
is applied as `wfQ E n <t>` instead of `whnfF n <t>`. When the spine walker
reaches `Scry p`, it applies `E` to `p`: `just v` splices `v` in as the new
head and reduction continues (a scry hit); `nothing` is NOT folded into the
existing `nothing`/`just` Maybe (that would silently conflate "genuinely
stuck" with "oracle had no answer" -- exactly the outcome-type-growth defect
PAPER.md S5 warns about). Instead the step function returns a THIRD outcome,
reusing tower_harness.py's own `stepped`/`done`/`errd` triple built for T3 --
a scry miss is `errd`, distinguishable from `done` (stuck) and from `rTime`
(fuel exhaustion) all the way out to the decoded result.

Usage:
    python3 scry_harness.py
"""
from __future__ import annotations
import sys, threading

sys.setrecursionlimit(10_000_000)

from aviary_kernel.terms import Atom, App, pretty, size as _tree_size
from aviary_kernel.abstraction import expand

# ---- load tower_harness.py's environment/definitions without running its
# ---- __main__ block (same technique pipeline.py uses). This also brings in
# ---- Err/T3's `stepped`, `done`, `errd`, `rVal`, `rErr`, `rTime`,
# ---- `decodeTag`, `nothing`, `just`, `cons`, `nil`, `Y`, `S`, `K`, `I`,
# ---- `env`, `A`, `a`, `v`, `D`, `AL`, `size`, `fast_reduce` -- all reused
# ---- below, unmodified.
_H = open("tower_harness.py").read().split("if __name__")[0]
exec(_H)

W = 70


def head(title):
    print(f"\n{title}\n" + "-" * W)


# ============================================================ encoding
# Alphabet {S, K, I, App, Scry}. Dispatch order (s, k, i, z, c): the first
# three are the ordinary 0-ary leaves, z is the 2-ary App slot, c is the new
# 1-ary Scry slot. Every leaf/app encoder must accept all 5 so any of them
# can stand in any dispatch position uniformly.
D("encSQ", ["s", "k", "i", "z", "c"], v("s"))
D("encKQ", ["s", "k", "i", "z", "c"], v("k"))
D("encIQ", ["s", "k", "i", "z", "c"], v("i"))
D("encAQ", ["t", "u", "s", "k", "i", "z", "c"], A(v("z"), v("t"), v("u")))
D("encCQ", ["s", "k", "i", "z", "c"], v("c"))
mkAppQ = a("encAQ")


def encQ(t):
    """Object term -> Scott-encoded {S,K,I,App,Scry} data, mirroring enc()/enc5()."""
    _LEAF = {"S": "encSQ", "K": "encKQ", "I": "encIQ", "Scry": "encCQ"}
    out, work = [], [(t, False)]
    while work:
        x, done = work.pop()
        if isinstance(x, Atom):
            out.append(a(_LEAF[x.name])); continue
        if not done:
            work.append((x, True)); work.append((x.arg, False)); work.append((x.fn, False))
        else:
            r = out.pop(); l = out.pop(); out.append(A(mkAppQ, l, r))
    return out.pop()


def Scry(path):
    """Object-level term: `Scry` applied to `path` (ordinary application)."""
    return App(Atom("Scry"), path)


# ======================================================= spine walker
# 4 leaves now (S, K, I, Scry), so the outward continuation tuple grows from
# (s,k,i) to (s,k,i,c). App recursion (spApp/cons/nil) is generic and is
# reused unmodified from tower_harness.py.
D("resSQ", ["acc", "s", "k", "i", "c"], A(v("s"), v("acc")))
D("resKQ", ["acc", "s", "k", "i", "c"], A(v("k"), v("acc")))
D("resIQ", ["acc", "s", "k", "i", "c"], A(v("i"), v("acc")))
D("resCQ", ["acc", "s", "k", "i", "c"], A(v("c"), v("acc")))
D("spGenQ", ["f", "m", "acc"], A(v("m"),
    A(a("resSQ"), v("acc")),
    A(a("resKQ"), v("acc")),
    A(a("resIQ"), v("acc")),
    A(a("spApp"), v("f"), v("acc")),   # reused unmodified from tower_harness.py
    A(a("resCQ"), v("acc"))))
AL("spQ", A(Y, a("spGenQ")))

# ============================================================ rebuild
# Needs its own version only because it must call mkAppQ (7-arg) rather
# than mkApp (6-arg); the recursion shape is identical to rb/rb5.
D("rbQ1", ["f", "h", "x", "xs"], A(v("f"), A(mkAppQ, v("h"), v("x")), v("xs")))
D("rbQGen", ["f", "h", "args"], A(v("args"), v("h"), A(a("rbQ1"), v("f"), v("h"))))
AL("rbQ", A(Y, a("rbQGen")))

# =============================================================== step
# S, K, I arms: identical in shape to tower_harness.py's stepS/stepK/stepI,
# but returning the 3-way stepped/done outcome (T3's types, reused
# unmodified) instead of just/nothing, and rebuilding via rbQ/mkAppQ.
D("stepIQ1", ["x", "rest"], A(a("stepped"), A(a("rbQ"), v("x"), v("rest"))))
D("stepIQ", ["args"], A(v("args"), a("done"), a("stepIQ1")))

D("stepKQ2", ["x", "y", "rest"], A(a("stepped"), A(a("rbQ"), v("x"), v("rest"))))
D("stepKQ1", ["x", "r"], A(v("r"), a("done"), A(a("stepKQ2"), v("x"))))
D("stepKQ", ["args"], A(v("args"), a("done"), a("stepKQ1")))

D("stepSQ3", ["x", "y", "z", "rest"], A(a("stepped"), A(a("rbQ"),
    A(mkAppQ, A(mkAppQ, v("x"), v("z")), A(mkAppQ, v("y"), v("z"))), v("rest"))))
D("stepSQ2", ["x", "y", "r2"], A(v("r2"), a("done"), A(a("stepSQ3"), v("x"), v("y"))))
D("stepSQ1", ["x", "r"], A(v("r"), a("done"), A(a("stepSQ2"), v("x"))))
D("stepSQ", ["args"], A(v("args"), a("done"), a("stepSQ1")))

# Scry arm: the new content. `e` is the oracle, threaded in as an explicit
# argument (not baked into a chosen interpreter variant, unlike T3's
# errArmAbs/errArmOmg). `e p` is a Maybe: `just v` -> stepped (splice v in,
# rebuild with the remaining args); `nothing` -> errd (a MISS, kept
# distinct from `done`/stuck -- see module docstring).
D("scHit", ["rest", "v"], A(a("stepped"), A(a("rbQ"), v("v"), v("rest"))))
D("stepScQ1", ["e", "p", "rest"], A(v("e"), v("p"), a("errd"), A(a("scHit"), v("rest"))))
D("stepScQ", ["e", "args"], A(v("args"), a("done"), A(a("stepScQ1"), v("e"))))

D("stepQE", ["e", "m"], A(a("spQ"), v("m"), a("nil"),
    a("stepSQ"), a("stepKQ"), a("stepIQ"), A(a("stepScQ"), v("e"))))

# ========================================================== fueled loop
# wfQ E n <t> -- same shape as whnfF n <t>, plus a threaded oracle E and a
# 3-way outcome (rVal/rErr/rTime, all reused unmodified from T3) instead of
# the 2-way (WHNF value / TIMEOUT) whnfF reports. rVal = reached WHNF.
# rErr = a scry miss was hit before WHNF. rTime = fuel ran out first.
D("wfQ1", ["e", "w", "m", "n2"], A(a("stepQE"), v("e"), v("m"),
    A(v("w"), v("e"), v("n2")),
    A(a("rVal"), v("m")),
    a("rErr")))
D("wfQGen", ["w", "e", "n", "m"], A(v("n"), a("rTime"), A(a("wfQ1"), v("e"), v("w"), v("m"))))
AL("wfQ", A(Y, a("wfQGen")))

WQ = expand(a("wfQ"), env)

# ================================================================ oracles
# Three test oracles: always hit (identity echo), always miss, and a
# path-dependent one built from spQ -- inspecting a path via the same
# spine-walker the interpreter itself uses, to show spQ is reusable as a
# general term-inspection primitive, not just interpreter-internal.
D("oracleAlways", ["p"], A(a("just"), v("p")))
D("oracleNever", ["p"], a("nothing"))

D("oracleIfKk", ["acc"], A(a("just"), a("encIQ")))
D("oracleIfK", ["p"], A(a("spQ"), v("p"), a("nil"),
    A(K, a("nothing")),      # head S -> miss
    a("oracleIfKk"),          # head K -> hit, resolves to <I>
    A(K, a("nothing")),      # head I -> miss
    A(K, a("nothing"))))     # head Scry -> miss

OA = expand(a("oracleAlways"), env)
ON = expand(a("oracleNever"), env)
OK_ = expand(a("oracleIfK"), env)


# =================================================================== run
def run(oracle_term, obj_term, fuel):
    """Returns (tag, payload_or_None). tag in {VAL, ERR, TIME, <status>}."""
    q = encQ(obj_term)
    r = fast_reduce(A(WQ, oracle_term, natP(fuel), q), env, max_steps=50_000_000)
    if r.status.value != "whnf":
        return f"<{r.status.value} within {fuel} steps>", None
    unwrapped = fast_reduce(A(r.term, Atom("C1"), Atom("C2"), Atom("C3")),
                             env, max_steps=200_000)
    txt = pretty(unwrapped.term)
    if txt.startswith("C1 "):
        return "VAL", unwrapped.term.arg   # payload, still Scott-encoded
    if txt == "C2":
        return "ERR", None
    if txt == "C3":
        return "TIME", None
    return f"<unrecognised outcome: {txt}>", None


_SLOTS = "skizc"  # dispatch order used throughout: s, k, i, z(app), c(scry)


def verify(oracle_term, obj_term, fuel, expected):
    """Behaviorally check a VAL payload against a fresh marker probe, rather
    than trusting the raw combinator syntax (which is algorithm-dependent
    and easy to mis-derive by hand -- see the design note this caught).
    `expected` is either a leaf slot 's'/'k'/'i'/'c' the payload should
    select, or the literal string 'ERR'/'TIME' for non-value outcomes.
    """
    tag, payload = run(oracle_term, obj_term, fuel)
    if expected in ("ERR", "TIME"):
        ok = tag == expected
        return ok, tag
    if tag != "VAL":
        return False, tag
    Xs = [Atom(f"X{i}") for i in range(1, 6)]
    probe = fast_reduce(A(payload, *Xs), env, whnf_only=False, max_steps=200_000)
    got = pretty(probe.term)
    want = "X" + str(_SLOTS.index(expected) + 1)
    return got == want, got


def show(label, oracle_term, obj_term, fuel, expected):
    ok, detail = verify(oracle_term, obj_term, fuel, expected)
    mark = "OK  " if ok else "*** FAIL ***"
    print(f"  {mark}  {label:<62s} ({detail})")
    return ok


def main():
    all_ok = True

    head("SANITY: no Scry present -- must match tower_harness.py's own results")
    base_term = App(I, K)
    base = fast_reduce(A(WP, natP(3), encP(base_term)), env, max_steps=50_000)
    print(f"  base whnfF 3 <I K> : {base.status.value}, {base.steps} steps"
          f" (whnf, 340 steps expected)")
    all_ok &= show("wfQ oracleAlways 3 <I K>  -> selects k-slot (value K)",
                    OA, base_term, 3, "k")
    all_ok &= show("wfQ oracleNever  3 <I K>  -> selects k-slot (oracle unused)",
                    ON, base_term, 3, "k")

    head("SCRY HIT: `I (Scry K)` -- I fires first, exposing Scry K to WHNF,")
    print("  then the oracle resolves it. (`K (Scry I)` would NOT test this --")
    print("  K's laziness means it never reaches its 2nd argument; see below.)")
    t = App(I, Scry(K))
    all_ok &= show("I (Scry K) under oracleAlways -> echoes path, selects k-slot",
                    OA, t, 10, "k")
    all_ok &= show("I (Scry K) under oracleNever  -> ERR",
                    ON, t, 10, "ERR")

    head("SCRY MISS is distinguishable from stuck AND from fuel exhaustion")
    all_ok &= show("Scry K (bare, saturated) under oracleNever  -> ERR (miss)",
                    ON, Scry(K), 10, "ERR")
    all_ok &= show("Scry K (bare, saturated) under oracleAlways -> selects k-slot (hit)",
                    OA, Scry(K), 10, "k")
    all_ok &= show("Scry (bare, unsaturated) under oracleAlways -> stuck/`done`,",
                    OA, Atom("Scry"), 10, "c")
    print("    (no path yet to consult -> selects its own c-slot, same as any")
    print("     other under-applied leaf; not a miss, not a hit, just stuck)")

    head("LAZINESS: a scry site inside a discarded K-argument is never consulted")
    all_ok &= show("K K (Scry K) under oracleNever -> reduces to K without ever",
                    ON, App(App(K, K), Scry(K)), 10, "k")
    print("    (K's rule discards its 2nd arg unevaluated -- same mechanism as")
    print("     `K I Omega` surviving under the base whnfF; a miss inside a")
    print("     never-forced branch cannot be observed, oracle or not)")

    head("PATH-DEPENDENT ORACLE: oracleIfK inspects the path via spQ itself")
    all_ok &= show("Scry K       under oracleIfK -> hit,  resolves to <I>",
                    OK_, Scry(K), 10, "i")
    all_ok &= show("Scry (S K K) under oracleIfK -> miss (head is S, not K)",
                    OK_, Scry(App(App(S, K), K)), 10, "ERR")

    head("FUEL EXHAUSTION still reports separately from a scry miss")
    omega = App(App(App(S, I), I), App(App(S, I), I))
    all_ok &= show("Omega under oracleAlways, fuel=5 -> TIME (never even a candidate",
                    OA, omega, 5, "TIME")
    print("    for a scry site -- distinguishes 'ran out of fuel' from 'oracle")
    print("     had no answer', which a 2-way Maybe could not keep apart)")

    print(f"\n  emulator (wfQ): {_tree_size(WQ):,} tree-atoms, basis {{S,K,I}}")
    print(f"\n  {'ALL CHECKS PASSED' if all_ok else '*** SOME CHECKS FAILED ***'}")
    return all_ok


if __name__ == "__main__":
    threading.stack_size(1024 * 1024 * 1024)
    box = {}
    th = threading.Thread(target=lambda: box.update(ok=main()))
    th.start(); th.join()
    sys.exit(0 if box.get("ok") else 1)
