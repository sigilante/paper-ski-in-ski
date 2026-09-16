# A Self-Interpreter for SKI, Written in SKI: Authored Failure and a Substitutable Scry Site

*Draft, restructured 2026-09-14 after the review recorded in `REVIEW.md`.
Basis: `tower_harness.py`, `census.py`, `bckw_census.py`, `pipeline.py`,
`scry_harness.py`, `scry_namespace.py`, `scry_paths.py`, the two notebooks,
`SCRY-BLOCKING-DESIGN.md`, and `GATE1-RELATED-WORK.md`, all in this
repository. Every number below was produced by running those files against
`aviary-kernel` 0.1.0 in the session that wrote this draft; the scripts in
`review/` reproduce the brute-force and construction checks. Nock appears
as precedent and analogy only.*

## 0. Abstract

We build a symbolic step-evaluator for SKI combinatory logic as a closed
term of the basis `{S, K, I}`: 618 atoms, all recursion through `Y`, no
host support past the one-time encoding of the input. Run on an encoding
of itself running on a base term, it reaches weak head normal form in
504,930 contractions and agrees with the host's own reduction. The
artifact is small enough to be read whole, and three things about it are
worth reporting. First, a structural census over the `{B, C, K, W}` basis
shows the representation layer is affine (weakening only) while the
interpreter core needs contraction at exactly seven variable occurrences;
representation needs weakening, iteration needs contraction, and
contraction alone already costs normalization. Second, extending the
object language with a fifth constructor forces the interpreter's result
type to grow, and whether the new outcome is exposed as a value or absorbed
into host divergence is a single-arm edit at one named site, measured at
four atoms versus seven in this file, with the two interpreters provably
agreeing on every input that never reaches the site. We read this as a
minimal executable instance of virtualized evaluation in the sense of
Nock's `+mock`, and we state precisely where the analogy breaks: Nock's
virtualization is free because formulas are nouns, while SKI must pay one
external quoting step, which no SKI term can perform (Jay & Given-Wilson
2011, Thm. 3.2). Third, we build the analogy out: a nonlocal scry site in
the style of opcode 12, with the resolver passed as an argument; a blocking
version with a namespace that grows across re-runs; and a namespace over
arbitrary compound paths keyed by a 240-atom structural-equality
combinator, which corrects an earlier claim that such a namespace was out
of reach.

## 1. The artifact

`tower_harness.py` defines the interpreter by named Scott-encoded
definitions and expands them to closed `{S, K, I}` terms. Sizes are
tree-atom counts (`aviary_kernel.terms.size`, which counts atoms and not
application nodes):

| component | tree-atoms |
|---|---|
| `whnfF`, the emulator | 618 |
| `UQ`, the unquoter | 43 |

The script's own banner prints 348 and 62. Those are counts of *DAG nodes*
(atoms plus application nodes, deduplicated by identity, from the local
`size()` at lines 24 to 36), not tree-atoms, which is why the second number
is larger than 43 rather than smaller. Both are correct measurements of
different things; the banner does not yet say which.

![The emulator `whnfF` as a term. Left, the typed-leaf spiral: function edges green, argument edges blue; `S` a filled circle, `K` a square, `I` a ring; the construction rule prunes subtrees below a length cutoff, leaving 48 of the 618 atoms visible. Right, every atom: angle is in-order leaf position, radius is depth, 48 levels. Each fern-like arm is one deeply nested argument, which is what bracket abstraction produces.](figures/fig-pair-whnff.svg)

Targets, all `VERDICT: OK` against the host reducer:

- **T0** `whnfF 3 <I K>`: 340 contractions.
- **T1** the emulator over the unquoter: 91,556 contractions.
- **T2** the tower, the emulator over an encoding of itself over `I K`:
  504,930 contractions. The script's default object fuel of 120 is below
  the 341 the inner run requires, and the script says so; any `--kk` of at
  least 341 gives this count (run at 341 and at 500).
- **T3** the observability pair: §5.

![How `whnfF` evaluates. The fuel loop peels one `suc` per step-attempt; `step` walks the spine to the head leaf, collecting the arguments; dispatch selects the arm for that leaf; a saturated arm contracts and `rb` re-applies the untouched arguments, returning `just ⟨t'⟩` to the loop; an unsaturated head returns `just ⟨t⟩`, the value; exhausted fuel returns `nothing`. The dashed fifth arm is the site of §5.](figures/fig-engine-mechanism.svg)

![The interpreter's components as terms, every atom drawn: the spine walker `sp` (126 atoms), the rebuilder `rb` (74), the three step arms `stepI` (92), `stepK` (105), `stepS` (237), and the unquoter `UQ` (43). Each panel is scaled to its frame, so sizes are not comparable across panels. The `S` arm is the largest because it must build `x z (y z)` as data.](figures/fig-engine-parts.svg)

![The emulator running T0, `whnfF 3 ⟨I K⟩`, after 0, 20, 60, 120, 200, 300 and 340 host contractions, in the spiral view. The spine curls as `Y` unfolds and the encoded term is walked; the tree reaches about 111,000 atoms at step 300 and collapses to the answer, `just ⟨K⟩`, at step 340.](figures/fig-engine-motion.svg)

`ski-in-ski.ipynb` executes end to end with zero errors and prints the
618, 43, and 504,930 figures in its stored outputs (the notebook file now
stores its executed outputs).
`ski-in-ski-aviary.ipynb` builds the same interpreter natively in the
`aviary` kernel and executes with zero errors, but measures no atom counts
and runs no tower; it is a construction walkthrough, not a second
reproduction of the figures.

Three follow-on files extend the object language with a fifth leaf,
`Scry`, and are the subject of §7. Each loads the previous file's
environment and modifies nothing in it, the pattern `pipeline.py`
established:

| component | file | tree-atoms |
|---|---|---|
| `wfQ`, oracle-threaded emulator | `scry_harness.py` | 950 |
| `wfN`, blocking emulator | `scry_namespace.py` | 1,066 |
| `EQ5`, structural equality on encoded paths | `scry_paths.py` | 240 |

All three scripts are self-verifying: each printed claim is checked
against a fresh-marker probe of the reduced value, and each exits 1 if any
check fails (confirmed by injecting a wrong expectation into a copy).

## 2. Encoding is external, decoding is internal

`S K K` and `I` agree on every argument, yet as terms of weak combinatory
logic they are distinct normal forms, 3 atoms against 1. A `quote` function
from live terms to Scott-encoded data must tell them apart, and no SKI
term can. Jay & Given-Wilson, *A combinatory account of internal
structure* (JSL 76(3), 2011), Theorem 3.2, §3: factorisation of
SK-combinators is a symbolic computation that is not representable. The
theorem is stated for `{S, K}`; its proof goes through unchanged with `I`
primitive. Quotation follows from it in two lines. If `Q M ↠ ⟨M⟩` were
definable, then under the translation to λ-calculus `⟦Q⟧ (λx.x)` is one
fixed term, yet `Q (S K X)` yields `⟨S K X⟩`, from which `X` is
extractable by Scott dispatch, so every `X` would share a reduct,
contradicting that `S` and `K` are distinct normal forms. (Equivalently,
`Q` together with this artifact's own `UQ` would build a factorisation
combinator, contradicting Theorem 3.2 directly.)

This is why `enc()` and `encQ()` are Python. Everything on the other side
of that boundary, `UQ`, `whnfF`, their self-application, and everything in
§7 including path equality, is ordinary `{S, K, I}`. Quoting is a one-time
cost paid to enter the representation, and every level above it is closed.
`ski-in-ski-aviary.ipynb` makes this its explicit stopping point ("the
wall", its §8).

![The decoder and a datum. `UQ`, 43 atoms, and the Scott encoding `⟨I K⟩` of the two-atom term `I K`, 40 atoms, each in spiral and every-atom views. A datum and a program look alike because in this calculus they are the same kind of thing; only the encoding step that produced `⟨I K⟩` lies outside it.](figures/fig-pair-uq-ik.svg)

## 3. Where the structural cost lives

`census.py` and `bckw_census.py` rebuild each component over `{B, C, K, W}`
and record which structural rule each needs, weakening (`K`) or contraction
(`W`). The measurement that is independent of the abstraction algorithm is
the *occurrence* census (`census.py` §1): a component needs weakening iff
some binder occurs zero times and contraction iff some binder occurs more
than once. The atom census is convention-relative and the scripts say so:
with `I` primitive the interpreter core shows 7 `W` atoms, with `I = W K`
it shows 10, and under the latter convention even the encoding layer shows
4.

**The representation layer is affine.** All ten Scott constructors
(`enc<S>`, `enc<K>`, `enc<I>`, `enc<app>`, `nil`, `cons`, `nothing`, `just`,
`zero`, `suc`) have no binder occurring twice: a constructor selects one
continuation and discards the rest, which is weakening by construction.
The representation lives in BCK.

**The interpreter core needs contraction at five of eight components,
seven surplus occurrences in total:** `UQ`'s `f` (twice, in `(f t)(f u)`),
the spine generator's `acc` (four times), the rebuild generator's `h`
(twice), the `S`-step arm's `z` (twice, in `x z (y z)`, which is the `S`
rule itself reappearing one level up), and the fuel loop's `m` (twice).
Surplus occurrences sum to `1 + 3 + 1 + 1 + 1 = 7`, and any BCKW
abstraction must perform at least that many contractions. The differential
check (18/18 SKI and BCKW abstractions extensionally agree; the purity
guard accepts pure-basis terms and rejects mixed ones) confirms the
abstractions are correct; it does not bear on the census, and is not cited
for it.

**Why each rule is needed.** Removing weakening removes dispatch: a Scott
constructor *is* an n-ary discard. Removing contraction removes iteration:
`Y` duplicates its argument, and the affine fragment BCK is strongly
normalizing, so it has no fixpoint combinator and no fuel loop. (The fuel
itself is a Scott numeral, which is affine; iteration here comes from `Y`,
not from the numeral.) Self-interpretation therefore needs both rules for
two different reasons. The asymmetry is worth stating exactly: contraction
alone already costs normalization. `(S I I)(S I I)` contains no `K`, and in
BCKW `W W W` reduces to itself with no weakening anywhere; the relevant
fragment BCIW is not normalizing while BCK is. So the rule that buys
iteration is the rule that costs normalization, and weakening is bought for
representation, not for divergence.

## 4. Fuel and the third outcome

An unfueled interpreter's outcome space is `{value, divergence}`, and
divergence cannot be observed from inside a finite run. Fuel converts it to
`{value, timeout}`, both observable. The precise limitation is local: at
any fixed fuel `k`, one observation does not separate a divergent term from
one that needs more than `k` steps. `Ω` reports `TIMEOUT` at every `k`;
`I³¹K` reports `TIMEOUT` for `k ≤ 31` and a value from `k = 32` on (31
contractions, and fuel `k` permits `k` step-attempts of which the last must
be the no-redex check). Convergence is semi-decidable by raising `k`;
divergence is not. `K I Ω` still discards `Ω` unevaluated under the
emulator, exactly as under host reduction, because the object-level `K`
rule fires before the interpreter recurses into the argument: object-level
laziness is inherited, not re-implemented.

Amin & Rompf's framework (*Collapsing Towers of Interpreters*, POPL 2018)
supports a rich family of semantic modifications across tower levels:
instrumentation and CPS transformation (their §4.2), `EM`, `call/cc` and
`shift`/`reset` at user level, reflection à la Black, and meta-level undo
(§5 to §7). Their correctness and optimality properties (Props. 4.2 to
4.7, of which 4.5 is a definition) are, in their words, "stated without
formal proofs but backed by experimental evidence" (§4.1, p. 11). The word
"fuel" does not occur in the paper, and no outcome-type that must grow when
the object language gains a construct is discussed. Their collapse is a
collapse of value-producing computation; the third outcome is outside the
space their equivalences range over.

## 5. Authored failure: one site

Extend the object language with a fifth constructor `Err`, with no
object-level contraction rule. Its Scott encoding is unremarkable, five
continuations instead of four. What is interesting is what the interpreter
does when the spine walker reaches `Err` in head position, and that is a
choice made at one site:

```
D("errArmAbs", ["acc"], a("errd"))      # observable: crash becomes a value
D("errArmOmg", ["acc"], OMEGA)           # hidden: crash becomes host divergence
```

(`tower_harness.py` lines 217 to 218, verbatim.) Expanded, the arms are
`K (K (K I))` at 4 tree-atoms and `K (S I I (S I I))` at 7; the two full
emulators `wf5Abs` and `wf5Omg` measure 768 and 771 and differ at exactly
this one definition site. The measurement is of this file, not a minimum:
the `K` wrapper on `Ω` is unnecessary, since `Ω acc` diverges as `Ω` does,
and a 6-atom arm reproduces the table below cell for cell
(`review/omg6.py`). Even the 4 depends on the abstraction algorithm's
η and `I` shortcuts. The honest statement is a single-digit-atom edit at
one named site.

![The two arms of the authored site. `errArmAbs = K (K (K I))`, 4 atoms, exposes the crash as a value; `errArmOmg = K (S I I (S I I))`, 7 atoms, absorbs it into divergence. The two emulators differ by exactly these atoms.](figures/fig-arms.svg)

`Ω = (S I I)(S I I)` is one of the smallest divergent terms in this basis,
not the unique one. Exhaustive enumeration of every `{S, K, I}` application
tree of at most 6 atoms (`review/brute2.py`; the counts match
`3ⁿ · Catalan(n−1)`, so the enumeration is complete) finds that all 3,873
terms of at most 5 atoms reach a normal form, and exactly five terms of 6
atoms do not, under both "no normal form" and "no weak head normal form":
`S I I (S I I)`, `S (S I)(S I) I`, `S S S (S I) I`, `S S I (S I) I`, and
`S (S S) S I I`. (Tromp notes that in `{S, K}` alone the smallest unsolvable
term is `S S K (S (S S K))`, 7 atoms; consistent with the enumeration, since
all five 6-atom divergent terms contain `I`.)

Re-run and verified:

| object term | exposing (`errArmAbs`) | hiding (`errArmOmg`) |
|---|---|---|
| `Err` | ERR | host diverges |
| `Err K` | ERR | host diverges |
| `K I Err` | VAL | VAL |
| `I K` | VAL | VAL |
| `Ω` | TIME | TIME |

"Host diverges" is the host reducer's 400,000-step cap being hit; it is
not a detected non-termination, though it is certain here because the arm
*is* `Ω`.

**Lemma (faithfulness off the site).** For every object term that never
brings `Err` into head position during its reduction, `wf5Abs` and
`wf5Omg` produce the same result. The two definitions differ only in
`errArm`, which is referenced only from the `Err` arm of the step function,
which the spine walker selects only when the head leaf is `Err`. On any
other input the two are the same program. The table's `K I Err` row is the
instance where `Err` is present but discarded by object-level laziness
before it is ever in head position.

Adding a constructor does not add a meaning. The meaning is authored
downstream by whoever writes the interpreter, and here the whole decision
is legible as a one-arm diff with a proof that nothing else changed.

## 6. Virtualized evaluation, read against `+mock`

Nock's `+mock` is not interesting because Nock can interpret Nock; that
follows once a formula computes `nock`, since a formula already is a noun.
Its interest is that a formula can be run through a *substituted*
interpreter, one that resolves a scry differently or catches a crash and
returns it as a `unit`, while agreement with the reference interpreter
holds wherever the substitution is not exercised, and the substitution is
confined to a named site.

Read that way, §5 is the SKI analogue of `+mock`, not §1's tower. The
tower demonstrates self-interpretation and fidelity; a general version of
that demonstration exists for value-producing towers (Amin & Rompf, Props.
4.2 and 4.6). What `errArmAbs` versus `errArmOmg` demonstrates is the thing
`+mock` is for: the same program, the same interpreter apart from one arm,
different observable outcomes because that arm decides what one outcome
category is allowed to be. The lemma in §5 is the faithfulness requirement,
virtualized-with-no-substitution equals real, and `pipeline.py`'s Stage 6
check and T0 to T2 are its instances.

**Where the analogy breaks.** `+mock` never needs a quoting step, because a
Nock formula already is the noun handed to the alternate interpreter. SKI
is not homoiconic: `S`, `K`, `I` are opaque, and §2 is precisely the
statement that no SKI term can turn an arbitrary SKI term into data about
itself. So SKI-in-SKI is not symmetric the way Nock-on-Nock is. It is one
unavoidable non-SKI quoting step, and only above that boundary is
virtualization SKI-native and closed under further quoting. Identifying
which half of "virtualized evaluation" transfers to a non-homoiconic
calculus is worth more than the analogy alone.

**Depth is bounded for the ordinary reason.** Layer one costs 340
contractions to emulate a 1-step reduction; layer two costs 504,930, about
1,485 times layer one. That is the familiar roughly-10³× per-layer overhead
of naive self-interpretation, not a measurement this artifact is claiming
(`GATE1-RELATED-WORK.md`, A3). A third level was not attempted. Real
Nock-on-Nock virtualization has the same character, which is why jets
exist.

## 7. Substitutability as an argument: the scry site

### 7.1 Synchronous: `scry_harness.py`

§5's substitution is a compile-time choice between two source variants.
Real scry substitution takes the resolver as an argument. `scry_harness.py`
builds that: a separate 5-symbol encoding `{S, K, I, App, Scry}` (parallel
to `{S, K, I, App, Err}`, not stacked on it; `Scry` has arity 1 like `I`),
and a fueled loop `wfQ E n <t>` whose extra argument `E` is an ordinary
Scott-encoded `{S, K, I}` partial function from paths to `Maybe` values.
When the spine walker reaches `Scry p` it applies `E` to `p`. A hit splices
the answer in and reduction continues. A miss is kept as a third,
distinguishable step outcome, reusing T3's `stepped`/`done`/`errd`, rather
than folded into the pre-existing `Maybe`, which would conflate "the oracle
had no answer" with "genuinely stuck". At the outer result type the three
points are `{value-or-stuck, miss, timeout}`: `done` maps to `rVal`, so
stuck and value share a tag there, and the stuck/miss distinction is a
step-level fact.

The path reaches the oracle as Scott-encoded data, exactly as written and
unreduced. Verified against three oracles (answer every path by echoing it;
answer none; dispatch on the path's head leaf and answer only `K`):

| test | result |
|---|---|
| `I K`, no `Scry`, either oracle | matches base `whnfF` exactly |
| `I (Scry K)`, echo oracle | hit; decodes to the answer |
| `I (Scry K)`, never oracle | miss, distinct from stuck |
| `Scry` alone, unsaturated | stuck (`done`), neither hit nor miss |
| `K K (Scry K)`, never oracle | reduces to `K`; the site is never consulted |
| `Scry K` / `Scry (S K K)`, head oracle | hit / miss, path-dependently |
| `Scry (I K)`, head oracle | miss: `I K` is not the path `K` (a probe in this session; not among the script's own checks, which `scry_paths.py`'s syntactic-versus-semantic rows cover) |
| `Ω`, fuel exhausted first | timeout, not a miss |

The laziness row is the same mechanism as `K I Ω` in §4, now for a
nonlocal effect: a scry site inside a branch the program never forces is
never consulted. Substitutability does not require eagerness.

### 7.2 Blocking: `scry_namespace.py`

A resolver that always answers is still not `+mock`'s scry: a real lookup
can fail to answer *yet*. `scry_namespace.py` builds the cheapest faithful
version, option (a) of `SCRY-BLOCKING-DESIGN.md`, written before any of it
was implemented. The resolver's type grows from 2-way `Maybe` to 3-way
(`oJust`/`oNothing`/`oNotYet`) and the interpreter's outcome types grow to
match (`pendingN` at the step level, `rBlockN` at the result level). This
is the phenomenon of §5 again, deliberately re-triggered by our own
extension rather than discovered.

Resuming a block captures no continuation. Because reduction is pure and
deterministic, the driver re-runs the whole term from the top under an
oracle that now also answers the missing fact. Two things make that sound,
and both need saying. First, the re-run's steps *strictly before* the block
are identical to the first run's only if the new oracle agrees with the old
one on every path the old one answered; that holds because the namespace is
append-only, and an oracle that revised an answer would break it. Second,
re-running is not fuel-neutral. Each round replays the previous one and
then takes at least one more step, so with a fixed fuel budget a block can
turn into a timeout on the next round:

```
Scry (S K), fact (S K)=I, fuel=1 -> [(1, 'BLOCK on S K'), (2, 'TIME')]
Scry (S K), fact (S K)=I, fuel=2 -> [(1, 'BLOCK on S K'), (2, 'VAL')]
```

Recomputation is charged for. The two heavier resume strategies in the
design note, resume from the top-level term and full CPS (the move Amin &
Rompf's CPS evaluator makes, their §4.2.2), remain unbuilt.

What is SKI and what is host, stated plainly: `wfN` and each round's oracle
term are closed `{S, K, I}`; the fact table standing in for an external
source of truth, the resume loop, and the "stuck" detection are Python.

The demonstration that matters is that the namespace accumulates. With an
empty namespace and a fact table `{S ↦ Scry K, K ↦ I}`, `Scry S` blocks on
`S` (round 1), learns it, re-runs, and the newly substituted `Scry K` blocks
on `K` (round 2), a fact forced by the result of resolving the first,
before round 3 reaches the value `I`. A path with no entry blocks into a
distinguishable stuck state; fuel exhaustion stays distinguishable from a
block at every round.

### 7.3 Compound paths: `scry_paths.py`

`scry_namespace.py` dispatched on a path's head leaf only, so its namespace
could not tell `S K` from `S K K`. An earlier draft of this paper, and that
file's docstring, said this was forced: that comparing arbitrary encoded
paths was "the structural-equality problem Jay & Given-Wilson show plain
SK cannot solve." That was wrong, and the review caught it. Theorem 3.2
is about factorising *live* combinators. The path the oracle receives is
Scott-encoded *data*, a tree with five leaf tags, and equality on such data
is an ordinary structural recursion. Jay & Given-Wilson say so themselves
(preprint pp. 7 to 8): once a term is encoded, factorisation "is a routine
list operation." What SK cannot do is produce the encoding from a live term,
which is §2, and it is the only thing SK cannot do here.

`scry_paths.py` builds `EQ5`, structural equality on the five-constructor
encoding, at 240 tree-atoms in `{S, K, I}`, and an oracle that compares the
incoming path against each known path in turn:

```
p |-> EQ5 p <k1> (oJust <a1>) (EQ5 p <k2> (oJust <a2>) (... oNotYet))
```

It runs inside `wfN` unchanged. Forty-one checks pass, among them:

| test | result |
|---|---|
| `EQ5 <S K K> <I>` | false (the pair §2 turns on) |
| `Scry (S K)`, fact `(S K) ↦ I` | block, then `I` |
| `Scry (S K)`, only fact `(K S) ↦ I` | block, stuck; no false hit |
| `Scry (S K K)` vs `Scry (S K)`, facts for both | `K` and `I` respectively: a path and its own prefix are distinguished |
| `Scry (K I)`, facts `(K I) ↦ Scry (S K)`, `(S K) ↦ I` | three rounds, chained through a compound answer |
| `Scry (I K)`, only fact `K ↦ S` | stuck: paths are compared as written, not up to conversion |
| `Scry (I K)`, fact `(I K) ↦ S` | `S` |

![`EQ5`, structural equality on encoded paths, 240 atoms: 92 `S`, 118 `K`, 30 `I`. Spiral view, 68 atoms visible, beside the every-atom disc.](figures/fig-pair-eq5.svg)

The last two rows are the design point. Paths are intensional, syntactic
objects, compared by structural equality of their encodings, exactly as a
Nock scry path is a noun compared by noun equality. Matching paths up to
conversion would be the word problem for SKI, undecidable; normalizing the
path under fuel before lookup would be a fueled approximation to it and
would reintroduce the third outcome inside path resolution. Nothing built
here does either. A three-fact compound-path oracle term measures 1,022
tree-atoms; the driver's decoder from an encoded payload back to an object
term, needed to consult the Python fact table, is a behavioral
fresh-marker probe, and its round trip is checked.

## 8. Prior art, and what is claimed

Self-interpretation for a Turing-complete system is old. Kleene 1936 gives
the Normal Form Theorem, from which a universal function follows; the
explicit universal machine is Turing 1936; "partial recursive" is Kleene
1938. Mogensen 1992 builds a compact self-interpreter and self-reducer in
untyped λ-calculus over his own term representation. Jay & Palsberg 2011
build a typed self-interpreter in a factorisation calculus in the style of
Jay & Given-Wilson, a combinatory calculus though not SK, and their
distinction between self-*recognisers* (recover the term from its
representation) and self-*enactors* (execute it) is the one this paper
needs below.

The closest prior construction for SK is Tromp, *Binary Lambda Calculus and
Combinatory Logic* (Dagstuhl Seminar Proceedings 06051, 2006; the 2023
revision at `tromp.github.io` has different sizes and should not be cited
for these). Theorem 3 gives a λ-term `F` of size 124 with
`F C (M̃ : N) = C M N` for the bitstring encoding `M̃` of a combinator
`M`; its verification is "left as an exercise to the reader." Theorem 4
states, in full, "There is a self-interpreter F for Combinatory Logic of
size 263," obtained from Theorem 3 by improved bracket abstraction and a
different fixpoint combinator (`Y''`); it has no proof text beyond size bookkeeping,
and the inductive proof in the paper is for the λ-calculus interpreter of
Theorem 2. With `C = I`, `F I (M̃ : N) = M N` is a self-enactor, and
Tromp's §4.1 uses it that way for universality. Architecturally `F` is a
decoder: it reconstructs live syntax from bits and hands it to a
continuation, and reduction then happens under the ambient calculus's own
rules. It carries no object-level `S` or `K` rule in its body, which means
it cannot implement a step relation that differs from the host's, and that
is exactly what §5's hiding arm does. The paper also contains (pp. 16 to
18) `nfreduce`, "a complete symbolic lambda calculus normal form reducer"
over Scott-encoded de Bruijn terms with explicit substitution, used as a
2,288-bit size constant: a symbolic evaluator over encoded data, for
λ-calculus, unfueled, not self-applied, and not run.

So the claim is narrow. A symbolic step-evaluator for SKI written in
λ-calculus is a textbook exercise, and bracket abstraction carries it into
`{S, K, I}` mechanically. What this artifact adds is the concrete term:
618 atoms, fueled, with its step rules as data manipulation rather than
re-spliced host syntax, applied to an encoding of itself, and executed to
completion with the count reported. On top of that term, §3's census, §5's
one-site authorship with its faithfulness lemma, and §7's substitutable,
blocking, compound-path scry site are, to the extent of a full read of the
closest papers, not found elsewhere. Amin & Rompf's outcome space has no
failure case to author (§4); Jay & Given-Wilson's result is about what SK
cannot do to live terms, not about what an interpreter that can be written
chooses to expose.

## 9. Adjacent, distinct work

Two lines of work in this same environment operate over a different basis
and question, and are context rather than sources:

- **Infinitary normal forms in the pure S-calculus** (companion draft,
  `Documents/Davis2026b`) studies `CL(S)`, the calculus generated by
  `S x y z → x z (y z)` alone, no `K`, no `I`, and writes out in detail
  (crediting the observation to an aside in Waldmann's thesis, §7.6) that it
  is infinitarily strongly normalizing: every term has a unique, possibly
  infinite normal form, a Böhm-tree analogue with no `⊥` needed. Its slogan,
  that `K` "purchases computational universality at the cost of infinitary
  semantic coherence," is the same style of result as §3 here, attributing a
  capability and its cost to one specific structural rule. Note that the
  `Ω` of §5 contains `I` and is not a `CL(S)` term; that paper's divergent
  example is the pure-`S` term `S S S (S S) S S`, and it is explicit that
  once `K` is present the Böhm-tree theory needs quotienting and `⊥`. The
  two papers treat divergence with different tools, denotational there and
  operational (fuel) here, on different fragments.
- **`ssearch`** (`Documents/ssearch`) is a computational classification of
  divergent pure-`S` orbits by the structure of their infinite spine
  dynamics, in service of the Wolfram `S`-combinator universality question.
  Same author, adjacent, not a dependency.

## 10. Open threads

- **Self-quotation above level 0.** Jay & Given-Wilson 2011 makes no claim
  about it (its §8, "Structure Completeness," is about `S, K, F, eqatom`
  and pattern matching; the word "quotation" does not occur). If a stronger
  claim is wanted it needs Jay, *Programs as Data Structures in
  λSF-Calculus* (ENTCS 325, 2016) or Jay, *Self-Quotation in a Typed,
  Intensional Lambda-Calculus* (MFPS XXXIII, 2017; ENTCS 336, 2018), neither
  read.
- Kavvos, *On the Semantics of Intensionality and Intensional Recursion*
  (arXiv 1712.09302), and the differential-testing literature remain unread;
  `GATE1-RELATED-WORK.md` §5 says why each matters.
- `tower_harness.py`'s banner should label its counts as DAG nodes (atoms
  plus applications), distinct from the tree-atom counts used here.
- The 6-atom hiding arm is verified but not adopted; adopting it would edit
  the base file, which every follow-on loads.
- `SCRY-BLOCKING-DESIGN.md` options (b) and (c) remain sketches. Given that
  re-run-from-scratch charges fuel for every replayed prefix (§7.2), (b) is
  the natural next step if round counts grow.
- A pure-SKI unquoter for the five-constructor encoding (the `UQ` of
  `{S, K, I, App, Scry}`) is not built; the driver's decoder is host-side.
- Whether to normalize paths under fuel before lookup (§7.3) is a design
  choice with a named cost; it is recorded, not made.

## Appendix: the emulator as an expression

The terms drawn in Figures 1 and 5, written out. Application is
juxtaposition and associates to the left; parentheses are only where
association is to the right; line breaks fall at spaces and carry no
meaning. Both are exactly what `expand()` produces from the named
definitions under `aviary_kernel.abstraction`'s bracket abstraction, so
their atom counts are algorithm-relative in the sense of §5; the atom
counts below were re-checked against the printed strings. Both begin with
the same fourteen atoms, `S (K (S I I)) (S (S (K S) K) (K (S I I)))`, which is
`Y`: each is a fixpoint of its generator, `UQGen` and `wfGen` respectively.

`UQ`, the unquoter, 43 atoms:

```
S (K (S I I)) (S (S (K S) K) (K (S I I))) (S (K (S (S (S (S I (K S)) (K K))
(K I)))) (S (K K) (S (S (K S) (S (K (S (K S))) (S (K K)))) K)))
```

`whnfF`, the emulator, 618 atoms:

```
S (K (S I I)) (S (S (K S) K) (K (S I I))) (S (K (S (S (K S) (S (K K) (S I (K
K)))))) (S (K K) (S (K (S (S (K S) (S (K K) (S (S (S (S (S (S (K (S I I)) (S
(S (K S) K) (K (S I I))) (S (K (S (S (K S) (S (S (K S) (S (S (K S) (S (S (K
S) K) (K (S (K (S (K K))) (S (K (S (K K))) (S (K (S I)) K)))))) (K (S (K K)
(S (K (S (K K))) (S (K (S I)) K)))))) (K (S (K K) (S (K K) (S (K (S I))
K)))))))) (S (K K) (S (S (K S) (S (K K) (S (K S) (S (K (S (K S))) (S (K
K)))))) (K (S (K K) (S (K (S (S (K (S (K K))) (S (S (K S) (S (K K) (S (K S)
(S (K (S I)) K)))) (K K))))) K))))))) (K K)) (K (S (S I (K K)) (K (S (K (S
(S I (K K)))) (S (K K) (S (K (S (K (S (S I (K K)))))) (S (K (S (K K))) (S (K
(S (K (S (K (S (K (S (K K) (S (K (S I)) K))))))))) (S (K (S (K (S (K (S (K
(S I I)) (S (S (K S) K) (K (S I I))) (S (K (S (S (K S) (S (K (S I)) K)))) (S
(K (S (K K))) (S (S (K S) (S (K K) (S (K S) K))) (K (S (K (S (K K))) (S (K
(S (K K))) (S (K (S (K K))) (S (S (K S) (S (K K) (S (K S) (S (K (S I)) K))))
(K K))))))))))))))) (S (S (K S) (S (K K) (S (K S) (S (K (S (K (S (K (S (K
K))) (S (K (S (K K))) (S (K (S (K K))) (S (S (K S) (S (K K) (S (K S) (S (K
(S I)) K)))) (K K)))))))) (S (K (S (K K))) (S (K (S (K K))) (S (K (S (K K)))
(S (S (K S) (S (K K) (S (K S) (S (K (S I)) K)))) (K K))))))))) (K (S (K (S
(K K))) (S (K (S (K K))) (S (K (S (K K))) (S (S (K S) (S (K K) (S (K S) (S
(K (S I)) K)))) (K K))))))))))))))))) (K (S (S I (K K)) (K (S (K (S (S I (K
K)))) (S (K K) (S (K K) (S (K (S (K (S (K K) (S (K (S I)) K))))) (S (K (S I
I)) (S (S (K S) K) (K (S I I))) (S (K (S (S (K S) (S (K (S I)) K)))) (S (K
(S (K K))) (S (S (K S) (S (K K) (S (K S) K))) (K (S (K (S (K K))) (S (K (S
(K K))) (S (K (S (K K))) (S (S (K S) (S (K K) (S (K S) (S (K (S I)) K)))) (K
K)))))))))))))))))) (K (S (S I (K K)) (K (S (K (S (K (S (K K) (S (K (S I))
K))))) (S (K (S I I)) (S (S (K S) K) (K (S I I))) (S (K (S (S (K S) (S (K (S
I)) K)))) (S (K (S (K K))) (S (S (K S) (S (K K) (S (K S) K))) (K (S (K (S (K
K))) (S (K (S (K K))) (S (K (S (K K))) (S (S (K S) (S (K K) (S (K S) (S (K
(S I)) K)))) (K K))))))))))))))) (S (K K) (S (K (S I)) K))))))) K)))
```

The strings are also in `figures/uq-43.txt` and `figures/whnff-618.txt`.
