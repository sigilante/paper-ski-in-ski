#!/usr/bin/env python3
"""SKI-emulator-in-SKI: tower harness.

Builds the pure-{S,K,I} fueled normal-order emulator (618 atoms) and runs
staged self-emulation targets.  Requires: pip install aviary-kernel

    python3 tower_harness.py --target t0        # baseline, seconds
    python3 tower_harness.py --target t1        # emulator over unquoter
    python3 tower_harness.py --target t2        # emulator over emulator (the prize)
    python3 tower_harness.py --target all --fuel 200000000

The stock aviary reducer computes term_size(full_term(...)) on EVERY
contraction -- O(n) per step, so O(n*steps) overall.  At tower scale the
encoded inner term is ~30k atoms and this dominates completely.  We
sample the size check every SIZE_CHECK_EVERY steps instead; the guard
still fires, just up to N steps late.  This is the single change that
makes t2 reachable.
"""
from __future__ import annotations
import argparse, time
from aviary_kernel.environment import Environment
from aviary_kernel.terms import Atom, App, pretty, size as _tree_size, apply as _apply

def size(term):
    """DAG-aware node count.  Reduction SHARES subterms (S x y z -> x z (y z)
    duplicates z by reference), so a compact DAG can denote an exponentially
    large tree.  The stock tree-walking size() therefore explodes on emulator
    output -- it was ~200,000x the cost of the reduction itself."""
    seen, stack, n = set(), [term], 0
    while stack:
        x = stack.pop()
        if id(x) in seen: continue
        seen.add(id(x)); n += 1
        if isinstance(x, App):
            stack.append(x.fn); stack.append(x.arg)
    return n
from aviary_kernel.reduce import Status, _decompose, _try_contract, ReduceResult
from aviary_kernel.abstraction import expand

SIZE_CHECK_EVERY = 512


def fast_reduce(term, env, *, whnf_only=True, max_steps=10**8, max_size=10**9):
    """reduce() with the size check sampled rather than per-step."""
    steps = 0
    stack = []

    def full_term(head, args):
        result = _apply(head, *args)
        for fr in reversed(stack):
            remaining = fr.todo[len(fr.done) + 1:]
            result = _apply(fr.head, *(fr.done + [result] + remaining))
        return result

    head, args = _decompose(term)
    while True:
        while True:
            if steps >= max_steps:
                return ReduceResult(full_term(head, args), steps, Status.FUEL, [])
            contraction = _try_contract(head, args, env)
            if contraction is None:
                break
            head, args, _ = contraction
            steps += 1
            if steps % 2_000_000 == 0 and steps:
                print(f"      ... {steps:,} contractions", flush=True)
            if steps % SIZE_CHECK_EVERY == 0:
                if size(full_term(head, args)) > max_size:
                    return ReduceResult(full_term(head, args), steps, Status.SIZE, [])
        if whnf_only and not stack:
            return ReduceResult(_apply(head, *args), steps, Status.WHNF, [])
        if args:
            from aviary_kernel.reduce import _Frame
            stack.append(_Frame(head=head, done=[], todo=list(args)))
            head, args = _decompose(args[0])
            continue
        result = head
        while stack:
            fr = stack[-1]
            fr.done.append(result)
            remaining = fr.todo[len(fr.done):]
            if remaining:
                head, args = _decompose(remaining[0])
                break
            built = _apply(fr.head, *fr.done)
            stack.pop()
            result = built
        else:
            return ReduceResult(result, steps, Status.NORMAL, [])


# ----------------------------------------------------------------- build
env = Environment()
def A(*ts):
    r = ts[0]
    for t in ts[1:]:
        r = App(r, t)
    return r
a = v = Atom
def D(n, f, b): env.define_rule(n, tuple(f), b); return a(n)
def AL(n, b):   env.define_alias(n, b);          return a(n)
S, K, I, Y = a("S"), a("K"), a("I"), a("Y")

D("encS", ["s","k","i","z"], v("s")); D("encK", ["s","k","i","z"], v("k"))
D("encI", ["s","k","i","z"], v("i"))
D("encA", ["t","u","s","k","i","z"], A(v("z"), v("t"), v("u")))
mkApp = a("encA")
D("nil", ["n","c"], v("n")); D("cons", ["h","t","n","c"], A(v("c"), v("h"), v("t")))
D("nothing", ["n","j"], v("n")); D("just", ["x","n","j"], A(v("j"), v("x")))
D("zero", ["z","sc"], v("z")); D("suc", ["n","z","sc"], A(v("sc"), v("n")))

def enc(t):
    _LEAF = {"S":"encS","K":"encK","I":"encI"}
    out, work = [], [(t, False)]
    while work:
        x, done = work.pop()
        if isinstance(x, Atom):
            out.append(a(_LEAF[x.name])); continue
        if not done:
            work.append((x, True)); work.append((x.arg, False)); work.append((x.fn, False))
        else:
            r = out.pop(); l = out.pop(); out.append(A(mkApp, l, r))
    return out.pop()
def nat(k):
    t = a("zero")
    for _ in range(k):
        t = A(a("suc"), t)
    return t

# recursion via Y so everything expands to closed S/K/I
D("resS", ["acc","s","k","i"], A(v("s"), v("acc")))
D("resK", ["acc","s","k","i"], A(v("k"), v("acc")))
D("resI", ["acc","s","k","i"], A(v("i"), v("acc")))
D("spApp", ["f","acc","t","u"], A(v("f"), v("t"), A(a("cons"), v("u"), v("acc"))))
D("spGen", ["f","m","acc"], A(v("m"), A(a("resS"), v("acc")), A(a("resK"), v("acc")),
                                      A(a("resI"), v("acc")), A(a("spApp"), v("f"), v("acc"))))
AL("sp", A(Y, a("spGen")))
D("rb1", ["f","h","x","xs"], A(v("f"), A(mkApp, v("h"), v("x")), v("xs")))
D("rbGen", ["f","h","args"], A(v("args"), v("h"), A(a("rb1"), v("f"), v("h"))))
AL("rb", A(Y, a("rbGen")))
D("stepI1", ["x","rest"], A(a("just"), A(a("rb"), v("x"), v("rest"))))
D("stepI",  ["args"], A(v("args"), a("nothing"), a("stepI1")))
D("stepK2", ["x","y","rest"], A(a("just"), A(a("rb"), v("x"), v("rest"))))
D("stepK1", ["x","r"], A(v("r"), a("nothing"), A(a("stepK2"), v("x"))))
D("stepK",  ["args"], A(v("args"), a("nothing"), a("stepK1")))
D("stepS3", ["x","y","z","rest"], A(a("just"), A(a("rb"),
    A(mkApp, A(mkApp, v("x"), v("z")), A(mkApp, v("y"), v("z"))), v("rest"))))
D("stepS2", ["x","y","r2"], A(v("r2"), a("nothing"), A(a("stepS3"), v("x"), v("y"))))
D("stepS1", ["x","r"], A(v("r"), a("nothing"), A(a("stepS2"), v("x"))))
D("stepS",  ["args"], A(v("args"), a("nothing"), a("stepS1")))
D("step",   ["m"], A(a("sp"), v("m"), a("nil"), a("stepS"), a("stepK"), a("stepI")))
D("wf1",   ["w","m","n2"], A(a("step"), v("m"), A(a("just"), v("m")), A(v("w"), v("n2"))))
D("wfGen", ["w","n","m"], A(v("n"), a("nothing"), A(a("wf1"), v("w"), v("m"))))
AL("whnfF", A(Y, a("wfGen")))
# the unquoter (the unit): E = Y (\e m. m S K I (\t u. (e t)(e u)))
D("UQA",   ["f","t","u"], A(A(v("f"), v("t")), A(v("f"), v("u"))))
D("UQGen", ["f","m"], A(v("m"), S, K, I, A(a("UQA"), v("f"))))
AL("UQ", A(Y, a("UQGen")))


# ------------------------------------------------- Err extension (T3)
# Five constructors.  The ONLY difference between the two emulators below
# is the Err arm -- one line each.  Note the three-way protocols: a Scott
# Maybe result CANNOT distinguish "contracted a redex" from "errored", so
# an absorbing Err arm returning `just <Err>` loops to fuel exhaustion and
# silently reports a crash as a timeout.  Extending the object language
# forces the interpreter's result types to grow with it.
D("encS5", ["s","k","i","z","e"], v("s")); D("encK5", ["s","k","i","z","e"], v("k"))
D("encI5", ["s","k","i","z","e"], v("i")); D("encE5", ["s","k","i","z","e"], v("e"))
D("encA5", ["t","u","s","k","i","z","e"], A(v("z"), v("t"), v("u")))
mk5 = a("encA5")
def enc5(t):
    _L = {"S":"encS5","K":"encK5","I":"encI5","Err":"encE5"}
    out, work = [], [(t, False)]
    while work:
        x, dn = work.pop()
        if isinstance(x, Atom): out.append(a(_L[x.name])); continue
        if not dn:
            work.append((x, True)); work.append((x.arg, False)); work.append((x.fn, False))
        else:
            r = out.pop(); l = out.pop(); out.append(A(mk5, l, r))
    return out.pop()

D("r5S", ["acc","s","k","i","e"], A(v("s"), v("acc")))
D("r5K", ["acc","s","k","i","e"], A(v("k"), v("acc")))
D("r5I", ["acc","s","k","i","e"], A(v("i"), v("acc")))
D("r5E", ["acc","s","k","i","e"], A(v("e"), v("acc")))
D("sp5App", ["f","acc","t","u"], A(v("f"), v("t"), A(a("cons"), v("u"), v("acc"))))
D("sp5Gen", ["f","m","acc"], A(v("m"), A(a("r5S"),v("acc")), A(a("r5K"),v("acc")),
                                       A(a("r5I"),v("acc")), A(a("sp5App"),v("f"),v("acc")),
                                       A(a("r5E"),v("acc"))))
AL("sp5", A(Y, a("sp5Gen")))
D("rb51", ["f","h","x","xs"], A(v("f"), A(mk5, v("h"), v("x")), v("xs")))
D("rb5Gen", ["f","h","args"], A(v("args"), v("h"), A(a("rb51"), v("f"), v("h"))))
AL("rb5", A(Y, a("rb5Gen")))

D("stepped", ["t","c1","c2","c3"], A(v("c1"), v("t")))
D("done",    ["c1","c2","c3"], v("c2"))
D("errd",    ["c1","c2","c3"], v("c3"))
D("rVal",  ["x","c1","c2","c3"], A(v("c1"), v("x")))
D("rErr",  ["c1","c2","c3"], v("c2"))
D("rTime", ["c1","c2","c3"], v("c3"))

D("q5I1", ["x","rest"], A(a("stepped"), A(a("rb5"), v("x"), v("rest"))))
D("q5I",  ["args"], A(v("args"), a("done"), a("q5I1")))
D("q5K2", ["x","y","rest"], A(a("stepped"), A(a("rb5"), v("x"), v("rest"))))
D("q5K1", ["x","r"], A(v("r"), a("done"), A(a("q5K2"), v("x"))))
D("q5K",  ["args"], A(v("args"), a("done"), a("q5K1")))
D("q5S3", ["x","y","z","rest"], A(a("stepped"), A(a("rb5"),
    A(mk5, A(mk5, v("x"), v("z")), A(mk5, v("y"), v("z"))), v("rest"))))
D("q5S2", ["x","y","r2"], A(v("r2"), a("done"), A(a("q5S3"), v("x"), v("y"))))
D("q5S1", ["x","r"], A(v("r"), a("done"), A(a("q5S2"), v("x"))))
D("q5S",  ["args"], A(v("args"), a("done"), a("q5S1")))

OMEGA = A(A(A(S, I), I), A(A(S, I), I))
# >>> THE AUTHORED SITE -- the entire difference between the two emulators
D("errArmAbs", ["acc"], a("errd"))      # observable: crash becomes a value
D("errArmOmg", ["acc"], OMEGA)           # hidden: crash becomes host divergence
# <<<
for _tag in ("Abs", "Omg"):
    D(f"st5{_tag}", ["m"], A(a("sp5"), v("m"), a("nil"),
                             a("q5S"), a("q5K"), a("q5I"), a(f"errArm{_tag}")))
    D(f"wf5{_tag}1", ["w","m","n2"], A(a(f"st5{_tag}"), v("m"),
        A(v("w"), v("n2")), A(a("rVal"), v("m")), a("rErr")))
    D(f"wf5{_tag}Gen", ["w","n","m"], A(v("n"), a("rTime"), A(a(f"wf5{_tag}1"), v("w"), v("m"))))
    AL(f"wf5{_tag}", A(Y, a(f"wf5{_tag}Gen")))
D("decodeTag", ["r"], A(v("r"), A(K, v("VAL")), v("ERR"), v("TIME")))


WP = expand(a("whnfF"), env)
UP = expand(a("UQ"), env)
natP = lambda k: expand(nat(k), env)
encP = lambda t: expand(enc(t), env)

def decode(term, env, fuel):
    """Apply a Maybe-result to two free continuations so both sides of a
    comparison are reduced identically (comparing a reduced result to an
    unreduced expansion is the classic false MISMATCH)."""
    return fast_reduce(A(term, v("NO"), v("JU")), env, whnf_only=False, max_steps=fuel)


def report(label, inner, expect, fuel):
    print(f"  {label}")
    print(f"    input size : {size(inner):,} atoms")
    t0 = time.time(); r = fast_reduce(inner, env, max_steps=fuel); el = time.time() - t0
    print(f"    result     : {r.status.value}  {r.steps:,} contractions  {el:,.1f}s")
    if r.status is not Status.WHNF:
        print("    VERDICT    : did not reach WHNF -- raise --fuel"); return False
    got = decode(r.term, env, fuel)
    want = decode(expand(expect, env), env, fuel)
    ok = pretty(got.term) == pretty(want.term)
    print(f"    decoded    : {pretty(got.term)[:64]}")
    print(f"    VERDICT    : {'OK' if ok else 'MISMATCH'}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="t0", choices=["t0","t1","t2","t3","all"])
    ap.add_argument("--fuel", type=int, default=50_000_000)
    ap.add_argument("--kk3", type=int, default=20, help="object fuel, T3")
    ap.add_argument("--fuel3", type=int, default=400_000, help="host fuel, T3 (small: the hidden variant must fail fast)")
    ap.add_argument("--k", type=int, default=3, help="object fuel, level 1")
    ap.add_argument("--kk", type=int, default=120, help="object fuel, level 2")
    args = ap.parse_args()

    print(f"emulator: {size(WP):,} atoms, basis {{S,K,I}}   unquoter: {size(UP):,} atoms")
    print(f"size check sampled every {SIZE_CHECK_EVERY} steps; host fuel {args.fuel:,}\n")
    t = App(I, K)
    tgt = args.target

    if tgt in ("t0", "all"):
        print("T0  baseline: whnfF k <I K>")
        ref = fast_reduce(t, env, max_steps=args.k)
        report(f"whnfF {args.k} <I K>", A(WP, natP(args.k), encP(t)),
               A(a("just"), enc(ref.term)), args.fuel)

    if tgt in ("t1", "all"):
        print("\nT1  tower, emulator over unquoter: whnfF k <UQ <I K>>")
        lvl1 = A(UP, encP(t))
        ref = fast_reduce(lvl1, env, max_steps=args.kk)
        report(f"whnfF {args.kk} <UQ <I K>>", A(WP, natP(args.kk), encP(lvl1)),
               A(a("just"), enc(ref.term)), args.fuel)

    if tgt in ("t2", "all"):
        print("\nT2  THE TOWER: whnfF kk <whnfF k <I K>>")
        lvl1 = A(WP, natP(args.k), encP(t))
        ref = fast_reduce(lvl1, env, max_steps=args.kk)
        if ref.status is not Status.WHNF:
            print(f"    inner needs > {args.kk} object steps; raise --kk"); return
        print(f"    inner reaches WHNF in {ref.steps:,} object steps -> --kk must exceed this")
        report(f"whnfF {args.kk} <whnfF {args.k} <I K>>",
               A(WP, natP(args.kk), encP(lvl1)),
               A(a("just"), enc(ref.term)), args.fuel)


    if tgt in ("t3", "all"):
        print("\nT3  observability pair: two emulators differing at ONE site")
        WA = expand(a("wf5Abs"), env); WO = expand(a("wf5Omg"), env)
        DT = expand(a("decodeTag"), env); enc5P = lambda x: expand(enc5(x), env)
        print(f"    absorbing: {size(WA):,} nodes    hidden: {size(WO):,} nodes"
              f"    (object fuel {args.kk3}, host fuel {args.fuel3:,})")
        Err = Atom("Err")
        rows = [("Err", Err), ("Err K", App(Err, K)), ("K I Err", App(App(K, I), Err)),
                ("I K", App(I, K)), ("Omega", A(A(A(S,I),I), A(A(S,I),I)))]
        print(f"    {'object term':<14s}{'absorbing':>14s}{'hidden':>14s}")
        for label, ot in rows:
            cells = []
            for W in (WA, WO):
                r = fast_reduce(A(DT, A(W, natP(args.kk3), enc5P(ot))), env,
                                whnf_only=False, max_steps=args.fuel3)
                cells.append(pretty(r.term) if r.status in (Status.NORMAL, Status.WHNF)
                             else "<host diverges>")
            print(f"    {label:<14s}{cells[0]:>14s}{cells[1]:>14s}")

if __name__ == "__main__":
    import sys, threading
    sys.setrecursionlimit(10_000_000)
    threading.stack_size(1024 * 1024 * 1024)   # 1 GiB: expand() recurses on term depth
    th = threading.Thread(target=main)
    th.start(); th.join()
