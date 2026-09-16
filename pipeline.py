#!/usr/bin/env python3
"""End-to-end pipeline for the SKI-in-SKI emulator.

    t  --encode-->  <t>  --whnfF-->  just <v>  --UQ-->  v

Stage 1 (encoding) is the only meta-level step, and necessarily so: a
quote function must separate terms that are extensionally equal (S K K
and I denote the same function but have different encodings), which pure
SK cannot do [Jay & Given-Wilson, JSL 76(3), 2011].  Every later stage is
a pure-{S,K,I} term.  In particular the DECODER IS THE UNQUOTER: UQ <v>
reduces to v, so dispatch-and-decode is a single application,

    (whnfF <k> <t>) TIMEOUT UQ

which yields the reduced object term itself -- directly comparable with
the host's own reduction of t, with no continuation tricks and no
WHNF-comparison hazard.

Usage:
    python3 pipeline.py "S K K I"
    python3 pipeline.py "K I (S I I (S I I))" --obj-fuel 6 --trace 12
    python3 pipeline.py "S I I K" --full-trace
"""
from __future__ import annotations
import argparse, sys, threading

sys.setrecursionlimit(10_000_000)

from aviary_kernel.terms import Atom, App, pretty, size as tree_atoms
from aviary_kernel.reduce import reduce, Status
from aviary_kernel.abstraction import expand

# reuse the harness's environment, emulator, encoder and fast reducer
_H = open("tower_harness.py").read().split("def decode")[0]
_H = _H.replace('if __name__', 'if False and __name__')
exec(_H)

W = 78


def parse_ski(s: str) -> Atom | App:
    """Left-associative application; parens; atoms S K I Err."""
    toks, i = [], 0
    while i < len(s):
        c = s[i]
        if c.isspace(): i += 1
        elif c in "()": toks.append(c); i += 1
        else:
            j = i
            while j < len(s) and not s[j].isspace() and s[j] not in "()": j += 1
            toks.append(s[i:j]); i = j
    pos = 0

    def atoms():
        nonlocal pos
        out = []
        while pos < len(toks) and toks[pos] != ")":
            if toks[pos] == "(":
                pos += 1
                out.append(atoms())
                if pos >= len(toks) or toks[pos] != ")":
                    raise SystemExit("unbalanced parentheses")
                pos += 1
            else:
                nm = toks[pos]; pos += 1
                if nm not in ("S", "K", "I"):
                    raise SystemExit(f"unknown atom {nm!r} (use S, K, I)")
                out.append(Atom(nm))
        if not out: raise SystemExit("empty subterm")
        r = out[0]
        for x in out[1:]: r = App(r, x)
        return r

    t = atoms()
    if pos != len(toks): raise SystemExit("trailing input")
    return t


def head(title): print(f"\n{title}\n" + "-" * W)


def show(label, value, limit=W - 24):
    txt = value if isinstance(value, str) else pretty(value)
    if len(txt) > limit: txt = txt[:limit - 3] + "..."
    print(f"  {label:<20s} {txt}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("term", help='e.g. "S K K I"')
    ap.add_argument("--obj-fuel", type=int, default=20, help="object steps the emulator may take")
    ap.add_argument("--trace", type=int, default=10, help="contractions to display")
    ap.add_argument("--full-trace", action="store_true")
    ap.add_argument("--host-fuel", type=int, default=50_000_000)
    a = ap.parse_args()

    t = parse_ski(a.term)

    head("INPUT")
    show("object term t", t)
    show("tree-atoms", f"{tree_atoms(t):,}")

    head("STAGE 1  encode  (meta-level: not SKI-definable)")
    q = encP(t)                       # expand(enc(t)) : pure {S,K,I}
    show("<t>", q)
    show("tree-atoms", f"{tree_atoms(q):,}")
    show("basis", "{" + ",".join(sorted({x.name for x in _leaves(q)})) + "}")

    head("STAGE 2  apply the emulator")
    applied = A(WP, natP(a.obj_fuel), q)
    show("whnfF <k> <t>", f"k = {a.obj_fuel}")
    show("tree-atoms", f"{tree_atoms(applied):,}")
    show("emulator size", f"{tree_atoms(WP):,} tree-atoms, basis {{S,K,I}}")

    head(f"STAGE 3  reduce  (first {'all' if a.full_trace else a.trace} contractions)")
    lim = 10 ** 7 if a.full_trace else a.trace
    tr = reduce(applied, env, whnf_only=True, max_steps=lim,
                max_size=10 ** 9, trace=True, trace_limit=lim + 1)
    print(f"  {'step':>6s}  {'rule':<8s} term")
    for st in tr.trace[: lim + 1]:
        txt = pretty(st.term)
        if len(txt) > W - 20: txt = txt[: W - 23] + "..."
        print(f"  {st.step:>6d}  {(st.contracted or '-'):<8s} {txt}")
    if not a.full_trace:
        print(f"  {'...':>6s}")

    head("STAGE 4  result of the emulator")
    r = fast_reduce(applied, env, max_steps=a.host_fuel)
    show("status", r.status.value)
    show("contractions", f"{r.steps:,}")
    show("raw result", r.term)
    print("  " + "(this is `just <v>` or `nothing`, with the payload still suspended:")
    print("   weak head normal form does not enter the argument of K)")

    head("STAGE 5  dispatch + decode in one application:  result TIMEOUT UQ")
    piped = A(r.term, Atom("TIMEOUT"), UP)
    dw = fast_reduce(piped, env, whnf_only=True,  max_steps=a.host_fuel)
    dn = fast_reduce(piped, env, whnf_only=False, max_steps=a.host_fuel)
    show("decoder", f"UQ, {tree_atoms(UP):,} tree-atoms (the unquoter IS the decoder)")
    show("contractions", f"{dw.steps:,} to whnf, {dn.steps:,} to normal form")
    show("decoded (whnf)", dw.term)
    show("decoded (normal)", dn.term if dn.status is Status.NORMAL else f"<{dn.status.value}>")
    print("  WHNF is NOT a canonical form: `K x` is weak-head-normal for every x, so")
    print("  the payload stays suspended and two equal results can differ as terms.")
    print("  Comparison must be at normal form -- comparing at WHNF is unsound.")

    head("STAGE 6  check against the host's own reduction")
    hw = fast_reduce(t, env, whnf_only=True, max_steps=a.obj_fuel)
    if hw.status is not Status.WHNF:
        show("host reduce t", f"<{hw.status.value}> within object budget {a.obj_fuel}")
        ok = pretty(dn.term) == "TIMEOUT"
        show("expected", "TIMEOUT")
    else:
        hn = fast_reduce(hw.term, env, whnf_only=False, max_steps=a.host_fuel)
        show("host whnf", hw.term)
        show("host normal", hn.term if hn.status is Status.NORMAL else f"<{hn.status.value}>")
        show("host steps", f"{hw.steps:,} to whnf")
        ok = (None if (dn.status is not Status.NORMAL or hn.status is not Status.NORMAL)
              else pretty(dn.term) == pretty(hn.term))
    print()
    if ok is None:
        show("VERDICT", "INCONCLUSIVE - normalisation capped; raise --host-fuel")
    else:
        show("VERDICT", "MATCH" if ok else "*** MISMATCH ***")
    print()
    print("  Note: closing the pipeline into a single term `RUN = \\n m. whnfF n m ? UQ`")
    print("  requires choosing a distinguished term for `?`.  Any SKI term chosen is")
    print("  also a possible legitimate output, so the timeout is indistinguishable")
    print("  from a value unless it is tagged -- the authored-failure choice again,")
    print("  now at the top of the pipeline.")
    sys.exit(0 if ok else (2 if ok is None else 1))


def _leaves(t):
    st, out = [t], []
    while st:
        x = st.pop()
        if isinstance(x, Atom): out.append(x)
        else: st.append(x.fn); st.append(x.arg)
    return out


if __name__ == "__main__":
    threading.stack_size(1024 * 1024 * 1024)
    box = {}
    th = threading.Thread(target=lambda: box.update(rc=_wrap()))
    def _wrap():
        try: main()
        except SystemExit as e: return e.code
        return 0
    th = threading.Thread(target=lambda: box.update(rc=_wrap()))
    th.start(); th.join()
    sys.exit(box.get("rc", 1))
