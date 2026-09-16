# Design: partial evaluation over the scry site

*2026-09-15. Follow-on to `scry_namespace.py` and `scry_paths.py`. Status:
designed, and the load-bearing parts prototyped against the real
environment (`proto/`, scratch scripts, not the deliverable). Everything
marked **verified** below was run in this session; everything marked
**unverified** was not, and says why. Definitions use the notation of the
source files: `D(name, [args], body)` is a Scott definition, `A(f, x, …)`
is application, and outcome selectors are as in `scry_namespace.py`.*

## 0. What is being built, in one paragraph

A partial evaluator is an interpreter that does not stop at an unknown.
The existing interpreters stop: `wfQ` reports a miss and `wfN` reports a
block when the oracle cannot answer `Scry p`. The partial evaluator `wfP`
instead treats an unanswered `Scry p` as an *inert head*, exactly as it
treats an under-applied `K`: the term is in weak head normal form with
respect to what is known, and is returned as the value. Applied to an
encoding of `wfQ E k ⟨p⟩` with `E` unknown, `wfP` returns a level-1 term
in which every dispatch on `⟨p⟩` up to the first oracle call has already
happened: `p` compiled by self-application, the first Futamura projection
in its weakest honest form. A second, depth-bounded loop `nfP` normalizes
arguments under inert heads for residuals that need it. The construction
reuses `spQ`, `rbQ`, `mkAppQ`, the four-way outcome types, `peel4`, and
`EQ5` unchanged; it adds one arm, two loops, one predicate, and a driver.

## 1. Facts about the existing code the design depends on

Read from the source on 2026-09-15; each is load-bearing below.

- **The spine walker collects arguments head-first.** `spApp f acc t u =
  f t (cons u acc)` (`tower_harness.py`), so walking `((h a₁) a₂) a₃` from
  `acc = nil` reaches the leaf `h` with `acc = [a₁, a₂, a₃]`; `rbQ h acc`
  rebuilds the same term.
- **A `Scry` leaf's continuation receives the whole argument list.**
  `resCQ acc s k i c = c acc`, and `stepScN e args = args doneN
  (stepScN1 e)`, so for `Scry p a₁ a₂` the arm sees `p` as the head of the
  list and `rest = [a₁, a₂]`. A bare `Scry` with no arguments is `doneN`
  before any oracle is consulted.
- **The oracle is consulted with the path exactly as written**
  (`scry_paths.py`: `Scry (I K)` and `Scry K` are different paths).
- **The three-way oracle answer** `oJust x j n w = j x`, `oNothing … = n`,
  `oNotYet … = w`; the blocking arm is `stepScN1 e p rest = e p
  (scHitN rest) errdN (pendingN p)` with `scHitN rest v = steppedN
  (rbQ v rest)`.
- **The four-way selectors** `steppedN t c₁…c₄ = c₁ t`, `doneN = c₂`,
  `errdN = c₃`, `pendingN p = c₄ p`; outer `rValN x = c₁ x`, `rErrN = c₂`,
  `rTimeN = c₃`, `rBlockN p = c₄ p`. A selector passed *as* its own
  continuation re-wraps itself (`rErrN` in the `c₂` slot yields `rErrN`),
  which lets the loops below propagate failures with no new code.
- **Fuel** `k` permits `k` step-attempts, the last of which must be the
  no-redex check (`wfNGen w e n m = n rTimeN (wfN1 e w m)`).
- **Under normal order, arguments are unevaluated closures.** After the
  static prefix, the residual is compact as a DAG (718 nodes for the
  Futamura example) but its arguments are thunks that reference the
  surrounding computation, so their *tree* sizes run to 10⁵ atoms each.
  Anything that walks a residual must be memoized by node identity, and
  `figures.py`-style tree walks, `pretty`, and the unmemoized
  `decode_path` of `scry_paths.py` are all inappropriate on residuals.
  This cost two out-of-memory kills before it was understood.
  **Verified.**
- **The host reducer with `Scry` as an inert atom is Stage 1's semantics.**
  `fast_reduce` performs normal-order head reduction and stops when the
  head is an atom with no rule; `wfP` performs the same reduction at level
  2. Their contraction counts agree (643 for the example below), which
  gives the level-2 fuel exactly and an independent residual to compare
  against. **Verified** (counts agree; see §5).
- **A level-2 unknown is a level-2 `Scry` leaf.** The `Scry` leaves inside
  encoded data are doubly encoded and never in head position at level 2;
  only a `Scry` leaf of the term being evaluated can be an unknown.

## 2. Stage 1: inert unknowns (`wfP`) — verified

One new arm; everything else reused.

```
D("stepScP1", ["e","p","rest"], A(v("e"), v("p"),
    A(a("scHitN"), v("rest")),     # oJust v   -> steppedN (rbQ v rest), as before
    a("errdN"),                    # oNothing  -> a definite miss, as before
    a("doneN")))                   # oNotYet   -> INERT: WHNF as far as is known
D("stepScP",  ["e","args"], A(v("args"), a("doneN"), A(a("stepScP1"), v("e"))))
D("stepPE",   ["e","m"],    A(a("spQ"), v("m"), a("nil"),
    a("stepSN"), a("stepKN"), a("stepIN"), A(a("stepScP"), v("e"))))
D("wfP1",  ["e","w","m","n2"], A(a("stepPE"), v("e"), v("m"),
    A(v("w"), v("e"), v("n2")), A(a("rValN"), v("m")), a("rErrN"), a("rBlockN")))
D("wfPGen", ["w","e","n","m"], A(v("n"), a("rTimeN"), A(a("wfP1"), v("e"), v("w"), v("m"))))
AL("wfP", A(Y, a("wfPGen")))
```

The only difference from `wfN` is the third continuation of the arm:
`pendingN p` becomes `doneN`. This is the paper's authored-site point a
third time: same leaf, same oracle, same answer, and the meaning of "not
yet" is decided by the choice between *stop and report* and *stop and
return*. `wfP` never produces `rBlockN`; the `c₄` slot is kept so `peel4`
still applies. **`wfP` expands to 1,056 tree-atoms, basis `{S,K,I}`.**

**Classifying the result.** A `rValN m` is a value if `m` contains no
`Scry` leaf and a residual otherwise. That is a property of the term, not
a fifth way the loop can end, so it is a predicate, not a fifth outcome.
Generator form, through `Y` like `spQ`:

```
D("anyArg1",    ["f","x","xs"], A(v("f"), v("x"), a("pTrue"), A(a("anyArg"), v("f"), v("xs"))))
D("anyArg",     ["f","acc"],    A(v("acc"), a("pFalse"), A(a("anyArg1"), v("f"))))
D("hasScryGen", ["f","m"],      A(a("spQ"), v("m"), a("nil"),
    A(a("anyArg"), v("f")), A(a("anyArg"), v("f")), A(a("anyArg"), v("f")), A(K, a("pTrue"))))
AL("hasScry", A(Y, a("hasScryGen")))
```

(`pTrue`/`pFalse` are `scry_paths.py`'s booleans. A `Scry` head is true;
otherwise true iff some argument is. Not yet run.)

**(P1), the fuel equation.** Let `E` answer `oNotYet` on a set of paths
`U`, and let `E'` agree with `E` on every path `E` answers `oJust` or
`oNothing`. Suppose `wfP E k ⟨t⟩ = rValN ⟨r⟩` after `s` step-attempts,
the last of which met an unknown head. Then for every `k ≥ s`,

> `wfN E' k ⟨t⟩` and `wfN E' (k − s + 1) ⟨r⟩` are the same outcome.

Why: the arms `stepSN`, `stepKN`, `stepIN` do not mention `e`; the only
arm that does is the `Scry` arm, and `wfP`'s and `wfN`'s `Scry` arms agree
on `oJust` and `oNothing`. So the two loops make identical choices for the
first `s − 1` attempts; at attempt `s`, `wfP` returns `m` and `wfN E'`
consults `E'`; `wfN E'` on `r` consults `E'` at its attempt 1. The `+ 1`
is that attempt. This is `SCRY-BLOCKING-DESIGN.md`'s re-run argument with
the agreement hypothesis stated. It says nothing about `wfP`'s arguments,
which are untouched.

**Checks, all run (`proto/pe_stage1.py`), all as expected:**

| term | oracle | result |
|---|---|---|
| `I K` | not-yet | `rValN ⟨K⟩`; matches `wfN` |
| `K (Scry S) Ω` | not-yet | `rValN ⟨Scry S⟩`; `Ω` never entered |
| `S K K (Scry S)` | not-yet | `rValN ⟨Scry S⟩`: two contractions, then the unknown is head |
| `Scry S K` | not-yet | `rValN ⟨Scry S K⟩`: inert head keeps its arguments |
| `Scry S` | `S ↦ oJust I` | `rValN ⟨I⟩`: a known path still splices |
| `Scry S` | `S ↦ oNothing` | `rErrN` |
| `Ω`, fuel 5 | any | `rTimeN` |
| (P1), `t = S K K (Scry S)`, `s = 3`, `E' = S ↦ I` | | `wfN E' 4 ⟨t⟩ = wfN E' 2 ⟨r⟩ = rValN ⟨I⟩`, and likewise at `k = 6` / `4` |

## 3. Stage 2: depth-bounded normalization under inert heads (`nfP`) — designed, unverified

`wfP` stops when the head is inert; its arguments may still contain
redexes. `nfP` normalizes them, **to a bounded depth**.

**Why the depth bound is not optional.** An earlier version of this
design recursed into arguments without a bound and argued termination
from "the arguments are subterms of the WHNF". That is false: the WHNF's
arguments are subterms of the *reduced* term, which `S` can grow without
limit, and any interpreter state contains an unapplied fixpoint
(`Y wfQGen`, or the loop's own continuation `wfQ e n₂`) in argument
position. `Y f` has no normal form: `Y f → f (Y f) → …`, each step
reaching WHNF quickly and never exhausting a per-call fuel. Unbounded
`nfP` would therefore never terminate on exactly the Futamura residual,
and per-call fuel would not save it. The bound is a Scott numeral `d`
decremented per nesting level; at `d = zero` an argument is left as it is.

```
# the fixpoint f is nfP itself, threaded like spQ threads spApp's f
D("nfArgs2", ["f","e","d","n","h","xs","x1"],
    A(a("nfArgs"), v("f"), v("e"), v("d"), v("n"), A(mkAppQ, v("h"), v("x1")), v("xs")))
D("nfArgs1", ["f","e","d","n","h","x","xs"],
    A(v("f"), v("e"), v("d"), v("n"), v("x"),                       # normalize this argument
      A(a("nfArgs2"), v("f"), v("e"), v("d"), v("n"), v("h"), v("xs")),
      a("rErrN"), a("rTimeN"), a("rBlockN")))                        # failures propagate
D("nfArgs",  ["f","e","d","n","h","acc"],
    A(v("acc"), A(a("rValN"), v("h")), A(a("nfArgs1"), v("f"), v("e"), v("d"), v("n"), v("h"))))
D("nfScry1", ["f","e","d","n","p","rest"],                           # keep the PATH unreduced
    A(a("nfArgs"), v("f"), v("e"), v("d"), v("n"), A(mkAppQ, a("encCQ"), v("p")), v("rest")))
D("nfScry",  ["f","e","d","n","acc"],
    A(v("acc"), A(a("rValN"), a("encCQ")), A(a("nfScry1"), v("f"), v("e"), v("d"), v("n"))))
D("nfVal",   ["f","e","d","n","m"], A(a("spQ"), v("m"), a("nil"),
    A(a("nfArgs"), v("f"), v("e"), v("d"), v("n"), a("encSQ")),
    A(a("nfArgs"), v("f"), v("e"), v("d"), v("n"), a("encKQ")),
    A(a("nfArgs"), v("f"), v("e"), v("d"), v("n"), a("encIQ")),
    A(a("nfScry"), v("f"), v("e"), v("d"), v("n"))))
D("nfDeep",  ["f","e","n","m","d1"], A(a("wfP"), v("e"), v("n"), v("m"),
    A(a("nfVal"), v("f"), v("e"), v("d1"), v("n")), a("rErrN"), a("rTimeN"), a("rBlockN")))
D("nfPGen",  ["f","e","d","n","m"], A(v("d"),
    A(a("wfP"), v("e"), v("n"), v("m")),                              # d = zero: WHNF only
    A(a("nfDeep"), v("f"), v("e"), v("n"), v("m"))))                  # d = suc d1: recurse at d1
AL("nfP", A(Y, a("nfPGen")))
```

Reading it: `nfP e d n m` runs `wfP e n m`; on a value it splits the WHNF
into head and argument list (`nfVal`), normalizes each argument with
`nfP e d₁ n` (`nfArgs1`), re-attaches it (`nfArgs2`), and returns
`rValN` of the rebuilt term. A `Scry` head's path is attached unreduced.
Any argument's failure is the whole result's failure, by the self-wrapping
selectors.

**Fuel and depth policy.** Every sub-normalization receives the same fuel
`n`; total work is bounded by `n × (spine positions visited)`, and the
recursion is bounded by `d`. Additive fuel (returning remaining fuel in
the value payload) is the right thing for a metered specializer and
another payload growth; recorded, not built.

**(P2).** If `nfP E d n ⟨t⟩ = rValN ⟨r⟩` then `t` and `r` are convertible
under any oracle `E'` agreeing with `E` off `U`: every step `nfP` takes is
an object-level contraction or a splice the instantiation would also
perform, so `t →* r` in weak CL extended by the splices, which is
confluent. The fuel equation of (P1) does **not** carry over: `nfP`
reduces inside arguments an instantiation might discard, so `r` may cost
more steps than `t` under some oracles. State (P2) as convertibility only.

**Checks to run when built** (expected values by hand, unverified):

| term | depth | expected |
|---|---|---|
| `S (Scry a) (Scry b) K` | 1 | `Scry a K (Scry b K)` |
| `Scry a (I K) (S K K I)` | 1 | `Scry a K I` |
| `Scry (I K) K` | 1 | `Scry (I K) K`: the path is not reduced |
| `K (S K K I) (Scry a)` | 1 | `I`; `hasScry` false |
| `Scry a Ω`, fuel 5 | 1 | `rTimeN` |
| `Scry a (Y wfQGen)` | 1 | terminates with the argument at WHNF; at depth 0 the argument is untouched |
| (P2), `S (Scry a) (Scry b) K` with `a ↦ K`, `b ↦ I` | 1 | original and residual both give `K`, by `EQ5` |

## 4. Stage 3: the first Futamura projection — verified at the host level, partly at level 2

**Setup.** Level-1 interpreter `wfQ` (synchronous, Maybe oracle, 950
atoms); program `p = I (Scry I)` whose input arrives by scry; the term to
specialize is `wfQ E k ⟨p⟩` with `⟨p⟩` and `k = 5` static and `E` dynamic.
`E` is written as the placeholder `Scry K`, a level-1 leaf whose path `K`
the level-2 oracle answers `oNotYet`:

```
L  =  wfQ (Scry K) 5 ⟨I (Scry I)⟩        # level-1 term, 1,088 atoms
T  =  ⟨L⟩                                 # level-2 datum, 3,263 DAG nodes
```

Instantiation is substitution of a concrete `E₀` for the placeholder
`Scry K` throughout, memoized by node identity.

**What happens.** Level 1's loop runs on `⟨p⟩`: `Y` unfolds, a `suc` is
peeled, the walker reaches `I`, `rbQ` rebuilds, the loop peels again, the
walker reaches the leaf `Scry` of `⟨p⟩`, and level 1's arm `stepScQ1 e p
rest = e p errd (scHit rest)` is reached with `e = Scry K`. The head is
now `Scry K` with six further arguments: `⟨I⟩`, `errd`, `scHit nil`, and
`wfQ1`'s three continuations `wfQ (Scry K) n₂`, `rVal m`, `rErr`. `wfP`
stops and returns this as the residual. Read as a level-1 program: *ask
the oracle for `I`; on a hit, splice and continue the loop with the
remaining fuel; on a miss, report; and here is the value if you stop.*
Every dispatch on `⟨p⟩` before the oracle call has been executed away.

**Verified, host level (`proto/pe_futamura_host.py`).** The host reducer
with `Scry` inert gives the residual in **643** contractions; its head is
`Scry`, its path `K`, its further arguments 6, its DAG 718 nodes.
Instantiated with `E₀ = (every path ↦ just ⟨K⟩)`:

| run | outcome | host contractions |
|---|---|---|
| original `wfQ E₀ 5 ⟨p⟩` | `rVal ⟨K⟩` | 890 |
| residual with `E₀` substituted | `rVal ⟨K⟩` | 247 |
| saved | | **643, exactly the static prefix** |

The saving equals the prefix to the contraction, which is (P1) with the
splice costing nothing at the host (substitution is not a step).

**Verified, level 2.** `wfP E₂ 644 T` runs to `whnf` in **1,351,410**
host contractions, 68 s, 0.20 GB, where 644 = 643 + 1 is the exact fuel
(P1) predicts. Level-2 attempts cost about 2,100 host contractions each
here, against 1,485 for T2, because the walked datum is larger.

**Unverified, level 2** (`proto/pe_futamura_level2.py` is written and ran
to the specialization step; the machine was then saturated by other jobs
and the remaining runs could not complete): that the outer tag is
`rValN`; that the residual's level-2 spine probes to head `X5` (`Scry`),
path `X2` (`K`), six further arguments; that under a level-2 oracle
answering `K ↦ oJust ⟨E₀⟩`, `wfN E₂' 900 T` and `wfN E₂' 257 R` give
`EQ5`-equal values (257 = 900 − 644 + 1), with the residual's minimal fuel
249 succeeding and 248 timing out. These are the (P1) equation at level 2
and should be run before the paper states anything about level 2 beyond
the specialization count.

**What it is not.** The residual still contains `wfQ (Scry K) n₂`, the
interpreter, in the hit continuation; after the oracle answers, the
interpreter resumes interpreting whatever came back. Removing that needs
Stage 4. So the claim is exactly: **the static prefix of the
interpretation is executed at specialization time; the residual is the
interpreter's state at the first dynamic dependency, with all
continuations in place.** It is the first Futamura projection in its
weakest honest form, and it is real: a closed level-1 term with one free
path, which runs 643 contractions faster than the program it came from.
Do not claim Jones optimality. Specializing once costs 1,351,410 host
contractions to save 643 per run; the arithmetic of when that pays is the
ordinary one and should be stated as such.

**Why `wfP` and not `nfP` here.** Stage 1 alone produces the residual,
(P1) applies with its exact fuel equation, and the arguments are
continuation closures whose normalization would unfold `Y` to the depth
bound for no benefit. A program with a longer static prefix (`S K K
(Scry I)` and up) is the better demonstration when the machine allows.

## 5. Stage 4, not designed: unfolding under an unknown head

To remove the interpreter from the residual's continuations, the
specializer must reduce `scHit rest v` and `wfQ (Scry K) n₂ ⟨…⟩` with `v`
*symbolic*, then re-abstract over `v`. In combinatory logic that is
bracket abstraction as a syntactic transformation over encoded terms with
a variable tag: definable, like `EQ5`, but it needs a sixth leaf tag and an
abstraction algorithm as a combinator, and the result equals the original
only extensionally (weak CL has no η). It is also where binding-time
analysis enters. A separate project; the point at which this becomes a
compiler in SKI.

## 6. Files, when built

- `scry_pe.py`, follow-on to `scry_paths.py` (guard-line split). Adds
  `stepScP1`, `stepScP`, `stepPE`, `wfP1`, `wfPGen`, `wfP`, `hasScry` and
  helpers, `nfP` and helpers; a driver `specialize(term, notyet_paths,
  fuel, depth)`; a **memoized** decoder (the `decode_path` of
  `scry_paths.py` is unmemoized and must not be used on residuals); a
  memoized instantiation; the checks of §2, §3, §4; exit 1 on any failure.
  The three `proto/` scripts contain working versions of all of this
  except `nfP` and `hasScry`.
- Paper: a §7.4 "Partial evaluation" after §7.3 with (P1), (P2), the
  643 / 890 / 247 / 1,351,410 figures, and the level-2 agreement once run.
- Nothing in any existing file changes.

## 7. Decisions taken here so the build does not have to

- Unknowns are unanswered `Scry` paths; no new leaf tag until Stage 4.
- "Residual versus value" is a predicate on the result, not a fifth
  outcome.
- `nfP` is depth-bounded; fuel is per sub-normalization; additive fuel is
  recorded, not built.
- Paths are never reduced, including inside residuals.
- The Futamura demonstration uses `wfP`, specializes `wfQ` (Maybe oracle,
  so level 1 has no "block"), and instantiates by memoized substitution.
- Every walk over a residual is memoized by node identity; no tree walks.
- Claims are (P1) with its fuel equation, (P2) as convertibility only, and
  measured savings for Futamura. Nothing stronger.
