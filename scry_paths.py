#!/usr/bin/env python3
"""Follow-on to scry_namespace.py: a scry NAMESPACE OVER ARBITRARY COMPOUND
PATHS, keyed by structural equality of Scott-encoded paths -- computed in
pure {S,K,I}.

This file does not modify scry_namespace.py, scry_harness.py, or
tower_harness.py. It loads scry_namespace.py's environment (which loads the
other two) and reuses its emulator `wfN`, its oracle-answer type
(oJust/oNothing/oNotYet), its 4-way outcomes, and its `peel4` UNCHANGED.
Nothing in the emulator changes. What changes is the ORACLE: instead of
dispatching on a path's head leaf tag via spQ (scry_namespace.py, which
therefore only handled bare-leaf paths), the oracle built here compares the
incoming path against each known path with `EQ5`, a structural-equality
combinator over the {S,K,I,App,Scry} encoding, and answers oJust for the
first match and oNotYet if none matches.

WHY THIS IS POSSIBLE, STATED EXACTLY. scry_namespace.py's docstring said
that comparing arbitrary encoded paths is "exactly the capability Jay &
Given-Wilson (2011, Thm. 3.2) show plain SK does not have". That was wrong,
and this file is the correction. Theorem 3.2 is about factorising LIVE
combinators: no SK term can take an opaque `S K K` apart, because
representable functions respect conversion and factorisation does not.
The path an oracle receives is not a live combinator. By the time the spine
walker reaches `Scry p`, `p` is Scott-encoded DATA -- a tree with five leaf
tags -- and equality on such data is an ordinary structural recursion,
definable with Y like everything else here. Jay & Given-Wilson say so
themselves (2011, pp. 7-8): once a term is encoded as a list, factorisation
"is a routine list operation". The thing SK cannot do is produce that
encoding from a live term, which is why enc()/encQ() are Python. Everything
after the encoding boundary, including this equality, is closed under SKI.

PATHS ARE COMPARED SYNTACTICALLY, NOT UP TO CONVERSION. `Scry (I K)` and
`Scry K` are different paths to this oracle even though `I K` reduces to
`K` -- the walker hands the oracle the path exactly as written, unreduced.
That is the correct design: matching paths up to conversion would be the
word problem for SKI (undecidable), and it is also what Nock does, where a
scry path is a noun compared by noun equality. A check below demonstrates
it directly.

WHAT IS SKI AND WHAT IS HOST. SKI: `wfN` (unchanged), `EQ5`, and every
oracle term built per round (closed {S,K,I}, checked). Host (Python): the
fact table standing in for an external source of truth, the resume loop,
the "stuck" detection, and `decode_path`, which turns a blocked path's
encoded payload back into an object term so the fact table can be consulted
-- the driver-side mirror of encQ, done behaviorally (fresh-marker probes),
never by reading combinator syntax.

RESUME IS RE-RUN FROM SCRATCH (scry_namespace.py's option (a)). Its
soundness needs a hypothesis scry_namespace.py's docstring left implicit:
the oracle in round r+1 must agree with the oracle in round r on every path
round r answered. That holds here because the namespace is append-only.
Re-run is also not fuel-neutral: each round replays the previous one and
then takes at least one more step, so a fixed fuel budget that suffices to
BLOCK may not suffice to finish. A check below demonstrates that too.

Usage:
    python3 scry_paths.py
"""
from __future__ import annotations
import sys, threading

sys.setrecursionlimit(10_000_000)

from aviary_kernel.terms import Atom, App, pretty, size as _tree_size
from aviary_kernel.abstraction import expand

# ---- load scry_namespace.py's environment without running its __main__.
# ---- scry_namespace.py's OWN source contains the guard string inside a
# ---- quoted split(...) call (its load of scry_harness.py), so splitting on
# ---- the bare string would truncate mid-literal. Split on the guard LINE.
_N = open("scry_namespace.py").read().split('\nif __name__ == "__main__":\n')[0]
exec(_N)

W = 74


def head(title):
    print(f"\n{title}\n" + "-" * W)


# ================================================== Scott booleans
D("pTrue", ["x", "y"], v("x"))
D("pFalse", ["x", "y"], v("y"))
D("pAnd", ["p", "q"], A(v("p"), v("q"), a("pFalse")))
# constant-false in a 2-argument slot (an App node compared against a leaf)
AL("pKKF", A(K, A(K, a("pFalse"))))

# ================================================== EQ5: structural equality
# over the {S,K,I,App,Scry} encoding. Dispatch order of the encoding is
# (s, k, i, z, c): leaf S, leaf K, leaf I, App t u, leaf Scry.
#   EQ5 m n  ->  pTrue | pFalse
# Leaf vs leaf: true iff same slot. Leaf vs App: false (pKKF absorbs t u).
# App vs App: EQ5 on both children, conjoined. App vs leaf: false.
D("eqApp2P", ["e", "t", "u", "t2", "u2"],
  A(a("pAnd"), A(v("e"), v("t"), v("t2")), A(v("e"), v("u"), v("u2"))))
D("eqApp1P", ["e", "n", "t", "u"],
  A(v("n"), a("pFalse"), a("pFalse"), a("pFalse"),
    A(a("eqApp2P"), v("e"), v("t"), v("u")), a("pFalse")))
D("eqNP", ["e", "m", "n"], A(v("m"),
    A(v("n"), a("pTrue"), a("pFalse"), a("pFalse"), a("pKKF"), a("pFalse")),
    A(v("n"), a("pFalse"), a("pTrue"), a("pFalse"), a("pKKF"), a("pFalse")),
    A(v("n"), a("pFalse"), a("pFalse"), a("pTrue"), a("pKKF"), a("pFalse")),
    A(a("eqApp1P"), v("e"), v("n")),
    A(v("n"), a("pFalse"), a("pFalse"), a("pFalse"), a("pKKF"), a("pTrue"))))
D("eqGenP", ["e", "m"], A(a("eqNP"), v("e"), v("m")))
AL("EQ5", A(Y, a("eqGenP")))

EQ5 = expand(a("EQ5"), env)


def eq5(t1, t2):
    """Host-side test of EQ5 on two OBJECT terms: encode both, apply EQ5,
    read the boolean with two fresh markers. Returns True/False/None."""
    r = fast_reduce(A(EQ5, encQ(t1), encQ(t2), Atom("TRUE"), Atom("FALSE")),
                    env, whnf_only=False, max_steps=2_000_000)
    txt = pretty(r.term)
    return {"TRUE": True, "FALSE": False}.get(txt)


# ================================================== host-side path decoder
_MARK = [Atom(f"X{i}") for i in range(1, 6)]
_LEAF_OF_MARK = {"X1": "S", "X2": "K", "X3": "I", "X5": "Scry"}


def _spine(t):
    args = []
    while isinstance(t, App):
        args.append(t.arg); t = t.fn
    return t, list(reversed(args))


def decode_path(payload):
    """Encoded {S,K,I,App,Scry} payload -> object term, by behavioral probe:
    apply to 5 fresh markers, reduce to WHNF, read which marker heads the
    result, recurse into the two arguments of an App. Returns None if the
    payload does not behave like an encoded term."""
    r = fast_reduce(A(payload, *_MARK), env, max_steps=200_000)
    hd, args = _spine(r.term)
    if not isinstance(hd, Atom):
        return None
    if hd.name in _LEAF_OF_MARK and not args:
        return Atom(_LEAF_OF_MARK[hd.name])
    if hd.name == "X4" and len(args) == 2:
        l = decode_path(args[0]); rr = decode_path(args[1])
        if l is None or rr is None:
            return None
        return App(l, rr)
    return None


# ================================================== the compound-path oracle
_path_round_counter = [0]


def make_path_oracle(facts_encoded):
    """Build a fresh, closed {S,K,I} oracle term from a list of
    (encoded path, encoded answer) pairs:
        p |-> EQ5 p <k1> (oJust <a1>) (EQ5 p <k2> (oJust <a2>) (... oNotYet))
    First structural match wins; no match answers oNotYet."""
    body = a("oNotYet")
    for key, ans in reversed(facts_encoded):
        body = A(a("EQ5"), v("p"), key, A(a("oJust"), ans), body)
    _path_round_counter[0] += 1
    name = f"pathOracle{_path_round_counter[0]}"
    D(name, ["p"], body)
    return expand(a(name), env)


def run_with_paths(term, resolution, fuel, max_rounds=10):
    """Resume loop over compound paths. `resolution` is a list of
    (object path term, object answer term) pairs -- the host-side source of
    truth. Facts are learned into an append-only namespace, keyed by the
    printed form of the path (host-side syntactic equality, mirroring the
    SKI-side EQ5). Returns a trace of (round, event) pairs."""
    table = {pretty(p): ans for p, ans in resolution}
    namespace = []            # list of (path term, answer term), append-only
    known = set()
    q = encQ(term)
    trace = []
    for rnd in range(1, max_rounds + 1):
        E = make_path_oracle([(encQ(p), encQ(x)) for p, x in namespace])
        r = fast_reduce(A(WN, E, natP(fuel), q), env, max_steps=50_000_000)
        if r.status.value != "whnf":
            trace.append((rnd, f"status:{r.status.value}"))
            return trace
        tag, payload = peel4(r.term)
        if tag in ("VAL", "ERR", "TIME"):
            trace.append((rnd, tag))
            return trace
        path = decode_path(payload)
        key = pretty(path) if path is not None else None
        trace.append((rnd, f"BLOCK on {key}"))
        if key is None or key in known or key not in table:
            trace.append((rnd, "STUCK"))
            return trace
        namespace.append((path, table[key])); known.add(key)
    trace.append((max_rounds, "EXCEEDED MAX ROUNDS"))
    return trace


def final_value(term, resolution, fuel, max_rounds=10):
    """Run to completion; if VAL, decode the payload to an object term (via
    the behavioral probe) and return its printed form, else None."""
    table = {pretty(p): ans for p, ans in resolution}
    namespace, known = [], set()
    q = encQ(term)
    for _ in range(max_rounds):
        E = make_path_oracle([(encQ(p), encQ(x)) for p, x in namespace])
        r = fast_reduce(A(WN, E, natP(fuel), q), env, max_steps=50_000_000)
        if r.status.value != "whnf":
            return None
        tag, payload = peel4(r.term)
        if tag == "VAL":
            d = decode_path(payload)
            return pretty(d) if d is not None else None
        if tag != "BLOCK":
            return None
        path = decode_path(payload)
        key = pretty(path) if path is not None else None
        if key is None or key in known or key not in table:
            return None
        namespace.append((path, table[key])); known.add(key)
    return None


def show(label, ok):
    print(f"  {'OK  ' if ok else '*** FAIL ***':<6s}  {label}")
    return ok


def leaves(t):
    st, out = [t], set()
    while st:
        x = st.pop()
        if isinstance(x, Atom): out.add(x.name)
        else: st.append(x.fn); st.append(x.arg)
    return out


def main():
    all_ok = True
    SK = App(S, K); KS = App(K, S); SKK = A(S, K, K); KI = App(K, I); IK = App(I, K)

    head("PURITY: EQ5 and the emulator stay in {S,K,I}")
    all_ok &= show(f"EQ5 basis == {{S,K,I}}  (got {sorted(leaves(EQ5))})",
                   sorted(leaves(EQ5)) == ["I", "K", "S"])
    all_ok &= show(f"WN (reused unchanged from scry_namespace.py) basis == {{S,K,I}}",
                   sorted(leaves(WN)) == ["I", "K", "S"])

    head("EQ5 DIRECTLY: structural equality on encoded paths, read with 2 markers")
    cases = [
        (K, K, True), (K, S, False), (I, SKK, False), (SKK, I, False),
        (SK, SK, True), (SK, KS, False), (SKK, SK, False), (SK, SKK, False),
        (Scry(K), Scry(K), True), (Scry(K), Scry(I), False),
        (Scry(SK), Scry(SK), True), (App(K, Scry(K)), App(K, Scry(K)), True),
        (App(K, Scry(K)), App(K, Scry(S)), False),
    ]
    for t1, t2, want in cases:
        got = eq5(t1, t2)
        all_ok &= show(f"EQ5 <{pretty(t1)}> <{pretty(t2)}> -> {got}", got is want)

    head("DECODER ROUND-TRIP: decode_path(encQ(t)) == t, by behavioral probe")
    for t in [S, K, I, SK, SKK, Scry(K), Scry(SK), App(K, Scry(SKK))]:
        d = decode_path(encQ(t))
        all_ok &= show(f"{pretty(t)} -> {pretty(d) if d is not None else None}",
                       d is not None and pretty(d) == pretty(t))

    head("REGRESSION: scry_namespace.py's bare-leaf cases, now via EQ5 matching")
    trace = run_with_paths(App(I, K), [], 10)
    all_ok &= show(f"I K, no facts -> {trace}", trace == [(1, "VAL")])
    trace = run_with_paths(App(I, Scry(K)), [(K, I)], 10)
    all_ok &= show(f"I (Scry K), fact K=I -> {trace}",
                   trace == [(1, "BLOCK on K"), (2, "VAL")])
    val = final_value(App(I, Scry(K)), [(K, I)], 10)
    all_ok &= show(f"  final value -> {val}", val == "I")
    trace = run_with_paths(Scry(S), [(S, Scry(K)), (K, I)], 10)
    all_ok &= show(f"Scry S, facts S=Scry K, K=I -> {trace}",
                   trace == [(1, "BLOCK on S"), (2, "BLOCK on K"), (3, "VAL")])
    val = final_value(Scry(S), [(S, Scry(K)), (K, I)], 10)
    all_ok &= show(f"  final value -> {val}", val == "I")

    head("COMPOUND PATHS: what scry_namespace.py could not do")
    trace = run_with_paths(Scry(SK), [(SK, I)], 10)
    all_ok &= show(f"Scry (S K), fact (S K)=I -> {trace}",
                   trace == [(1, "BLOCK on S K"), (2, "VAL")])
    val = final_value(Scry(SK), [(SK, I)], 10)
    all_ok &= show(f"  final value -> {val}", val == "I")
    trace = run_with_paths(Scry(SK), [(KS, I)], 10)
    all_ok &= show(f"Scry (S K), only fact (K S)=I -> {trace}  (no false hit)",
                   trace == [(1, "BLOCK on S K"), (1, "STUCK")])

    head("PREFIX DISCRIMINATION: (S K K) vs its own prefix (S K)")
    facts = [(SK, I), (SKK, K)]
    val = final_value(Scry(SKK), facts, 10)
    all_ok &= show(f"Scry (S K K), facts (S K)=I,(S K K)=K -> {val}", val == "K")
    val = final_value(Scry(SK), facts, 10)
    all_ok &= show(f"Scry (S K),   same facts              -> {val}", val == "I")

    head("CHAINED COMPOUND: a learned answer contains a new compound path")
    facts = [(KI, Scry(SK)), (SK, I)]
    trace = run_with_paths(Scry(KI), facts, 10)
    all_ok &= show(f"Scry (K I), facts (K I)=Scry (S K), (S K)=I -> {trace}",
                   trace == [(1, "BLOCK on K I"), (2, "BLOCK on S K"), (3, "VAL")])
    val = final_value(Scry(KI), facts, 10)
    all_ok &= show(f"  final value -> {val}", val == "I")

    head("SYNTACTIC, NOT SEMANTIC: I K reduces to K, but is not the path K")
    trace = run_with_paths(Scry(IK), [(K, S)], 10)
    all_ok &= show(f"Scry (I K), only fact K=S -> {trace}",
                   trace == [(1, "BLOCK on I K"), (1, "STUCK")])
    val = final_value(Scry(IK), [(IK, S)], 10)
    all_ok &= show(f"Scry (I K), fact (I K)=S -> {val}", val == "S")

    head("FUEL IS CHARGED PER ROUND: re-run from scratch is not fuel-neutral")
    tr1 = run_with_paths(Scry(SK), [(SK, I)], 1)
    tr2 = run_with_paths(Scry(SK), [(SK, I)], 2)
    all_ok &= show(f"Scry (S K), fact (S K)=I, fuel=1 -> {tr1}",
                   tr1 == [(1, "BLOCK on S K"), (2, "TIME")])
    all_ok &= show(f"Scry (S K), fact (S K)=I, fuel=2 -> {tr2}",
                   tr2 == [(1, "BLOCK on S K"), (2, "VAL")])
    omega = App(App(App(S, I), I), App(App(S, I), I))
    trace = run_with_paths(omega, [], 5)
    all_ok &= show(f"Omega, fuel=5 -> {trace}", trace == [(1, "TIME")])

    head("SIZES")
    E3 = make_path_oracle([(encQ(SK), encQ(I)), (encQ(SKK), encQ(K)), (encQ(KI), encQ(S))])
    print(f"  EQ5: {_tree_size(EQ5):,} tree-atoms, basis {sorted(leaves(EQ5))}")
    print(f"  a 3-fact compound-path oracle term: {_tree_size(E3):,} tree-atoms, basis {sorted(leaves(E3))}")
    print(f"  emulator (wfN, unchanged): {_tree_size(WN):,} tree-atoms")
    print(f"  oracle rounds built this run: {_path_round_counter[0]}")
    all_ok &= show("3-fact oracle term basis == {S,K,I}", sorted(leaves(E3)) == ["I", "K", "S"])

    print(f"\n  {'ALL CHECKS PASSED' if all_ok else '*** SOME CHECKS FAILED ***'}")
    return all_ok


if __name__ == "__main__":
    threading.stack_size(1024 * 1024 * 1024)
    box = {}
    th = threading.Thread(target=lambda: box.update(ok=main()))
    th.start(); th.join()
    sys.exit(0 if box.get("ok") else 1)
