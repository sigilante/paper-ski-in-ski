# Review of `PAPER.md` (draft as of 2026-09-14)

> **Status (2026-09-14, after the review):** every item in sections A, B,
> and C below has been applied, and the four decisions in section F were
> all taken in favour of the first option: `scry_paths.py` now builds the
> compound-path namespace (`EQ5`, 240 tree-atoms, 41 checks, exit 1 on
> failure); the site edit is reported as measured with the 6-atom arm
> noted; `PAPER.md` was rewritten as an artifact paper; and
> `ski-in-ski.ipynb` stores its executed outputs. Stale text was also
> corrected in `SCRY-BLOCKING-DESIGN.md`, `GATE1-RELATED-WORK.md` (Prop
> 4.6), the comment blocks of `census.py` and `bckw_census.py`, and the
> docstring of `scry_namespace.py`. No interpreter code in any
> pre-existing file changed; all pre-existing scripts still exit 0 with
> identical checks. The findings below are kept as written, as the record
> of what was wrong.

Four independent passes were run: a formal-claims review (every "provably",
"exactly", "cannot", "never" in the paper, plus brute-force and construction
probes), a ground-truth pass that re-ran every script and reproduced every
number, a paper-versus-artifact fidelity pass over the code, the design docs,
and the notebooks' markdown, and a primary-source pass that downloaded the
cited PDFs and checked each citation against the text. Every finding below
that came from an agent was then re-run or re-read directly before being
recorded here. The scripts that produced the evidence are in `review/` and
run from the repository root (`python3 review/<name>.py`). No file outside
`review/` and this one was modified.

**Verdict.** Every number in the paper reproduces exactly. The artifact and
the §6 authored-failure result are sound. The reasoning layered on top of
the numbers has errors, three of them serious: one retracts §7.2's scope
argument, one is a false mathematical statement in §4, and one is a wrong
citation characterization in §1. None of them touches the headline result.

---

## A. Errors that must be corrected

### A1. §7.2 and §9: structural equality on encoded paths is not blocked by Jay & Given-Wilson Thm 3.2 (lines 424–432, 500–504)

The paper says compound-path matching "is exactly the structural-equality
problem Jay & Given-Wilson (§3, Thm. 3.2) show plain SK cannot solve." This
is wrong. The oracle receives the path as Scott-encoded data (traced through
`spGenQ` → `resCQ` → `stepScQ1` in `scry_harness.py`; confirmed by probing
the echo oracle, which returns the encoded `App` node for `Scry (S K K)`).
Equality on Scott-encoded trees is an ordinary structural recursion,
definable in `{S,K,I}` with `Y`. Jay & Given-Wilson say so themselves
(preprint pp. 7–8): once a term is encoded as a list, factorisation "is a
routine list operation"; Theorem 3.2 is about *live* combinators only.

Constructed and verified: `review/eqtest.py` builds `EQ`, a 173-tree-atom
`{S,K,I}` equality on the 4-constructor encoding (14 test pairs, including
`EQ <S K K> <I> => FALSE`). `review/eq5ns.py` builds the 5-constructor
`EQ5` (240 tree-atoms) and drops a compound-path namespace oracle into the
**unmodified** `wfN` from `scry_namespace.py`:

```
Scry (S K)   with namespace {(S K)->I}            -> VAL   leaf=I
Scry (S K)   with namespace {(K S)->I}            -> BLOCK leaf=None
Scry (S K K) with ns {(S K)->I,(S K K)->K}        -> VAL   leaf=K
Scry (S K)   with ns {(S K K)->K,(S K)->S}        -> VAL   leaf=S
```

Rows 3 and 4 distinguish a compound path from its own proper prefix. The
bare-leaf restriction is an engineering shortcut, not a theorem-forced
boundary. The paper conflates (i) factorisation of live SK terms, which
Thm 3.2 does block and which is why `enc()` is Python, with (ii) equality
of encoded data, which is routine and simply was not built.

Correct statement: "paths reaching the oracle are already data, so equality
on them is definable (a 240-atom combinator suffices); only bare-leaf
dispatch was implemented." The last bullet of §9 should drop the claim that
Jay's 2016/2017 papers gate this.

Related: the paths are compared *syntactically*, not up to conversion.
`Scry (I K)` misses under the head-dispatching oracle while `Scry K` hits,
even though `I K` reduces to `K`. This is the right design (it matches
noun equality on Nock paths, and matching up to conversion would be the
undecidable word problem), and the paper should say it.

### A2. §4: "Church numerals ≥ 2 need `W` exactly `n − 1` times" is false and unmeasured (lines 200–201, framed as algorithm-independent at 182–186)

- `bckw_census.py` contains no code constructing a Church numeral; the
  claim exists only in a comment block (line 116) that says "verified".
- Under the repository's own declared convention `I = W K`
  (`census.py` line 46 of output), the count is `n`, not `n − 1`, for every
  `n` (`review/church.py`).
- As a statement about BCKW terms denoting Church numerals it is false:
  `2 (2 2)` denotes Church 16 with 3 `W` atoms (`review/bckw_red.py`,
  independent BCKW reducer, normal form checked as `f^16 x`).
- It is irrelevant to this interpreter: fuel is a Scott numeral, which is
  affine (`zero W=0, suc W=0`); iteration comes from `Y`.

Replacement that is true and sufficient for §4's argument: a Church numeral
`n ≥ 2` has its binder `f` occurring `n` times, so it is not affine; `Y`'s
self-application is likewise a duplicated occurrence; and the affine
fragment BCK is strongly normalizing, so it has no fixpoint combinator and
no fuel loop. Contraction is what buys iteration.

### A3. §4: "the basis admitting both is exactly the basis where `Ω = (SII)(SII)` lives" (lines 204–206; also copied into `census.py` and `bckw_census.py` comments)

`(SII)(SII)` contains no `K`. Divergence needs contraction only: `W W W`
reduces to itself in BCIW with no weakening anywhere, and `Ω` is a λI-term.
So "admits weakening and contraction" is sufficient for `Ω`, not necessary,
and "exactly" is false. The sharper true statement: dispatch needs `K`,
iteration needs `W`, and `W` alone already costs normalization (BCK is
strongly normalizing; BCIW is not).

### A4. §1: Tromp's Theorem 4 is mischaracterized, and the "nothing closer" claim is too strong (lines 57–83)

Checked against the Dagstuhl 2006 PDF (`DagSemProc.06051.4`):

- The equation `F C (M̃:N) = C M N` is **Theorem 3** (cross-interpreter,
  size 124, a λ-term). **Theorem 4** reads, in full: "There is a
  self-interpreter F for Combinatory Logic of size 263." It has no equation
  and no proof text beyond the size bookkeeping in §3.2.
- Theorem 4 is **not** "established by induction on term structure (via
  Theorem 2's proof)". The induction on `M` (p. 5–7) proves Theorem 2, the
  λ-calculus self-interpreter `E`. For Theorem 3, Tromp writes:
  "Verification is straightforward and left as an exercise to the reader."
- "Nothing in Tromp's `F` performs a contraction step" is ill-formed as
  written (evaluating `F` *is* a sequence of ambient contractions). The
  meaningful claim is that `F` carries no object-level `S`/`K` rewrite rule
  in its own body; a decoder cannot implement a step relation different
  from the host's, which is exactly what `errArmOmg` does. That is the
  argument §1 should make, and it is the one that connects to §6.
- Tromp pp. 16–18 contain `nfreduce`, described as "a complete symbolic
  lambda calculus normal form reducer" over Scott-encoded de Bruijn terms,
  with explicit substitution, used as a 2288-bit size constant. It is for
  λ-calculus, unfueled, not self-applied, and not run, but it is a symbolic
  evaluator over encoded data in the sense §1 claims is unpublished.
  "This search found nothing closer" must be narrowed to: for SK/SKI, as a
  fueled step-evaluator, self-applied, and actually executed.
- Note also that a symbolic SKI evaluator in λ-calculus (which Mogensen's
  style gives) becomes one in `{S,K,I}` by bracket abstraction, a textbook
  translation. The genuine residue is the artifact claim: compiled to a
  concrete 618-atom term, self-applied, executed in 504,930 contractions.
  Say it that way.
- `tromp.github.io/cl/LC.pdf` is the 2023 revision ("Functional Bits") with
  different sizes (206/119/263). Cite the Dagstuhl PDF specifically.

### A5. §2: the 618/348 and 43/62 discrepancy is misdiagnosed (lines 118–123, and the §9 "one-line fix" bullet)

"DAG-aware and collapses subterms" cannot explain 62 > 43. Two differences
are in play: `aviary_kernel.terms.size` counts **atoms only**;
`tower_harness.size()` (lines 24–36) counts **all DAG nodes, atoms and
applications**, deduplicated by identity. `UQ` has 43 atoms, 85 tree nodes,
62 DAG nodes (`review/sizes.py`). The correct labels are "tree-atoms" vs
"DAG nodes (atoms + applications)".

### A6. §5: Amin & Rompf's propositions are not "proved" (line 227–228)

§5 says their correctness propositions "are proved for exactly this class."
§1 correctly says the opposite. The paper (p. 11, §4.1): "We state these
properties without formal proofs but backed by experimental evidence." Also:
4.5 is a Definition, not a Proposition; CPS transformation and the first
tracing example are in §4.2, not §5–7; the counter is §6.1, undo is §7.4,
call/cc and shift/reset via EM are §5.1.3. Suggest "§4.2 and §5–7".
`GATE1-RELATED-WORK.md` §7.1 also misstates Prop 4.6: the top-level argument
is `evalc-src` and the relation is `⇓`, not `≡`.

### A7. §8: `Ω = (SII)(SII)` is not a `CL(S)` term (lines 452–457)

The companion draft studies `S`-only terms and never mentions `Ω`, `SII`, or
`I` (grep: zero hits). Its only divergent example is
`W = S S S (S S) S S`. With `K` present the draft says the Böhm-tree theory
"requires quotienting by hypercollapsing terms and adjoining ⊥". So `Ω` is
precisely the kind of term that paper does *not* give an infinitary
denotation to. Replace `Ω` with a pure-`S` divergent term or drop the
sentence. (The draft also credits the SN^∞ observation to Waldmann's thesis
§7.6, contributing "the detailed write-up"; worth reflecting.)

### A8. §2: "Both notebooks ... independently reproduce the 618/43/504,930 figures" (lines 135–138)

Re-executed both notebooks with `nbconvert --execute` into the scratchpad.
Both run with zero errors. `ski-in-ski.ipynb` prints all three figures in
executed output. `ski-in-ski-aviary.ipynb` builds the interpreter natively
and runs small examples but prints **none** of them: no atom measurement, no
tower run. As committed, both notebooks have no stored outputs at all
(`execution_count: null` everywhere), so a reader cannot check the claim
from the repository either way. Fix: attribute the reproduction to
`ski-in-ski.ipynb` only, and either commit executed outputs or say they are
not preserved.

### A9. §7.1, §7.2: "§5's C1 finding" points at nothing (lines 350, 403)

"C1" is a label from `GATE1-RELATED-WORK.md`'s triage table. §5 of the
paper does not use it and does not state the outcome-type-growth claim;
§6 does. `SCRY-BLOCKING-DESIGN.md` line 17 has the same stale reference.

### A10. §6 table header and §8: "absorbing" is used for both arms (lines 256, 455)

Line 253 says "4 atoms to expose, 7 to hide". The table header then labels
the `errArmAbs` column (the one showing `ERR`, the exposing arm)
"absorbing", and §8 calls the `Ω` arm "the absorbing arm". Source comments
(`tower_harness.py:217–218`) say "observable" / "hidden". Pick one pair of
words and use it everywhere; the table header is the wrong one.

### A11. §1: "Neither is a claim about combinators" (Jay & Palsberg) (line 53–55)

Their abstract: "Our language is a factorisation calculus in the style of
Jay and Given-Wilson, a combinatory calculus with a factorisation operator."
It *is* a typed combinatory calculus, just not SK/SKI. Say "neither is in
the SK/SKI basis". Note also that §1's decoder-versus-evaluator distinction
is Jay & Palsberg's self-recogniser versus self-enactor, and with `C = I`
Tromp's `F I (M̃:N) = M N` is a self-enactor; cite them for the distinction.

### A12. §0/§1: "Kleene 1936, universal partial recursive functions"

Kleene 1936 ("General recursive functions of natural numbers") gives the
Normal Form Theorem, from which a universal function follows. "Partial
recursive" is Kleene 1938. The explicit universal machine is Turing 1936.
Checked against the SEP entry; the Springer primary source is paywalled.

---

## B. Gaps and imprecisions (conclusion right, argument or wording not)

### B1. §7.2: "provably safe by the same purity argument" (lines 404–411)

Purity gives uniqueness of the result for a *fixed* oracle. The re-run uses
a *different* oracle each round. Soundness needs a monotonicity hypothesis
the paper never states: the new oracle agrees with the old one on every
path the old one answered. `SCRY-BLOCKING-DESIGN.md` lines 69–71 state it
("`E' = E` except answers `p` too"); the paper drops it. It holds here only
because the driver's namespace is append-only. An oracle that revised an
answer would make the scheme unsound.

Two further precision points. "Reproduces every already-taken step" is false
for the blocking step itself (round 1 yields `pendingN` there, round 2
yields `steppedN`); say "every step strictly before the block". And re-run
is not fuel-neutral: each round replays the previous one plus at least one
step, so with a fixed budget a block silently becomes a timeout
(`review/fuelrounds.py`):

```
chained Scry S, {S->Scry K, K->I}
   fuel=1: [(1, 'BLOCK on S'), (2, 'TIME')]
   fuel=2: [(1, 'BLOCK on S'), (2, 'BLOCK on K'), (3, 'TIME')]
   fuel=3: [(1, 'BLOCK on S'), (2, 'BLOCK on K'), (3, 'VAL')]
```

Recomputation cost already matters, because fuel is charged for it. The §9
bullet saying (b)/(c) would matter "if recomputation cost ever mattered"
should be revised.

### B2. §7.2: the namespace and resume loop are Python, and "stuck" is a Python branch

`scry_namespace.py` says so plainly (the namespace is a Python dict; `STUCK`
is `leaf in namespace or leaf not in resolution_table`). §7.2 does not, and
the surrounding "pure `{S,K,I}`" framing invites the wrong reading. State
what is SKI (`wfN`, the oracle term built each round) and what is host
(the fact table, the loop, the stuck detection).

### B3. §7.1: at the outer result type, stuck and value share a tag

`done` maps to `rVal m` (`scry_harness.py` lines 142–145). The step-level
distinction the table row reports is real, but the 3-way outer outcome is
`{value-or-stuck, miss, timeout}`; "stuck" is not one of its points. This
matters for the outcome-type-growth narrative and should be stated.

### B4. §3: Thm 3.2 does not prove "exactly this"; a short reduction is missing (lines 156–166)

Thm 3.2 is about a one-layer factorisation operator on live combinators;
`quote` is a total map to Scott data. The conclusion follows, by a
two-line argument the paper should supply: if `Q M ↠ ⟨M⟩` were SKI-definable
then, translating to λ-calculus, `⟦Q⟧ (λx.x)` would be a single term, yet
`Q (S K X)` would yield `⟨S K X⟩` from which `X` is extractable, so every
`X` would share a reduct, contradicting that `S` and `K` are distinct
normal forms. (Equivalently: `Q` plus the artifact's own `UQ` builds a
factorisation combinator, contradicting Thm 3.2 directly.) Also line 157:
"every SKI context treats them identically" is false for the empty context
in weak CL, where `S K K` is a normal form distinct from `I`; the true
statement is that they agree on every argument. And Thm 3.2 is stated for
`{S,K}`; the proof goes through with `I` primitive, but say so.

### B5. §4: "seven atom-level sites ... none an artifact of the abstraction algorithm" (lines 195–199)

The repository's two census scripts disagree on the atom count: 7 with
primitive `I` (`bckw_census.py`), 10 with `I = W K` (`census.py`, which
also reports the encoding layer at `W = 4`, contradicting "None needs
contraction" at line 191 under that convention). `census.py`'s own header
calls the atom census "secondary, algorithm-relative". What is invariant
is the **occurrence** census: surplus occurrences `Σ(occ − 1)` over the five
non-affine components is `1 + 3 + 1 + 1 + 1 = 7`, and any BCKW abstraction
needs at least that many contractions. Reground "seven" on occurrences.
Also: "the rebuild generator's `f`/`h`" names two variables where only `h`
is duplicated (`{f:1, h:2}`). And "verified: 18/18 SKI and BCKW
abstractions agree" is a non sequitur for algorithm-independence of the
census: the differential check tests extensional equality of the two
abstractions, and the SKI side has `W = 0` by construction.

### B6. §0, §6: "four-atom-versus-seven" is measured, not minimal (lines 24–26, 253)

`errArmAbs = K (K (K I))` (4), `errArmOmg = K (S I I (S I I))` (7), and the
two emulators differ by exactly 3 atoms (768 vs 771). But the `K` wrapper on
`Ω` is unnecessary: `Ω acc` diverges as `Ω` does, and a 6-atom arm
reproduces the T3 table cell for cell (`review/omg6.py`). Even 4 depends on
`aviary_kernel.abstraction`'s η/`I` shortcuts. Either say "as measured in
this file" or use 4 versus 6 and "the smallest edit we found".

### B7. §6: "`Ω = (SII)(SII)`, itself the smallest divergent term" (lines 253–254)

Exhaustive enumeration of all `{S,K,I}` application trees up to 6 atoms
(`review/brute2.py`; counts match `3ⁿ·Catalan(n−1)` exactly, so the
enumeration is complete): every one of the 3,873 terms with ≤ 5 atoms
reaches a normal form; at 6 atoms exactly five terms do not, under both
"no NF" and "no WHNF": `SII(SII)`, `S(SI)(SI)I`, `SSS(SI)I`, `SSI(SI)I`,
`S(SS)SII`. All five were confirmed genuinely divergent (strictly growing
under 3,000 head steps, `review/div6.py`). So 6 is minimal, which is good
for the paper, but `Ω` is *one of five*, not *the* one. (Tromp notes the
`{S,K}`-only minimum is `S S K (S (S S K))` at 7 atoms.)

### B8. §5: quantifier slip (lines 212–214)

"`Ω` reports TIMEOUT at every fuel level `k`, but so does `I³¹K`" distributes
"every `k`" onto `I³¹K`, which only times out for `k ≤ 31`. The intended
claim is local: at any fixed `k`, one observation does not separate a
divergent term from one needing more than `k` steps. The "32" is exactly
right (31 contractions, fuel `k` permits `k` step-attempts of which the last
must be the no-redex check, `review/fuel.py`).

### B9. §6: "`Err` — no reduction rules" (line 239)

Reaching `Err` in head position fires `errArm` and terminates or diverges the
loop. Say "no object-level contraction rule".

### B10. §7: "consistent with the known 10²–10³×-per-layer overhead" (lines 325–330)

Measured: layer 1 is 340×, layer 2 is 504,930/340 ≈ 1,485×. Say "roughly
10³×". And "see §1" for this figure points at nothing; the phenomenon is
recorded in `GATE1-RELATED-WORK.md` A3, not in §1.

### B11. §2: T2 needs `--kk 500`; the script's default is 120

The inner run needs 341 object steps, so the default does not suffice.
Worth one sentence in §2 so a reader running the script gets the number.

### B12. §7.1: the two "caught mistakes" are process narrative

The second (the `K (Scry I)` test) is documented in `scry_harness.py`
comments; the first (the hand-derived abstraction) is not recorded anywhere
a reader can check. Neither belongs in the argument of a paper; move to the
repository or an appendix.

---

## C. Cosmetic

- §6 code block (lines 248–250) is presented as a verbatim quote but the
  comments differ from `tower_harness.py:217–218` ("exposed/absorbed" vs
  "observable/hidden").
- §7.1 should state explicitly that `{S,K,I,App,Scry}` is a separate
  5-symbol encoding parallel to `{S,K,I,App,Err}`, not stacked on it
  (`scry_harness.py` docstring lines 6–9 say so; the paper does not).
- "host diverges" in the §6 table is a 400,000-step host fuel cap
  (`Status.FUEL`), not detected non-termination. It is mathematically
  certain here because the arm *is* `Ω`, but the label reads as detection.
- Jay 2017: venue "MFPS XXXIII, 2017" is right; the archival version is
  ENTCS 336 (2018).

---

## D. What was verified and holds

All against `aviary-kernel` 0.1.0, re-run in this review:

| claim | result |
|---|---|
| `whnfF` 618 tree-atoms, `UQ` 43, basis `{S,K,I}` | exact |
| banner 348 / 62 | exact (but see A5 for what they measure) |
| T0 340, T1 91,556, T2 504,930 (`--kk 500`), all `VERDICT: OK` | exact |
| §6 T3 table, all ten cells | exact |
| `wf5Abs` / `wf5Omg` 768 / 771, differ at exactly one definition site | exact |
| `wfQ` 950, `wfN` 1,066; both scripts `ALL CHECKS PASSED`, exit 0; exit 1 on an injected failure | exact |
| §7.1 table, all seven rows, by fresh-marker probe | exact |
| `K (Scry I)` payload decodes to the unreduced term (Scry never reached) | confirmed |
| oracle receives the Scott-encoded path, unreduced | confirmed |
| §7.2 three-round trace, final value `I`; unresolvable → STUCK; `Ω` → TIME | exact |
| `I³¹K` minimal fuel 32; `K I Ω` → `just ⟨I⟩` under the emulator | exact |
| occurrence census 10/10 encoding affine, 3/8 core affine; differential 18/18; purity guard | exact |
| `ski-in-ski.ipynb` executes with zero errors and prints 618 / 43 / 504,930 | confirmed |
| Amin & Rompf: Prop 4.2, Prop 4.6 statement, "without formal proofs" (p. 11), §4.2.2 CPS, no "fuel" anywhere, no failure outcome | confirmed against the PDF |
| Jay & Given-Wilson: Thm 3.2 verbatim in §3; §8 "Structure Completeness"; no occurrence of "quotation" | confirmed against the PDF |
| Mogensen 1992 is untyped λ-calculus; Jay & Palsberg 2011 is typed, self-recogniser vs self-enactor | confirmed |
| Davis2026b: `CL(S)` is `S`-only; SN^∞; "`K` purchases universality at the cost of infinitary semantic coherence" verbatim | confirmed |
| `ssearch` description | confirmed against its README |
| Jay 2016 ENTCS 325; Jay 2017 MFPS XXXIII; Kavvos arXiv 1712.09302 | confirmed |

---

## E. Assessment of the argument

The artifact is stronger than the paper. The interpreter, the follow-on
discipline, and the self-verifying scripts are exemplary, and every number
survives. The most quotable technical result is §4's split (representation
is affine; iteration needs contraction; self-interpretation needs both),
which the paper underweights relative to the Nock material. The
homoiconicity disanalogy in §7 is the sharpest sentence about `+mock`.

"Authored failure" is real but, as a general insight, is something every
interpreter author knows. The contribution is minimality and legibility: a
single-arm diff with everything else fixed. Stated that way it is
defensible; stated as "what is new" it invites "this is standard". The
scry sections re-trigger the same phenomenon by construction and call it a
second independent instance; it is the same instance.

The `+mock` faithfulness property is checkable by construction and should
be a lemma: for every term not containing `Err`, the two emulators are the
same program apart from an unreachable arm, so they agree. The table is
evidence; the one-line argument is the proof.

§1 narrates its own revisions and is the weakest section. Cut it to a
clean statement of prior art (Tromp Thm 3/4 as decoder and self-enactor,
`nfreduce` as the closest symbolic evaluator, Mogensen, Jay & Palsberg for
the recogniser/enactor distinction) and a one-paragraph statement of the
residue: a concrete `{S,K,I}` step-evaluator, fueled, self-applied,
executed.

Recommended shape: an artifact paper. Lead with the interpreter and the
census, state faithfulness as a lemma, keep the disanalogy, present scry as
substitutability-as-argument, and correct §7.2's scope note to "not built"
rather than "not possible". `review/eq5ns.py` shows the compound-path
namespace is a 240-atom addition; promoting it to a follow-on file would
remove the scope caveat entirely.

## F. Decisions for the author before corrections are applied

1. Promote `EQ5` and the compound-path namespace oracle to a real follow-on
   file, or leave §7.2 at bare leaves with the corrected wording.
2. Report the site edit as measured (4 vs 7) with a "not minimal" note, or
   switch the artifact to the 6-atom arm and report 4 vs 6.
3. Restructure as an artifact paper (E above), or keep the current section
   order and apply only the corrections in A and B.
4. Commit executed notebook outputs, or state that outputs are not
   preserved.
