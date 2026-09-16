# Figure brief: two visual notations for SKI combinator terms

This brief describes four static figures for a paper on visualizing SKI combinator calculus. Figures A1 and A2 show the socket-glyph notation. Figures B1 and B2 show the typed-leaf spiral notation. A1 illustrates the reduction rules; A2, B1 and B2 all use the same running example so the two notations can be compared directly.

## Background the illustrator needs

A combinator term is built from the atoms S, K and I (and, in examples, lowercase variables such as x) by application. Application associates to the left, so `S K K x` means `((S K) K) x`. Each combinator needs a fixed number of arguments before it can act. This number is its arity: I needs one, K needs two, S needs three. When a combinator at the head of a term has at least that many arguments, it can fire:

- `I a` becomes `a`.
- `K a b` becomes `a`, and `b` is discarded.
- `S a b c` becomes `a c (b c)`, and `c` is copied.

The running example is `S K K x`, which reduces in two steps: first to `K x (K x)`, and then to `x`.

## Shared conventions

Both notations use one small palette, and every distinction also survives greyscale printing because it is carried by shape as well as colour.

| Role | Colour | Hex |
|---|---|---|
| Combinators (glyphs in A, leaves in B) | Red | #C62828 (glyph fill in A may use a light tint such as #FAECE7 with a #993C1D outline) |
| Variables | Mid grey | #7A7F87 |
| Function edges (B only) | Green | #3F8F2F |
| Argument edges (B only) | Blue | #2F6FC9 |
| Structural lines, sockets, labels | Dark grey | #444441 |
| Highlight for the part about to fire (A only) | Red-orange, dashed | #D85A30 |

Line weights are thin throughout: about 0.5 pt for shape outlines, 1 pt for connecting lines, and 1.5 pt for spines. Letters inside glyphs are set in the paper's text face at medium weight. All other labels are set at a smaller size in regular weight.

## Figure A: socket glyphs

### Idea

Each combinator is drawn as a rectangular glyph carrying its letter. Along its bottom edge the glyph has one small socket per argument it needs. An argument hangs below its socket on a short vertical line. The glyph's sockets show what the combinator will do:

- An ordinary socket is a small circle.
- K's second socket is a small square instead. This marks it as the drop socket: whatever plugs in there will be discarded.
- S's third socket is a circle with a thin concentric ring around it. This marks it as the copy socket: whatever plugs in there will be duplicated.

A socket is filled solid when an argument is plugged into it and drawn hollow when it is empty.

A glyph whose sockets are all filled is ready to fire. It is surrounded by a dashed red-orange rounded rectangle.

When the head of a term is a variable rather than a combinator, it has no sockets. Its arguments instead hang from short downward teeth along a horizontal spine that runs to the right of the head.

### Proportions

Let u be the diameter of a variable node (a grey circle carrying its letter).

**Top-level glyphs:**
- Height about 1.3u.
- Width about 1.6u per socket plus a margin, so the S glyph is roughly three times as wide as the I glyph.
- Sockets are spaced about 1.6u apart and centred on the bottom edge.

**Socket marks:**
- Socket circles have radius about 0.12u.
- The K drop square has side about 0.25u.
- The ring around S's copy socket has radius about 0.25u.
- Argument lines are about 0.8u long.

**Glyphs in argument position** (hanging under another glyph) are smaller:
- Height about 1.07u, width about 1.3u.
- Sockets about 0.57u apart.

**Other marks:**
- Any variable that is a copy made by S gets a thin outer ring at 1.3 times its radius, echoing the copy socket.
- The ready-to-fire outline sits about 0.3u outside the glyph, with a dash pattern of roughly 4 on, 3 off.

### Figure A1: the three rules

Three rows, each reading left to right: a left-hand side, a rightward arrow, and a right-hand side. The arrows sit at the same horizontal position in all three rows. The left-hand sides are left-aligned, and the right-hand sides begin in a common column.

**Row 1, the I rule.**
- Left side: an I glyph with one filled socket, and a variable `a` hanging below it.
- Right side: the variable `a` alone.

**Row 2, the K rule.**
- Left side: a K glyph with two sockets, a filled circle then a filled square. Variable `a` hangs from the circle.
- Variable `b` hangs from the square on a dashed line. `b` itself is drawn at about 50% opacity with a dashed outline, showing it will be discarded.
- Right side: `a` alone.

**Row 3, the S rule.**
- Left side: an S glyph with three filled sockets, the third ringed. Variables `a`, `b` and `c` hang below, and `c` carries an outer ring.
- Right side: `a c (b c)`, drawn with the spine convention.
  - `a` is the head. A horizontal spine runs to its right with two teeth.
  - From the first tooth hangs a ringed `c`.
  - From the second tooth hangs `b`. `b` has its own short spine with one tooth, from which hangs another ringed `c`.

Draft caption: *Socket-glyph notation for the SKI rules. Each glyph has one socket per argument. K's square socket drops its argument, and S's ringed socket copies its argument; copies carry the same ring.*

### Figure A2: reduction of S K K x

Three panels in a row, labelled t = 0, t = 1 and t = 2 above them, joined by rightward arrows.

**Panel t = 0.**
- A top-level S glyph with all three sockets filled; the third is ringed. It is surrounded by the dashed ready-to-fire outline.
- Hanging from the first socket is a small K glyph with both sockets hollow (a circle then a square), because it has no arguments yet.
- Hanging from the second socket is an identical small K glyph.
- Hanging from the third socket is the variable `x`, with its copy ring.

**Panel t = 1.**
- A top-level K glyph with both sockets filled (circle then square), surrounded by the dashed ready-to-fire outline.
- Hanging from the circle is a ringed `x`.
- Hanging from the square, on a dashed line, is a small K glyph. Its circle socket is filled, with a ringed `x` below it; its square socket is hollow because it has only one argument.
- This whole hanging K-and-`x` group is drawn at about 45% opacity, because the outer K is about to discard it.

**Panel t = 2.** The variable `x` alone, without a ring.

**Key.** Below the panels, in two short rows:
- a filled circle labelled "plugged socket";
- a hollow circle labelled "empty socket";
- a hollow square labelled "drop socket (K)";
- a ringed filled circle labelled "copy socket (S)";
- a small dashed rounded rectangle labelled "saturated: fires next".

Draft caption: *Reduction of S K K x in socket-glyph notation. A dashed outline marks the combinator about to fire. At t = 1 the inner K is not saturated (one hollow socket), and its whole subterm is faded because the outer K will discard it.*

## Figure B: typed-leaf spiral

### Idea

This follows the drawing style of Barendregt, Endrullis, Klop and Waldmann ("Dance of the Starlings"), which they credit to Hans Zantema. A term is drawn as a binary tree with no visible application nodes: every point where two edges leave a common corner is an application.

- Of the two edges leaving a corner, the green one leads to the function part and the blue one to the argument part.
- Leaves are shaped by type:
  - S is a filled red circle.
  - K is a filled red square.
  - I is a hollow red ring.
  - A variable is a filled grey upward-pointing triangle.
- The root is marked with a small hollow dark-grey circle.

The original paper uses only S, drawn as red dots. The typed leaves are what extend the style to full SKI.

### Construction rule

The drawing is produced by a simple turtle rule, so the illustrator can either trace output from the accompanying tool (`typed-leaf-spiral.html`, which exports SVG) or construct it by hand.

**Start.** Begin at the root with the pen heading straight up and a current length L = 10 units.

**At each application corner,** with current heading θ and current length L:
- Draw the function edge in green, at heading θ + 25° (turning left, counterclockwise), with length L.
- Draw the argument edge in blue, at heading θ − 65° (turning right, clockwise), with length 0.55 L.
- Continue into the function subterm from the end of the green edge, with heading θ + 25° and length 0.9 L.
- Continue into the argument subterm from the end of the blue edge, with heading θ − 65° and length 0.55 L.

Because every function step turns left and shrinks only slightly, the chain of function edges from the root curls into a spiral.

**Leaves.** At the end of an edge that reaches a leaf, draw the leaf shape. Its radius is 0.3 times the length L that the leaf would have inherited, clamped between 0.12 and 2.2 units. For K, the square's side is 1.6 times that radius; for I, the ring's radius is 0.85 times that radius.

**Weights.** Function edges are drawn slightly heavier than argument edges, at about 1.4 : 1.

**Pruning.** Subtrees whose edge length would fall below 0.02 units are omitted.

The angles and ratios are this project's choices, not values from the original paper. Tighter function turns give a more nautilus-like curl; smaller argument ratios give a finer, fern-like texture.

### Figure B1: reduction of S K K x

Three small square panels in a row, each with a hairline frame, labelled beneath with t = 0 · S K K x, t = 1 · K x (K x) and t = 2 · x.

**Panel t = 0.**
- From the root, the green spine makes three short left-turning segments. It ends at a red circle, which is S.
- The first corner has a blue edge to a grey triangle (`x`).
- The second corner has a blue edge to a red square (K).
- The third corner has a blue edge to another red square (K).

**Panel t = 1.**
- Two green spine segments end at a red square (the outer K).
- The first corner's blue edge leads to a small application corner. From there, a green edge goes to a red square and a blue edge to a grey triangle.
- The second corner's blue edge goes to a grey triangle.

**Panel t = 2.** Only the root marker and a single grey triangle at the root.

Each panel is scaled to fill its frame, so leaf sizes are not comparable across panels.

Draft caption: *The same reduction in typed-leaf spiral notation. Green edges lead to function parts and blue edges to arguments; red circles are S, red squares K, grey triangles variables.*

### Figure B2: a larger term

A single large square panel showing the term S(SS)SSS(SS(KK)) after 24 leftmost-outermost reduction steps (415 leaves). This panel should be exported from the tool, since it is not practical to draw by hand.

What the reader should see:
- a long green spine curling left from the root;
- blue side branches of decreasing size, each with its own smaller curl;
- red circles as the dominant leaf;
- red squares that stand out clearly, especially near the base of the spine.

Draft caption: *S(SS)SSS(SS(KK)) after 24 reduction steps. The spiral view shows the global shape of a large term, which the socket-glyph view cannot.*

## Suggested pairing in the paper

Place A2 and B1 in the same figure, one above the other with t = 0, 1, 2 aligned in columns, so readers can compare the notations step by step. A1 introduces the socket notation before that figure. B2 follows it to show where the spiral earns its place.
