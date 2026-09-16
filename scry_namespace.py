#!/usr/bin/env python3
"""Follow-on to scry_harness.py: a BLOCKING scry site with a growing
namespace, implementing option (a) ("re-run from scratch") from
SCRY-BLOCKING-DESIGN.md.

This file does not modify scry_harness.py or tower_harness.py. It loads
scry_harness.py's environment (which itself loads tower_harness.py's, same
technique pipeline.py established) and adds a SECOND, independent extension
of the outcome type -- suffixed "N" (namespace) -- reusing scry_harness.py's
encQ/spQ/rbQ/Scry UNCHANGED (they are purely structural, no coupling to any
outcome type) and building fresh 4-way step/result types alongside its
existing 3-way ones, per SCRY-BLOCKING-DESIGN.md S1's point 3: the existing
`stepped`/`done`/`errd` (3-continuation Scott selectors) cannot be reused
for a 4th outcome without an arity mismatch, so this is new code, not a
patch to old code.

THE DESIGN. The oracle's own type grows from 2-way Maybe (just/nothing) to
3-way (oJust/oNothing/oNotYet): a "notyet" answer means the oracle doesn't
know (yet), not "the path doesn't exist" (oNothing, kept distinct -- see
SCRY-BLOCKING-DESIGN.md's warning against conflating outcomes). The step
outcome grows correspondingly to 4-way (steppedN/doneN/errdN/pendingN),
and the fuel loop's outer result to 4-way (rValN/rErrN/rTimeN/rBlockN).

Resuming a block does NOT capture a continuation -- reduction is pure and
deterministic, so re-running the WHOLE computation from the original input
term, under an oracle that now additionally knows the fact that was missing,
reproduces every step already taken and then proceeds past the block. This
is SCRY-BLOCKING-DESIGN.md's option (a), chosen there as the cheapest and
most auditable, and (per my best understanding) the closest to how real
scry-blocking actually behaves in practice -- an event that blocks on a
scry is retried, not resumed via a captured continuation.

The "namespace" is the Python-level dict of facts learned so far, threaded
through successive re-runs -- each round builds a FRESH oracle term (an
ordinary SKI combinator, not a Python closure standing in for one) that
answers `oJust` for every leaf currently known and `oNotYet` for every leaf
that isn't, dispatching via spQ (reused, unmodified) exactly the way
oracleIfK in scry_harness.py already did. Scope, stated precisely: paths
are restricted to bare leaves (S, K, I, or a path that is itself the Scry
tag), because dispatch-by-leaf-tag via spQ is tag selection, not equality
comparison. An earlier version of this docstring claimed that comparing
arbitrary encoded paths is what Jay & Given-Wilson (2011, Thm. 3.2) show
plain SK cannot do. That was wrong: Thm. 3.2 is about factorising LIVE
combinators; the path the oracle receives is Scott-encoded DATA, and
structural equality on it is an ordinary recursion in {S,K,I}. The
follow-on scry_paths.py builds exactly that (EQ5, 240 tree-atoms) and runs
a compound-path namespace inside this file's wfN, unchanged.

Usage:
    python3 scry_namespace.py
"""
from __future__ import annotations
import sys, threading

sys.setrecursionlimit(10_000_000)

from aviary_kernel.terms import Atom, App, pretty, size as _tree_size
from aviary_kernel.abstraction import expand

# ---- load scry_harness.py's environment (which loads tower_harness.py's)
# ---- without running either file's __main__ block. Split on the exact
# ---- guard line, not the bare substring "if __name__" -- scry_harness.py's
# ---- OWN source contains that substring inside a quoted string (its own
# ---- load of tower_harness.py), so a naive split truncates mid-string.
# ---- (Caught by testing this exact line before trusting it.)
_S = open("scry_harness.py").read().split('if __name__ == "__main__":')[0]
exec(_S)

W = 74


def head(title):
    print(f"\n{title}\n" + "-" * W)


# ================================================ 3-way oracle-answer type
# oJust v | oNothing | oNotYet. The step function's Scry arm consults an
# oracle of this type instead of the synchronous 2-way Maybe -- "I don't
# know yet" (oNotYet) is a genuinely different answer from "there is no
# such path" (oNothing), and this driver only ever produces oNotYet (see
# module docstring: everything not yet in the namespace is presumed
# learnable, not presumed absent).
D("oJust", ["x", "j", "n", "w"], A(v("j"), v("x")))
D("oNothing", ["j", "n", "w"], v("n"))
D("oNotYet", ["j", "n", "w"], v("w"))

# =================================================== 4-way step outcome
# steppedN t | doneN | errdN | pendingN p -- mechanical extension of
# scry_harness.py's stepped/done/errd (reused there unmodified from T3);
# cannot reuse those directly here since a 4th continuation slot changes
# every selector's arity (SCRY-BLOCKING-DESIGN.md S1, point 3).
D("steppedN", ["t", "c1", "c2", "c3", "c4"], A(v("c1"), v("t")))
D("doneN", ["c1", "c2", "c3", "c4"], v("c2"))
D("errdN", ["c1", "c2", "c3", "c4"], v("c3"))
D("pendingN", ["p", "c1", "c2", "c3", "c4"], A(v("c4"), v("p")))

# S, K, I arms: identical redex logic to scry_harness.py's stepSQ/stepKQ/
# stepIQ, rebuilt against steppedN/doneN for arity, reusing rbQ/mkAppQ
# unmodified (purely structural, no outcome-type coupling).
D("stepIN1", ["x", "rest"], A(a("steppedN"), A(a("rbQ"), v("x"), v("rest"))))
D("stepIN", ["args"], A(v("args"), a("doneN"), a("stepIN1")))

D("stepKN2", ["x", "y", "rest"], A(a("steppedN"), A(a("rbQ"), v("x"), v("rest"))))
D("stepKN1", ["x", "r"], A(v("r"), a("doneN"), A(a("stepKN2"), v("x"))))
D("stepKN", ["args"], A(v("args"), a("doneN"), a("stepKN1")))

D("stepSN3", ["x", "y", "z", "rest"], A(a("steppedN"), A(a("rbQ"),
    A(mkAppQ, A(mkAppQ, v("x"), v("z")), A(mkAppQ, v("y"), v("z"))), v("rest"))))
D("stepSN2", ["x", "y", "r2"], A(v("r2"), a("doneN"), A(a("stepSN3"), v("x"), v("y"))))
D("stepSN1", ["x", "r"], A(v("r"), a("doneN"), A(a("stepSN2"), v("x"))))
D("stepSN", ["args"], A(v("args"), a("doneN"), a("stepSN1")))

# Scry arm: the oracle's 3-way answer maps onto the 4-way outcome. `p` (the
# path being asked about) is supplied by stepScN1 itself when building
# pendingN's payload -- the oracle's oNotYet answer carries no payload of
# its own, since the caller already knows what it asked.
D("scHitN", ["rest", "v"], A(a("steppedN"), A(a("rbQ"), v("v"), v("rest"))))
D("stepScN1", ["e", "p", "rest"], A(v("e"), v("p"),
    A(a("scHitN"), v("rest")),
    a("errdN"),
    A(a("pendingN"), v("p"))))
D("stepScN", ["e", "args"], A(v("args"), a("doneN"), A(a("stepScN1"), v("e"))))

D("stepNE", ["e", "m"], A(a("spQ"), v("m"), a("nil"),
    a("stepSN"), a("stepKN"), a("stepIN"), A(a("stepScN"), v("e"))))

# ================================================== 4-way outer result
# rValN x | rErrN | rTimeN | rBlockN p -- same reasoning as steppedN etc.,
# applied to the outer type (scry_harness.py's rVal/rErr/rTime, reused
# unmodified there from T3, cannot take a 4th branch without new arity).
D("rValN", ["x", "c1", "c2", "c3", "c4"], A(v("c1"), v("x")))
D("rErrN", ["c1", "c2", "c3", "c4"], v("c2"))
D("rTimeN", ["c1", "c2", "c3", "c4"], v("c3"))
D("rBlockN", ["p", "c1", "c2", "c3", "c4"], A(v("c4"), v("p")))

D("wfN1", ["e", "w", "m", "n2"], A(a("stepNE"), v("e"), v("m"),
    A(v("w"), v("e"), v("n2")),
    A(a("rValN"), v("m")),
    a("rErrN"),
    a("rBlockN")))
D("wfNGen", ["w", "e", "n", "m"], A(v("n"), a("rTimeN"), A(a("wfN1"), v("e"), v("w"), v("m"))))
AL("wfN", A(Y, a("wfNGen")))

WN = expand(a("wfN"), env)

_LEAF_SLOT = {"S": 0, "K": 1, "I": 2, "Scry": 4}   # index into (s,k,i,z,c)
_SLOT_LEAF = {v: k for k, v in _LEAF_SLOT.items()}


def peel4(r_term):
    """Peel the outer rValN/rErrN/rTimeN/rBlockN wrapper with 4 fresh
    markers. Returns (tag, payload_or_None); payload is still a Scott-
    encoded {S,K,I,App,Scry} term (5-arity), not further decoded."""
    unwrapped = fast_reduce(A(r_term, Atom("C1"), Atom("C2"), Atom("C3"), Atom("C4")),
                             env, max_steps=200_000)
    txt = pretty(unwrapped.term)
    if txt.startswith("C1 "):
        return "VAL", unwrapped.term.arg
    if txt == "C2":
        return "ERR", None
    if txt == "C3":
        return "TIME", None
    if txt.startswith("C4 "):
        return "BLOCK", unwrapped.term.arg
    return f"<unrecognised outcome: {txt}>", None


def identify_leaf(payload):
    """Which of S/K/I/Scry a payload behaves like, by probing with 5 fresh
    markers (the ENCODING's own arity -- s,k,i,z,c -- not the 4-way outcome
    type's arity; conflating these was a real bug caught while building
    this, see the verification transcript). Returns None if the payload is
    not a bare leaf (e.g. an unresolved application)."""
    Xs = [Atom(f"X{i}") for i in range(1, 6)]
    probe = fast_reduce(A(payload, *Xs), env, whnf_only=False, max_steps=200_000)
    txt = pretty(probe.term)
    for name, slot in _LEAF_SLOT.items():
        if txt == f"X{slot + 1}":
            return name
    return None


_round_counter = [0]


def make_oracle(namespace_encoded):
    """Build a fresh SKI oracle term from the current namespace snapshot.
    namespace_encoded: dict of leaf-name -> Scott-encoded object term for
    every leaf currently known. Dispatches via spQ (reused, unmodified) --
    tag selection, not equality comparison; see module docstring for why
    that distinction is load-bearing here."""
    def leaf_cont(name):
        if name in namespace_encoded:
            return A(K, A(a("oJust"), namespace_encoded[name]))
        return A(K, a("oNotYet"))

    body = A(a("spQ"), v("p"), a("nil"),
              leaf_cont("S"), leaf_cont("K"), leaf_cont("I"), leaf_cont("Scry"))
    _round_counter[0] += 1
    name = f"nsOracle{_round_counter[0]}"
    D(name, ["p"], body)
    return expand(a(name), env)


def run_with_namespace(term, resolution_table, fuel, max_rounds=10):
    """The resume loop. resolution_table: dict leaf-name -> OBJECT-level
    term (unencoded) representing "the real answer" for that leaf, standing
    in for whatever external source of truth a namespace would consult.
    Returns a trace: list of (round, event) pairs, ending in one of
    VAL/ERR/TIME/STUCK/EXCEEDED MAX ROUNDS."""
    namespace = {}
    q = encQ(term)
    trace = []
    for rnd in range(1, max_rounds + 1):
        enc_ns = {k: encQ(v) for k, v in namespace.items()}
        E = make_oracle(enc_ns)
        r = fast_reduce(A(WN, E, natP(fuel), q), env, max_steps=50_000_000)
        if r.status.value != "whnf":
            trace.append((rnd, f"status:{r.status.value}"))
            return trace
        tag, payload = peel4(r.term)
        if tag in ("VAL", "ERR", "TIME"):
            trace.append((rnd, tag))
            return trace
        # BLOCK: learn one fact (if we can) and re-run from the original term.
        leaf = identify_leaf(payload)
        trace.append((rnd, f"BLOCK on {leaf}"))
        if leaf is None or leaf in namespace or leaf not in resolution_table:
            trace.append((rnd, "STUCK"))
            return trace
        namespace[leaf] = resolution_table[leaf]
    trace.append((max_rounds, "EXCEEDED MAX ROUNDS"))
    return trace


def final_payload_slot(term, resolution_table, fuel, max_rounds=10):
    """Run to completion and, if it ends VAL, return which leaf-slot the
    payload behaves like (for behavioral verification against a fresh
    marker probe, not the raw combinator syntax)."""
    namespace = {}
    q = encQ(term)
    for _ in range(max_rounds):
        enc_ns = {k: encQ(v) for k, v in namespace.items()}
        E = make_oracle(enc_ns)
        r = fast_reduce(A(WN, E, natP(fuel), q), env, max_steps=50_000_000)
        if r.status.value != "whnf":
            return None
        tag, payload = peel4(r.term)
        if tag == "VAL":
            return identify_leaf(payload)
        if tag != "BLOCK":
            return None
        leaf = identify_leaf(payload)
        if leaf is None or leaf in namespace or leaf not in resolution_table:
            return None
        namespace[leaf] = resolution_table[leaf]
    return None


def show(label, ok):
    print(f"  {'OK  ' if ok else '*** FAIL ***':<6s}  {label}")
    return ok


def main():
    all_ok = True

    head("PURITY: the emulator and every combinator used stay in {S,K,I}")
    def leaves(t):
        st, out = [t], set()
        while st:
            x = st.pop()
            if isinstance(x, Atom): out.add(x.name)
            else: st.append(x.fn); st.append(x.arg)
        return out
    all_ok &= show(f"WN basis == {{S,K,I}}  (got {sorted(leaves(WN))})",
                    sorted(leaves(WN)) == ["I", "K", "S"])

    head("REGRESSION: no Scry present -- resolves round 1, exactly like")
    print("  the non-blocking wfQ from scry_harness.py")
    trace = run_with_namespace(App(I, K), {}, 10)
    all_ok &= show(f"I K, empty resolution table -> {trace}",
                    trace == [(1, "VAL")])

    head("SINGLE BLOCK: one fact needed, one round to learn it, then resolves")
    trace = run_with_namespace(App(I, Scry(K)), {"K": I}, 10)
    all_ok &= show(f"I (Scry K), K unknown -> learn K=I -> {trace}",
                    trace == [(1, "BLOCK on K"), (2, "VAL")])
    slot = final_payload_slot(App(I, Scry(K)), {"K": I}, 10)
    all_ok &= show(f"final payload behaves like the i-slot (K resolved to I) -> got {slot}",
                    slot == "I")

    head("MULTI-ROUND, CHAINED: the namespace genuinely GROWS across rounds")
    print("  Scry S resolves to (Scry K), which itself then blocks on K --")
    print("  a second fact learned in a second round before WHNF is reached.")
    resolution = {"S": Scry(K), "K": I}
    trace = run_with_namespace(Scry(S), resolution, 10)
    all_ok &= show(f"Scry S -> {trace}",
                    trace == [(1, "BLOCK on S"), (2, "BLOCK on K"), (3, "VAL")])
    slot = final_payload_slot(Scry(S), resolution, 10)
    all_ok &= show(f"final payload behaves like the i-slot (S->Scry K->I) -> got {slot}",
                    slot == "I")

    head("UNRESOLVABLE: a path with no entry in the resolution table gets")
    print("  stuck cleanly -- distinguishable from both a definite miss (ERR,")
    print("  which this driver never produces -- see module docstring) and")
    print("  from exceeding the round budget.")
    trace = run_with_namespace(Scry(K), {}, 10)
    all_ok &= show(f"Scry K, empty resolution table -> {trace}",
                    trace == [(1, "BLOCK on K"), (1, "STUCK")])

    head("FUEL EXHAUSTION is still distinct from a block, at any round")
    omega = App(App(App(S, I), I), App(App(S, I), I))
    trace = run_with_namespace(omega, {}, 5)
    all_ok &= show(f"Omega, fuel=5 -> {trace}", trace == [(1, "TIME")])

    print(f"\n  emulator (wfN): {_tree_size(WN):,} tree-atoms, basis {{S,K,I}}")
    print(f"  oracle rounds built this run: {_round_counter[0]}")
    print(f"\n  {'ALL CHECKS PASSED' if all_ok else '*** SOME CHECKS FAILED ***'}")
    return all_ok


if __name__ == "__main__":
    threading.stack_size(1024 * 1024 * 1024)
    box = {}
    th = threading.Thread(target=lambda: box.update(ok=main()))
    th.start(); th.join()
    sys.exit(0 if box.get("ok") else 1)
