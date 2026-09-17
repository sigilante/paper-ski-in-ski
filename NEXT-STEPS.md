# Next steps: apparatus that self-virtualization makes cheap

*2026-09-15. What exists: a fueled symbolic step-evaluator for `{S,K,I}`
in `{S,K,I}` (`whnfF`, 618 atoms), run on itself (T2); an oracle-threaded
variant with a `Scry` leaf (`wfQ`, 950); a blocking variant whose
outcome type carries a pending path and whose driver re-runs from scratch
under a growing namespace (`wfN`, 1,066); structural equality on encoded
paths (`EQ5`, 240) and a compound-path namespace on top of it. Every one of
the items below is an interpreter variant, an oracle, or a driver over
those pieces. Costs are in sessions of the kind that built `scry_paths.py`.*

The common shape: the interpreter is an ordinary term with one
substitutable site and a fuel loop whose result type we control. Each item
below changes one of three things: what the site does, what the loop
threads, or what the driver does with the outcome.

## Near (one session each)

1. **Tracer and profiler.** Thread a list through `wfQ1`'s continuation
   and cons each `stepped t'` onto it; the result type grows from `value`
   to `value × trace`, the same outcome-type growth as §5 of the paper, a
   fourth time. Three counters in place of the list, one per arm, give a
   profiler (how many `S`, `K`, `I`, `Scry` firings). This is Amin & Rompf's
   instrumentation example (§4.2.1) with no staging machinery.
   *Change:* `wfQ1`, `wfQGen`, the outer result payload. *Check:* trace
   length equals the host's contraction count for T0 (340).

2. **Gas metering.** Fuel already charges one unit per step-attempt. Charge
   per arm instead (`S` more than `K`, a `Scry` more than either) by having
   each arm return how much to deduct; "out of gas" is the existing
   timeout outcome. *Change:* the step arms' return payload and `wfQGen`'s
   numeral peel. *Check:* the same term under two tariffs times out at
   different budgets, and never changes its value.

3. **Reduction certificates.** A checker `cert n ⟨t⟩ ⟨t'⟩` that runs
   `whnfF n ⟨t⟩` and compares the result to `⟨t'⟩` with `EQ5` (over the
   4-tag encoding, `review/eqtest.py`'s `EQ`). The host reducer's claims
   become verifiable inside the calculus; T2's 504,930 could be certified
   rather than reported. *Change:* none to the interpreter; one new
   combinator. *Cost:* T2-scale runs for T2-scale certificates.

4. **Sandboxing.** A fifth arm that refuses: an interpreter that treats one
   leaf, or one scry path, as forbidden and reports it (`errd`). Amin &
   Rompf's "sandboxing for security" use case, as a one-arm edit like
   `errArmOmg`. *Change:* one arm. *Check:* the forbidden term is refused,
   the same term with the leaf in a discarded position is not (laziness).

## Middle distance (sits on the scry work)

5. **Event-sourced state.** `scry_namespace.py`'s namespace is an event log
   and re-run-from-scratch is replay. Make the driver explicit about it:
   append is commit, truncate is rollback, undo is free by purity.
   Arvo's model in miniature. *Change:* driver only. *Check:* truncating
   the log after round 2 of the chained example reproduces round 2's
   block exactly.

6. **A scheduler and message passing.** Interleave two encoded terms with
   fuel slices, and let one term's blocked scry be answered by the other's
   value. A blocking scry becomes "wait for a message"; two actors and a
   round-robin scheduler, all in `{S,K,I}` except the driver. The most
   Nock-shaped item here. *Change:* driver plus a per-term fuel slice;
   no interpreter change. *Check:* a producer/consumer pair terminates
   with the consumer's value equal to the producer's.

7. **Strictness experiments.** A call-by-value `whnfF` (normalize each
   argument before dispatch) stacked with the normal-order one. `K I Ω`
   survives normal order and dies under applicative order, so the same
   tower gives different answers depending on which level is strict.
   Authored semantics beyond authored failure. *Change:* the step arms
   (arguments normalized before the rule fires), which needs the
   normal-form loop from item 8. *Check:* `K I Ω` value/timeout table by
   level.

## Farther, and the most interesting

8. **Partial evaluation and the first Futamura projection.** Treat an
   unanswered `Scry p` as an inert unknown rather than a block, normalize
   around it, and return the residual. Specialize `wfQ E k ⟨p⟩` to a fixed
   `⟨p⟩` with `E` unknown, and the residual is `p` compiled by
   self-application: all interpretive dispatch on `⟨p⟩` executed, only the
   oracle call left. Designed in full in `PARTIAL-EVALUATION-DESIGN.md`,
   with Stage 1 and the host-level Futamura measurement already
   prototyped (`proto/`); the recommended next build.

9. **Self-quotation above level 0.** The paper says quoting is external at
   level 0 and closed above it, but nothing builds `⟨t⟩ ↦ ⟨⟨t⟩⟩`. It is a
   data transformation, so it is definable (a fold over the encoding that
   emits encoded constructors). With it the tower can be deepened from
   inside, which is what a reflective tower needs and what Jay's 2016 and
   2017 papers are about. *Cost:* small to build, T2-scale to exercise.

10. **Introspection.** Let the oracle see interpreter state (fuel remaining,
    the current step) so a term can ask about its own execution. Reflection
    in the Black/Purple sense (Amin & Rompf §6 to §7). *Change:* thread the
    state into the oracle call in `stepScQ1`; the oracle's type grows.

11. **A subject-oriented surface language.** Hoon's layering over Nock,
    reproduced over SKI: Scott pairs as cells with Nock axes, cores tied
    with `Y`, wings resolved at compile time, and a quotation line fixed
    by the paper's Proposition 3.1 rather than chosen. Internalizes the
    resolver's namespace (item 8's driver) as a core, and supplies the
    bracket-abstraction combinator item 8's Stage 4 needs. Designed in
    `~/SKIjack/SURFACE-LANGUAGE-DESIGN.md`, with the runtime in
    `~/SKIjack/RUNTIME-DESIGN.md`; a separate repository and paper.

## Not recommended

- **Full CPS resume** (`SCRY-BLOCKING-DESIGN.md` option (c)): a different
  project, as that note says.
- **Second Futamura projection** (specializing the specializer): three
  interpreter levels at roughly 1,485× cost per level (§6 of the paper);
  not reachable with this host reducer.

## Order

8, then 3 (its checker is what verifies 8's residuals), then 6. Items 1, 2,
4 are cheap demonstrations that can be added when the paper needs them.
