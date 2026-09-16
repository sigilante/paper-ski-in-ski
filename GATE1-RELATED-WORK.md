# GATE 1: Related-Work Triage

**Scope of this pass — read this first.** Three targeted searches;
abstracts, indexed excerpts, and secondary summaries. **No primary source
read in full.** This is triage sufficient to rule on the kill criterion
and to reprice claims, not the 2–3 week pass PAPER-SPEC-v2 §6 requires.
Confidence is stated per verdict. Two items need primary reading before
anything is drafted (§5).

**Headline:** the kill criterion does not fire, but two claims are
superseded by existing literature and the paper's centre of gravity
should move. Recommended reframing in §4.

---

## 1. Verdicts

| Claim | v2 tag | Verdict | Confidence |
|---|---|---|---|
| B1 / input boundary — quote not SK-definable | PROSE + LEAN-NEW | **SUPERSEDED.** Established result. Demote to citation. | High |
| C3 — unit/extension decomposition (kill criterion) | PROSE | **SURVIVES,** but adjacent work is closer than assumed. Requires careful positioning. | Medium |
| A3 — interpretive overhead 10²–10³×/layer | CERT | **KNOWN PHENOMENON.** Demote from claim to measurement. | High |
| B2 / B3 — encoding of failure is inert; semantics authored in the arm; 4 vs 7 atoms | CERT | **NO PRIOR FOUND.** Strongest surviving contribution. | Medium |
| B4 / B5 — the observability pair, executable | CERT | **NO PRIOR FOUND.** | Medium |
| C1 — adding an outcome forces the result type to grow; failing silently converts crash → timeout | CERT | **NO PRIOR FOUND.** Concrete and reproducible. | Medium |
| D1 / D2 — three-valued jet contract, composition by initiality | LEAN | **UNAFFECTED.** | High |
| D3 — production evidence (`%exit`/`%fail`, NockVM enum) | PROD | **UNAFFECTED.** | High |
| C2 — fuel is the only totalizer for a crash-free host | PROSE | Not searched this pass. | — |

## 2. Superseded: the input-boundary finding

Jay & Given-Wilson, *A combinatory account of internal structure*, JSL
76(3):807–826, 2011, states our observation as its opening premise:
there exist computable functions on combinators that S and K cannot
represent, <cite index="17-1">because they reach internal structure in ways S and K cannot</cite>. Their
factorisation combinator F supplies the missing capability; SF-calculus
is *structure complete* and <cite index="17-1">supports a function deciding structural equality of arbitrary normal forms</cite> — which is precisely the
operation a `quote` would need. Follow-ups are directly on our target:
Jay, *Programs as Data Structures in λSF-Calculus* (2016), and Jay,
*Self-Quotation in a Typed, Intensional Lambda-Calculus* (MFPS XXXIII,
2017).

A detail worth noting for §6: they engage the same Ω we use, observing
that <cite index="21-1">Ω = (SII)(SII) has no factorable form, so FΩFF is head normal</cite>.

**Action.** The "level 0 → 1 needs an external encoder; every level above
is closed under quoting" statement stays in the paper, but as a
*corollary of Jay & Given-Wilson*, one sentence, cited — not as a
finding. It still earns its place because it explains the artifact's
Python encoder and licenses the SKI-parser fix, and because it is the
sharp contrast with Nock's homoiconicity (D3 territory), which is ours.

## 3. The kill criterion: C3 survives, narrowly

Amin & Rompf, *Collapsing Towers of Interpreters*, PACMPL 2(POPL):52,
2018, is the closest work and is closer than PAPER-SPEC-v2 assumed. They
collapse a tower into a single-pass compiler via staging and stage
polymorphism, and — the part that matters to us — they do it <cite index="24-1">for arbitrarily many levels of self-interpretation, including levels with semantic modifications</cite>. Purple realizes a conceptually infinite
reflective tower in which, by their account, every aspect of the
semantics can change dynamically.

So "a level may modify semantics" is established, and "towers collapse"
is their result, not ours. What I did **not** find in the abstracts,
artifact README, or indexed body text:

- any characterization of *what* a level can contribute to the outcome
  structure (values vs. deterministic failure vs. divergence);
- the unit/extension decomposition, or an identification of faithful
  self-interpretation as the unit of that composition;
- any treatment of failure semantics as a *design choice made at a site*,
  as opposed to a semantics that is simply given.

Their objective is performance — removing interpretive overhead. Ours is
the algebra of failure outcomes and its consequence for correctness
contracts. Different questions about the same structure.

**But the risk is real and the language collides.** "Collapse" is their
word for what we call the unit law. Using ours without positioning
against theirs would read as either ignorance or appropriation.

**Action.** C3 survives as a contribution, conditional on §5's primary
read. §9 must position explicitly: *Amin & Rompf collapse towers whose
levels may modify semantics; we ask which modifications to the failure
structure are available, and show the choice is authored at named sites
with measurable cost.*

## 4. Recommended reframing (the substantive change)

The surviving contributions cluster on one side of the v2 outline:

**Strong:** the authored arm (B2/B3) — the encoding of a failure carries
no failure, and the semantics is a downstream choice, 4 atoms against 7.
The observability pair as an executable artifact (B4/B5). The
outcome-type growth defect (C1). The three-valued jet contract and its
composition theorem (D1/D2). Production evidence (D3).

**Weakened:** the tower itself (A1–A4) and interpretive overhead (A3).
Self-interpretation is old; collapse is Amin–Rompf's; overhead is the
premise of their paper.

So the paper should not present itself as a contribution to the
reflective-tower literature. That field is crowded, well-tenanted by
Smith, Wand–Friedman, Danvy–Malmkjær, Asai's Black, and Amin–Rompf, and
we would be entering it with a citation-shaped observation and a
performance measurement.

**Reframe: this is a paper about correctness contracts for accelerated
implementations, in which the SKI artifact is the minimal exhibit.**
The thesis narrows and strengthens: *an accelerated implementation's
correctness contract is determined by the failure structure its host
exposes; that structure is authored, not inherited; and the naive
two-valued contract is therefore unsound wherever a reflective layer has
authored an observable failure.* Nock/C is the industrial case with the
mechanized contract; SKI is the minimal case where the entire authored
decision is visible as four atoms against seven; the tower is
*demonstration apparatus*, not a result.

Structural consequences for PAPER-SPEC-v2:
- §2 (authored failure) and §4 (Nock/C) become co-equal centres; §4
  grows, §3 (the lattice) shrinks to ~2 pp and cites Amin–Rompf and Jay
  rather than building a framework from scratch.
- §5's A1–A4 numbers move to apparatus description; §5.2 (the defect
  log) is *promoted* — it is now proportionally more of the
  contribution, which makes decision D-a (conviction-story reuse) more
  urgent, not less.
- Venue: the narrowing favors ICFP or OOPSLA as an
  experience-plus-artifact paper over JFP. TOPLAS is off the table
  unless §3 regrows, which this pass argues against.

## 5. Remaining reading — must-do before drafting

1. ~~**Amin & Rompf POPL 2018, in full**~~ **DONE, see §7.** Kill
   criterion confirmed not to fire, confidence raised to High.
2. ~~**Jay & Given-Wilson 2011, §4 and §8**~~ **DONE, see §7.** One
   correction: §8 has no self-quotation content — see §7 for what to do
   about it.
3. Kavvos, *On the Semantics of Intensionality and Intensional
   Recursion* (arXiv 1712.09302) — a survey placing reflective towers and
   naming Jay's factorisation calculus as the current foundation for
   reflection. Cheap, high-yield for §9, and it corroborates our
   motivation: reflective facilities are <cite index="32-1">infamous for pernicious bugs</cite>.
4. Not yet searched: differential testing's crash-equals-crash oracle
   (Csmith lineage, consensus/EVM fuzzing) — needed for §1's motivation
   and for the `eq` blind-spot argument. Also Mogensen and Kiselyov for
   technique, and the combinator-size literature for A3's numbers.
5. **New, from §7.2.** Jay, *Programs as Data Structures in
   λSF-Calculus* (2016), and Jay, *Self-Quotation in a Typed,
   Intensional Lambda-Calculus* (MFPS XXXIII, 2017) — needed
   specifically to source any "self-quotation is possible above level
   0" claim; the 2011 JSL paper does not make that claim (§7.2).

## 6. Decision requested

**D-e (new).** Adopt the §4 reframing? It narrows the paper, moves
Nock/C to a co-equal centre, shrinks the framework section, and changes
the venue target. My recommendation is yes: the reframed claims are ones
this pass could not find priors for, whereas the tower-centric framing
walks into Amin–Rompf's territory carrying a measurement they would
regard as their premise.

D-a (conviction-story reuse) is now gating a larger fraction of the
paper and should be settled in the same pass.

---

## 7. Primary-source verification (full reads, not triage)

Both §5 must-do items read in full — Amin & Rompf all 33 pp, Jay &
Given-Wilson all 21 pp — not abstracts or excerpts.

### 7.1 Amin & Rompf, *Collapsing Towers of Interpreters* (POPL 2018)

**Kill criterion: confirmed not to fire. Confidence raised Medium →
High.** The full text — including §11 Related Work and §12
Conclusions — contains no treatment, anywhere, of: failure/error as a
distinct execution outcome; an outcome-type or result-type that must
grow when the object language gains a construct; or failure semantics
authored at a site. This is a stronger negative than the triage pass
could establish from abstracts alone.

What "semantic modifications" actually means in the paper (§5–§7,
Purple/Black): tracing, meta-level variable-access counting,
instrumentation hooks, undo/rollback, `call/cc` and `shift`/`reset`
via `EM`, CPS transformation. Every example changes *how* a
value-producing computation is observed or transformed — none changes
*whether* it produces a value, fails, or diverges. Divergence itself is
never modeled as an outcome; the correctness propositions are silent
about non-termination, and there is no fuel/timeout concept anywhere in
the paper.

The closest thing to a "unit law" is explicit and citable by number:

- **Prop 4.2 (Correctness of Interpretation).** `eval ≡ (eval eval-src)`
  — self-interpretation is observationally the identity.
- **Prop 4.6 (Multi-Level Jones Optimality).** Generalizes 4.2 to
  arbitrary depth `n`: for any Pink program `p` and natural `n`,
  `⟦((evalⁿ evalc-src) p-src)⟧ ⇓ ⟦p⟧`, with `eval¹ = eval` and
  `evalⁿ⁺¹ = (evalⁿ eval-src)` (verbatim from p. 12; note the top-level
  argument is `evalc-src`, the compiler instance, and the relation is `⇓`).

Cite these two by number in §9's positioning sentence rather than
paraphrasing "collapse." Note for precision: the paper states these
"without formal proof but backed by experimental evidence" (p.11) — they
are propositions/claims tested by example, not proven theorems. Say so
if leaning on them.

**§9 positioning, now with real citations:** *Amin & Rompf prove
(Prop. 4.2, 4.6) that towers of value-producing self-interpretation
collapse to the identity; this holds under semantic modifications to
control flow (tracing, CPS, reflection — §5–7 of their paper) but their
framework has no notion of a failure outcome to modify. We ask which
modifications to the failure structure specifically are available, and
show the choice is authored at named sites with measurable cost —
outside the outcome space their equivalences are stated over.*

### 7.2 Jay & Given-Wilson, *A combinatory account of internal
structure* (JSL 76(3), 2011)

Confirms the load-bearing citations, with exact locations:

- **Theorem 3.2** (p.7): *Factorisation of SK-combinators is a symbolic
  computation that is not representable* — this is the precise theorem
  for "quote is not SK-definable." Cite it as Theorem 3.2, not generally.
- **§4** (p.8–9): defines `F` and SF-calculus; **Theorem 4.3** is the
  structural-equality result ("`equal` decides structural equality of
  normal forms").
- **Ω = (SII)(SII) has no factorable form, so `FΩFF` is head normal**:
  this is **§5** ("Head Normal Forms," p.10), *not* §4 as loosely cited
  before. Small correction — fix the section number if this passage is
  quoted in the paper.

**Correction to the §5 action item.** §8 is titled "Structure
Completeness" and is entirely about the Theorem 8.2 characterization
(structure-complete ⟺ supports S, K, F, eqatom) plus pattern-matching
and generic-query applications (`equal`, `apply2all`, `update`). **It
contains no discussion of self-quotation** — a term quoting itself, or
a calculus containing its own interpreter/quoter internally does not
appear anywhere in this paper (checked the full 21 pp, references
included). The paper's actual claim is narrower and different: SF
*decides structural equality of arbitrary normal forms* (Thm 4.3),
which is what a `quote` needs downstream, not a claim that SF can
*self-quote*.

**Action.** Don't cite this 2011 paper for a self-quotation capability —
it doesn't make that claim. If the paper needs "self-quotation is
possible one level up," that claim (if it exists) belongs to the two
follow-ups already flagged in §2 — Jay, *Programs as Data Structures in
λSF-Calculus* (2016) and Jay, *Self-Quotation in a Typed, Intensional
Lambda-Calculus* (MFPS XXXIII, 2017) — neither read yet. Add reading
those two, specifically for the self-quotation claim, to §5's list if
the paper's "closed under quoting above level 0" line is going to lean
on it by name.

### 7.3 Net effect on open decisions

- **D-e (reframing):** recommend adopting it now with High confidence,
  not Medium — the full Amin & Rompf read closes the last channel by
  which the kill criterion could have fired.
- **§5 remaining-reading list:** items 1–2 done; add "Jay 2016 / Jay
  2017, for the self-quotation claim specifically" as a new item,
  separate from the superseded-citation use of the 2011 paper.
