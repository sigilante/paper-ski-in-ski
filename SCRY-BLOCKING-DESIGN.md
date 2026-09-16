# Design note: blocking scry (not implemented)

`scry_harness.py` implements the *synchronous* version of a nonlocal scry
site: the oracle `E` is a total-enough Scott-encoded function `path -> Maybe
value` that always answers immediately, `just v` or `nothing`, within the
same reduction. This note traces precisely where that assumption is baked
in, and what would have to change to support a scry that can *block* — the
oracle doesn't know yet, and the computation must suspend until it does —
which is closer to what real nonlocal scry (`.^`, opcode 12) actually does.
Nothing here is built; this is a map of the diff, not the diff.

## Where the outcome type would grow, precisely

`scry_harness.py` already extended the outcome type once, from `whnfF`'s
2-way `Maybe` (`nothing`/`just`) to a 3-way `stepped`/`done`/`errd` (reused
unmodified from `tower_harness.py`'s T3). That extension is exactly why
`PAPER.md` §5 ("Authored failure": adding an outcome forces the result
type to grow) is directly demonstrated by this repo's own history, not just
asserted about Nock.

Blocking scry forces a **second** growth, from 3-way to 4-way: `stepped(t)
| done() | errd() | pending(p, k)`. Tracing exactly which functions that
touches, in call order:

1. **`stepScQ1`** (the site itself). Currently: `e p errd (scHit rest)` —
   the oracle's Maybe is consumed directly, `nothing` becomes the terminal
   `errd`. Blocking needs the oracle to return a *three*-way answer instead
   of a Maybe — `just v | nothing | notyet` — so `stepScQ1` can distinguish
   "definitely absent" (still `errd`, if that outcome is wanted at all) from
   "don't know yet" (`pending`). This means the oracle's own type grows
   too, not just the interpreter's.

2. **`stepQE`** and **`stepScQ`**. These currently only ever return one of
   the 3 outcomes already defined; they'd need to pass a `pending` straight
   through unchanged when `stepScQ1` produces one — mechanical, no new
   design decision here, just widened arity on every continuation these
   functions apply.

3. **`stepped`, `done`, `errd`** themselves. Each is currently a 3-arg Scott
   selector (`stepped t c1 c2 c3 = c1 t`, etc.) — reused unmodified from
   T3. A 4th outcome means these are no longer reusable as-is: every
   existing use site (`stepScQ1`, `wfQ1`, `wfQGen`, `decodeTag`, and this
   repo's own T3 code in `tower_harness.py`) supplies exactly 3
   continuations, and all of them would need a 4th. This is the concrete
   shape of "extending the object language forces the interpreter's result
   type to grow" — it is not contained to the new code, it reaches back
   into already-shipped, already-tested combinators.

4. **`wfQ1` / `wfQGen`** (the fuel loop). Currently threads exactly the
   oracle `E`, the fuel `n`, and the term `m`. A `pending(p, k)` reaching
   this level means: the fuel loop itself has to stop, but *what does it
   hand back*? This is where the design genuinely forks — see below.

5. **The driver (`run`/`verify`/`main`)**. Would need a fourth branch
   alongside VAL/ERR/TIME — call it BLOCKED — and, critically, a way to
   *resume*: re-supply an answer for the path that blocked and continue.
   This is the part that has no analogue in the synchronous version at all.

## The actual hard part: what does `k` (the continuation) have to be?

Growing the outcome type is mechanical. The real question `pending(p, k)`
raises is what `k` — "the rest of the computation, resumable once `p`
resolves" — actually has to capture. Three honest options, in increasing
order of implementation cost:

**(a) Re-run from scratch.** When a scry blocks, don't try to resume
mid-reduction at all: record that path `p` needs an answer, and once the
caller supplies one, extend the oracle (`E' = E` except answers `p` too) and
re-invoke `wfQ E' n <t>` **from the original term**, not from wherever it
stopped. This works *because* SKI reduction is pure and deterministic **and**
`E'` agrees with `E` on every path `E` answered — the steps strictly before
the block are then identical in the re-run, so nothing is lost, only
recomputed. (The agreement hypothesis is load-bearing: an oracle that
revised an earlier answer would make the re-run's prefix differ. It holds
when the namespace is append-only. Re-running also charges fuel again for
the replayed prefix, so a fixed fuel budget that suffices to block may not
suffice to finish — see `scry_paths.py`'s fuel check.) This is the cheapest option by far: it
needs no CPS, no continuation-capture, and barely touches the interpreter —
`pending` just needs to carry the missed path `p` back to the caller, and
the caller loops. The cost is pure recomputation, paid every time a new
path is discovered partway through a run. This is close to what I
understand real Nock/Arvo scry-blocking does in practice — an event that
blocks on a scry is retried, not resumed via a captured continuation — so
it's also the most faithful option to the actual precedent, not just the
cheapest.

**(b) Resume from the top level only.** Restrict where `Scry` is allowed to
appear such that a block can only happen at the point `wf1` calls `step` —
i.e., forbid a blocking scry from being nested inside an argument that
hasn't yet been forced (this is already true of every scry in the
synchronous version, since `sp` only ever reaches leaves that are actually
being reduced — but it becomes a load-bearing restriction once blocking is
possible, rather than an incidental consequence of call-by-name). Under
this restriction, "the continuation" is just `(E, n, m)` — the same triple
`wfQ` already takes — so resuming means: extend `E` with the new fact and
call `wfQ E' n m` again, but `m` is now *the specific unreduced term*
`stepQE` was looking at when it blocked, not the original input term. This
avoids (a)'s full recomputation from the original input, at the cost of
`stepScQ1` needing to hand back the exact `m` in progress (already
available — it's `rbQ`'s job to rebuild it, so `pending` could carry
`rbQ p rest` as `m`) rather than just the raw path.

**(c) Full CPS.** Make `sp`/`rb`/`step` genuinely continuation-passing all
the way through — not just at the top level, the way `stepped`'s single
continuation currently only selects a branch — so that *any* point in the
spine-walk or rebuild, not just the top of `step`, can suspend and later
resume exactly where it left off, including partially-unwound spines and
partially-rebuilt terms. This is the only option that supports scry nested
arbitrarily deep in an unforced position becoming observable without
re-deriving it, and it is architecturally the same move Amin & Rompf's
`λ↑↓` CPS-Pink evaluator makes (§4.2.2, read in full for `PAPER.md`) — which
is worth noting as precedent for the technique, not for the failure-outcome
content, consistent with §5 there. It is also the only option that requires
rewriting `spGenQ`, `rbQGen`, and every step arm, not just the outcome type
and the fuel loop — a materially larger change than (a) or (b).

## Recommendation, if this gets built

Start with (a). It requires the smallest, most auditable diff on top of
`scry_harness.py` — extend `pending`'s payload to just the missed path,
have the driver loop on a growing oracle — and it is provably correct by
the same purity argument the whole artifact already leans on (deterministic
reduction ⇒ re-running is safe). (b) is a reasonable second step once (a)
is working, if recomputation cost matters. (c) should only be attempted if
the goal shifts from "demonstrate a blocking scry site" to "build a
faithful suspend/resume virtual machine" — at which point it stops being a
follow-on to this artifact and becomes a different project.
