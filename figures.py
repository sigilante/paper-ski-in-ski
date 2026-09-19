#!/usr/bin/env python3
"""Render the artifact's actual terms as figures, in the typed-leaf spiral
notation of figure-brief-A-B.md (Figure B), straight from the expanded
{S,K,I} terms. Nothing here is drawn by hand: every leaf in every figure is
an atom of the term named in its caption.

Construction rule (verbatim from the brief): start at the root heading up
with length L = 10. At each application, draw the function edge (green) at
heading +25 deg with length L, the argument edge (blue) at heading -65 deg
with length 0.55 L; continue into the function subterm with length 0.9 L
and into the argument subterm with length 0.55 L. Leaves: S filled circle,
K filled square (side 1.6 r), I hollow ring (radius 0.85 r), with
r = clamp(0.3 L, 0.12, 2.2). Function edges 1.4x heavier than argument
edges. Subtrees whose edge length would fall below 0.02 are omitted.

Outputs (figures/):
  fig-term-uq.svg          UQ, the unquoter (43 atoms)
  fig-term-whnff.svg       whnfF, the emulator (618 atoms)
  fig-term-eq5.svg         EQ5, path equality (240 atoms)
  fig-term-enc-ik.svg      the datum <I K> (40 atoms)
  fig-arms.svg             errArmAbs (4) beside errArmOmg (7)
  fig-engine-parts.svg     sp, rb, stepI, stepK, stepS, UQ side by side
  fig-engine-motion.svg    whnfF 3 <I K> at steps 0..340
  fig-full-*.svg           the same terms with EVERY atom drawn, radially
                           (angle = in-order leaf position, radius = depth),
                           same typed leaves and edge colours;
                           the spiral prunes deep argument subtrees, and
                           bracket-abstracted terms nest 41 levels deep
                           in argument position, so the spiral shows the
                           global shape and the tidy tree shows the term.

Usage:
    python3 figures.py        # writes figures/*.svg, then build/fig/*.pdf (via rsvg-convert)
                              # for every SVG in figures/, including the hand-drawn mechanism diagram
"""
from __future__ import annotations
import sys, math, os, threading, io, contextlib, glob, shutil, subprocess
from html import escape as esc

sys.setrecursionlimit(10_000_000)

from aviary_kernel.terms import Atom, App, size as tree_size

# ---- load scry_paths.py's environment (which loads the whole chain down to
# ---- tower_harness.py) without running any __main__ block.
_buf = io.StringIO()
with contextlib.redirect_stdout(_buf):
    exec(open("scry_paths.py").read().split('\nif __name__ == "__main__":\n')[0])

# ---- palette and geometry, from the brief
RED, GREEN, BLUE, INK = "#C62828", "#3F8F2F", "#2F6FC9", "#444441"
TF, TA = math.radians(25), math.radians(65)
RF, RA = 0.9, 0.55
L0 = 10.0
PRUNE = 0.02


def layout(term, prune=PRUNE):
    """Turtle walk. Returns (segments, leaves): segments are
    (x1,y1,x2,y2,is_arg); leaves are (x,y,kind,r). Iterative, so a long
    function spine does not recurse."""
    segs, leaves = [], []
    stack = [(term, 0.0, 0.0, math.pi / 2, L0)]
    while stack:
        t, x, y, ang, L = stack.pop()
        if isinstance(t, Atom):
            leaves.append((x, y, t.name, max(0.12, min(2.2, 0.3 * L))))
            continue
        if L < prune:
            continue
        fa = ang + TF
        fx, fy = x + L * math.cos(fa), y - L * math.sin(fa)
        aa = ang - TA
        al = L * RA
        ax, ay = x + al * math.cos(aa), y - al * math.sin(aa)
        segs.append((x, y, fx, fy, False))
        segs.append((x, y, ax, ay, True))
        stack.append((t.arg, ax, ay, aa, al))
        stack.append((t.fn, fx, fy, fa, L * RF))
    return segs, leaves


def _bounds(segs, leaves):
    xs = [0.0]; ys = [0.0]
    for s in segs:
        xs += [s[0], s[2]]; ys += [s[1], s[3]]
    for l in leaves:
        xs += [l[0] - l[3], l[0] + l[3]]; ys += [l[1] - l[3], l[1] + l[3]]
    return min(xs), min(ys), max(xs), max(ys)


def panel_svg(term, prune=PRUNE, stroke_scale=None):
    """SVG fragment for one term, in its own local coordinates. Returns
    (fragment, viewbox tuple, leaf count). Strokes are non-scaling so a
    panel drawn small keeps hairlines."""
    segs, leaves = layout(term, prune)
    x0, y0, x1, y1 = _bounds(segs, leaves)
    w, h = max(x1 - x0, 8), max(y1 - y0, 8)
    p = 0.08 * max(w, h) + 1.5
    E = max(w, h)
    w_fn, w_arg = E / 230, E / 320          # explicit widths: renderers that ignore
    ns = f'stroke-width="{E / 400:.3f}"'    # vector-effect (rsvg, some print paths) still agree
    out = []
    for (a, b, c, d, is_arg) in segs:
        col = BLUE if is_arg else GREEN
        wd = w_arg if is_arg else w_fn
        out.append(f'<line x1="{a:.1f}" y1="{b:.1f}" x2="{c:.1f}" y2="{d:.1f}" '
                   f'stroke="{col}" stroke-width="{wd:.3f}" stroke-linecap="round"/>')
    for (x, y, k, r) in leaves:
        if k == "S":
            out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{RED}"/>')
        elif k == "K":
            s = 1.6 * r
            out.append(f'<rect x="{x - s/2:.2f}" y="{y - s/2:.2f}" width="{s:.2f}" height="{s:.2f}" fill="{RED}"/>')
        elif k == "I":
            out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{0.85*r:.2f}" fill="none" '
                       f'stroke="{RED}" stroke-width="{max(0.3*r, E/400):.3f}"/>')
        else:  # a variable or marker, if any
            s = 1.6 * r
            out.append(f'<polygon points="{x:.2f},{y - s/2:.2f} {x - s/2:.2f},{y + s/2:.2f} {x + s/2:.2f},{y + s/2:.2f}" fill="#7A7F87"/>')
    rr = 0.018 * max(w, h) + 0.35
    out.append(f'<circle cx="0" cy="0" r="{rr:.2f}" fill="none" stroke="{INK}" {ns}/>')
    return "\n".join(out), (x0 - p, y0 - p, w + 2 * p, h + 2 * p), len(leaves)


def single(term, title, path):
    frag, (vx, vy, vw, vh), n = panel_svg(term)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vx:.2f} {vy:.2f} {vw:.2f} {vh:.2f}" '
           f'width="100%" role="img" aria-label="{esc(title)}">\n'
           f'<title>{esc(title)}</title>\n{frag}\n</svg>\n')
    open(path, "w").write(svg)
    return n


TEXT_WIDTH_PT = 454.0   # the paper's \linewidth (letter, 1.1in margins); figures are set at this width


def strip(panels, path, aria, cell=100.0, gap=8.0, render=None,
          label_pt=8.0, label_font="IBM Plex Mono, Menlo, monospace"):
    """Several panels in a row, each scaled to fill a square cell (leaf sizes
    are therefore not comparable across panels, as the brief notes).
    panels: list of (term, label, prune[, renderer])."""
    n = len(panels)
    W = n * cell + (n + 1) * gap
    # font-size is in viewBox units; convert the requested PRINT size (points,
    # when the figure is set at TEXT_WIDTH_PT) into units for this figure
    fs = label_pt * W / TEXT_WIDTH_PT
    label_h = 2.2 * fs
    H = cell + 2 * gap + label_h
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" width="100%" '
           f'role="img" aria-label="{esc(aria)}">', f'<title>{esc(aria)}</title>']
    counts = []
    for i, panel in enumerate(panels):
        term, label, prune = panel[:3]
        rend = panel[3] if len(panel) > 3 else (render or panel_svg)
        frag, (vx, vy, vw, vh), cnt = rend(term, prune)
        counts.append(cnt)
        cx = gap + i * (cell + gap)
        s = cell / max(vw, vh)
        ox = cx + (cell - vw * s) / 2 - vx * s
        oy = gap + (cell - vh * s) / 2 - vy * s
        out.append(f'<rect x="{cx:.1f}" y="{gap:.1f}" width="{cell:.1f}" height="{cell:.1f}" '
                   f'fill="#FFFFFF" stroke="{INK}" stroke-width="0.4"/>')
        out.append(f'<g transform="translate({ox:.3f},{oy:.3f}) scale({s:.4f})">{frag}</g>')
        out.append(f'<text x="{cx + cell/2:.1f}" y="{gap + cell + label_h - 0.5*fs:.1f}" text-anchor="middle" '
                   f'font-family="{label_font}" font-size="{fs:.2f}" fill="{INK}">{esc(label)}</text>')
    out.append("</svg>")
    open(path, "w").write("\n".join(out) + "\n")
    return counts


def leaf_counts(term):
    c = {"S": 0, "K": 0, "I": 0}
    st = [term]
    while st:
        t = st.pop()
        if isinstance(t, Atom): c[t.name] = c.get(t.name, 0) + 1
        else: st.append(t.fn); st.append(t.arg)
    return c


def _nodes(term):
    """Iterative traversal: [depth, leaf kind or None, parent, is_arg, pos].
    Leaves get consecutive in-order positions (function subtree first);
    internal nodes get the mean of their children's. A DAG with shared
    subterms is drawn as the tree it denotes."""
    nodes, children = [], {}
    work = [(term, 0, None, False)]
    while work:
        t, d, parent, is_arg = work.pop()
        idx = len(nodes)
        nodes.append([d, t.name if isinstance(t, Atom) else None, parent, is_arg, None])
        if parent is not None:
            children.setdefault(parent, []).append(idx)
        if not isinstance(t, Atom):
            work.append((t.arg, d + 1, idx, True))
            work.append((t.fn, d + 1, idx, False))    # popped first
    counter = 0
    for n in nodes:
        if n[1] is not None:
            n[4] = counter; counter += 1
    for k in range(len(nodes) - 1, -1, -1):            # children follow their parent
        if nodes[k][1] is None:
            ks = children[k]
            nodes[k][4] = sum(nodes[c][4] for c in ks) / len(ks)
    return nodes, counter


def radial_frag(term, prune=None, dr=2.2):
    """Every atom drawn. Angle from in-order leaf position (function
    subtree first, clockwise from the top), radius from depth, so a term
    reads as a disc: the root at the centre, its head along the first ray.
    Same typed leaves and edge colours as the spiral. Returns
    (fragment, viewbox, leaf count) like panel_svg, so strip() can hold it."""
    nodes, n_leaves = _nodes(term)
    maxd = max(n[0] for n in nodes)
    R = maxd * dr
    # leaf spacing on the outer ring is at least 1 unit: grow dr if needed
    if 2 * math.pi * R < n_leaves * 1.0 and maxd:
        dr = n_leaves / (2 * math.pi * maxd); R = maxd * dr
    def xy(n):
        th = -math.pi / 2 + 2 * math.pi * n[4] / n_leaves
        r = n[0] * dr
        return r * math.cos(th), r * math.sin(th)
    spacing = 2 * math.pi * R / max(n_leaves, 1)   # leaf-to-leaf distance on the outer ring
    rl = max(0.32, min(1.2, 0.4 * spacing))
    w_fn = max(0.08, min(0.5, 0.11 * spacing)); w_arg = 0.7 * w_fn
    ns = f'stroke-width="{w_fn:.3f}"'
    out = []
    for n in nodes:
        if n[2] is None: continue
        x1, y1 = xy(nodes[n[2]]); x2, y2 = xy(n)
        col, wd = (BLUE, w_arg) if n[3] else (GREEN, w_fn)
        out.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
                   f'stroke="{col}" stroke-width="{wd:.3f}" stroke-linecap="round"/>')
    for n in nodes:
        if n[1] is None: continue
        x, y = xy(n); k = n[1]
        if k == "S":
            out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{rl:.2f}" fill="{RED}"/>')
        elif k == "K":
            sd = 1.6 * rl
            out.append(f'<rect x="{x - sd/2:.2f}" y="{y - sd/2:.2f}" width="{sd:.2f}" height="{sd:.2f}" fill="{RED}"/>')
        elif k == "I":
            out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{0.85*rl:.2f}" fill="none" stroke="{RED}" stroke-width="{0.3*rl:.3f}"/>')
    out.append(f'<circle cx="0" cy="0" r="{max(0.6, 0.9*rl):.2f}" fill="none" stroke="{INK}" {ns}/>')
    p = 1.5
    return "\n".join(out), (-R - p, -R - p, 2 * R + 2 * p, 2 * R + 2 * p), n_leaves


def full(term, title, path):
    frag, (vx, vy, vw, vh), n = radial_frag(term)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vx:.2f} {vy:.2f} {vw:.2f} {vh:.2f}" '
           f'width="100%" role="img" aria-label="{esc(title)}">\n'
           f'<title>{esc(title)}</title>\n{frag}\n</svg>\n')
    open(path, "w").write(svg)
    nodes, _ = _nodes(term)
    return n, max(nd[0] for nd in nodes)

def main():
    os.makedirs("figures", exist_ok=True)
    rep = []

    # ---- the terms themselves
    IK = App(I, K)
    for term, title, fn in [
        (UP, "UQ", "fig-term-uq.svg"),
        (WP, "whnfF", "fig-term-whnff.svg"),
        (EQ5, "EQ5", "fig-term-eq5.svg"),
        (encP(IK), "the encoded datum <I K>", "fig-term-enc-ik.svg"),
    ]:
        n = single(term, title, f"figures/{fn}")
        rep.append((fn, tree_size(term), n))
        fullfn = fn.replace("fig-term-", "fig-full-")
        leaves, depth = full(term, title + ", every atom drawn", f"figures/{fullfn}")
        lc = leaf_counts(term)
        rep.append((fullfn, f"{leaves} (S {lc['S']}, K {lc['K']}, I {lc['I']}), depth {depth}", leaves))

    # ---- composites for the paper: spiral beside every-atom disc
    def pair_panels(term, name):
        n_all = tree_size(term)
        n_vis = len(layout(term)[1])
        return [(term, f"{name}", PRUNE),
                (term, f"{name}", PRUNE, radial_frag)]
    c = strip(pair_panels(WP, ""), "figures/fig-pair-whnff.svg",
              "whnfF, the emulator: spiral view beside the every-atom disc, 618 atoms",
              label_pt=10.0)
    rep.append(("fig-pair-whnff.svg", 618, c))
    c = strip(pair_panels(EQ5, "EQ5"), "figures/fig-pair-eq5.svg",
              "EQ5, structural equality on encoded paths: spiral view beside the every-atom disc, 240 atoms",
              label_pt=10.0)
    rep.append(("fig-pair-eq5.svg", 240, c))
    c = strip(pair_panels(UP, "UQ") + pair_panels(encP(IK), "<I K>"), "figures/fig-pair-uq-ik.svg",
              "UQ, the unquoter (43 atoms), and the datum <I K> it decodes (40 atoms), each in spiral and every-atom views",
              label_pt=10.0)
    rep.append(("fig-pair-uq-ik.svg", "43 / 40", c))

    # ---- the one-site diff, side by side
    arms = [(expand(a("errArmAbs"), env), "errArmAbs  4 atoms", 0.0),
            (expand(a("errArmOmg"), env), "errArmOmg  7 atoms", 0.0)]
    c = strip(arms, "figures/fig-arms.svg",
              "The two arms of the authored site: errArmAbs, 4 atoms, and errArmOmg, 7 atoms")
    rep.append(("fig-arms.svg", "4 / 7", c))

    # ---- the engine, part by part
    parts = [("sp", "spine walk"), ("rb", "rebuild"), ("stepI", "I arm"),
             ("stepK", "K arm"), ("stepS", "S arm"), ("UQ", "unquote")]
    panels = []
    for name, label in parts:
        t = expand(a(name), env)
        panels.append((t, f"{name} · {tree_size(t)}", PRUNE))
    c = strip(panels, "figures/fig-engine-parts.svg",
              "The interpreter's components as terms, every atom drawn: sp 126, rb 74, stepI 92, stepK 105, stepS 237, UQ 43 atoms",
              render=radial_frag,
              label_pt=10.0)
    rep.append(("fig-engine-parts.svg", [tree_size(p[0]) for p in panels], c))

    # ---- the engine in motion: whnfF 3 <I K>, the T0 target, at chosen steps
    t0 = A(WP, natP(3), encP(IK))
    steps = [0, 20, 60, 120, 200, 300, 340]
    panels = []
    for n in steps:
        r = fast_reduce(t0, env, max_steps=n) if n else None
        term = r.term if n else t0
        panels.append((term, f"step {n}", 0.12))   # coarser pruning: these trees reach 1e5 leaves
    c = strip(panels, "figures/fig-engine-motion.svg",
              "The emulator running: whnfF 3 <I K> after 0, 20, 60, 120, 200, 300 and 340 host contractions",
              label_pt=10.0)
    rep.append(("fig-engine-motion.svg", steps, c))

    for fn, atoms, drawn in rep:
        print(f"{fn:26s} atoms={atoms}  leaves drawn={drawn}  bytes={os.path.getsize('figures/'+fn):,}")
    to_pdf()


def to_pdf(src_dir="figures", out_dir="build/fig"):
    """Convert every SVG in figures/ (generated or hand-drawn) to the PDF the
    manuscript includes via \\includegraphics{build/fig/NAME.pdf}. Skips
    files whose PDF is newer than the SVG. Needs rsvg-convert."""
    if shutil.which("rsvg-convert") is None:
        print("rsvg-convert not found: SVGs written, PDFs NOT regenerated"); return
    os.makedirs(out_dir, exist_ok=True)
    done = 0
    for svg in sorted(glob.glob(os.path.join(src_dir, "*.svg"))):
        pdf = os.path.join(out_dir, os.path.basename(svg)[:-4] + ".pdf")
        if os.path.exists(pdf) and os.path.getmtime(pdf) >= os.path.getmtime(svg):
            continue
        subprocess.run(["rsvg-convert", "-f", "pdf", "-o", pdf, svg], check=True); done += 1
    print(f"PDFs: {done} regenerated in {out_dir}/ ({len(glob.glob(os.path.join(src_dir, '*.svg')))} SVGs)")


if __name__ == "__main__":
    threading.stack_size(1024 * 1024 * 1024)
    th = threading.Thread(target=main); th.start(); th.join()
