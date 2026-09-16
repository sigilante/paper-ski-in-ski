#!/usr/bin/env python3
"""Regenerate build/mss-from-md.tex from PAPER.md (historical; mss.tex is
the hand-edited canonical manuscript since 2026-09-15 and is NOT written).

Preamble: copied from the murmuration-i.tex preamble (Davis2026, pure
S-calculus), with the title/author replaced and two packages added
(stmaryrd for double brackets, calc for pandoc's longtable column specs).
Body: pandoc (gfm -> latex) on the abstract and the sections separately,
with the H1 as \\title, "## 0. Abstract" as the abstract environment, and
the italic front-matter paragraph as a note after the abstract. The
paper's Unicode (angle brackets, Omega, arrows, superscripts, the
combining tilde on M) is mapped to macros so pdfLaTeX compiles it.

Usage:
    python3 build_tex.py            # writes mss.tex, then runs latexmk -pdf
    python3 build_tex.py --no-pdf   # writes mss.tex only
"""
import re, subprocess, sys, os, shutil, tempfile

SRC = "PAPER.md"
OUT = "build/mss-from-md.tex"   # mss.tex is hand-edited and canonical since 2026-09-15; never write it
PREAMBLE_FROM = os.path.expanduser(
    "~/Documents/Davis2026 Universality of the Pure S Calculus/murmuration-i.tex")
AUTHOR = r"N.\ E.\ Davis"

md = open(SRC, encoding="utf-8").read()

# ---- split the markdown: title, preface, abstract, body
m = re.match(r"# (.+)\n", md)
title = m.group(1).strip()
rest = md[m.end():]
pre_m = re.search(r"\n\*(.+?)\*\n\n## 0\. Abstract\n", rest, re.S)
preface = pre_m.group(1).replace("\n", " ").strip()
abs_m = re.search(r"## 0\. Abstract\n(.+?)\n## 1\. ", rest, re.S)
abstract_md = abs_m.group(1).strip()
body_md = rest[rest.index("## 1. "):]
# LaTeX numbers sections itself; drop the markdown's own "N." / "N.M" prefixes
body_md = re.sub(r"^(#{2,3}) \d+(?:\.\d+)?\.? ", r"\1 ", body_md, flags=re.M)


def pandoc(text, shift):
    return subprocess.run(
        ["pandoc", "-f", "gfm+smart+implicit_figures", "-t", "latex", f"--shift-heading-level-by={shift}"],
        input=text, capture_output=True, text=True, check=True).stdout


# ---- Unicode -> LaTeX (order matters: multi-char sequences first)
SUP = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6",
       "⁷": "7", "⁸": "8", "⁹": "9", "ⁿ": "n"}
def texify(s):
    s = re.sub(r"(\w)\u0303", r"$\\tilde{\1}$", s)                     # M̃
    s = re.sub("[" + "".join(SUP) + "]+",
               lambda mm: "$^{" + "".join(SUP[c] for c in mm.group(0)) + "}$", s)
    table = {
        "§": r"\S{}", "Ω": r"$\Omega$", "λ": r"$\lambda$", "η": r"$\eta$",
        "↦": r"$\mapsto$", "↠": r"$\twoheadrightarrow$", "→": r"$\to$",
        "⟨": r"$\langle$", "⟩": r"$\rangle$",
        "⟦": r"$\llbracket$", "⟧": r"$\rrbracket$",
        "⊥": r"$\bot$", "≤": r"$\leq$", "·": r"$\cdot$", "−": r"$-$", "×": r"$\times$",
    }
    for k, v in table.items():
        s = s.replace(k, v)
    # pandoc >= 3.x wraps uncaptioned tables in {\def\LTcaptype{none} ... },
    # which this preamble's longtable rejects ("No counter 'none'"); unwrap.
    s = re.sub(r"\{\\def\\LTcaptype\{none\}[^\n]*\n(.*?\\end\{longtable\})\n\}",
               r"\1", s, flags=re.S)
    # pandoc writes code-span spaces as "\\ " (unbreakable); let them break
    s = re.sub(r"\\texttt\{((?:[^{}]|\{[^{}]*\})*)\}", lambda mm: "\\texttt{" + mm.group(1).replace("\\ ", " ").replace("/", "/\\allowbreak{}") + "}", s)
    # figures: pandoc emits \\pandocbounded{\\includesvg[..]{figures/X.svg}};
    # convert each SVG to PDF (rsvg-convert) and include that at text width
    def fig(mm):
        svg = mm.group(1)
        pdf = os.path.join("build", "fig", os.path.basename(svg)[:-4] + ".pdf")
        os.makedirs(os.path.dirname(pdf), exist_ok=True)
        if not os.path.exists(pdf) or os.path.getmtime(pdf) < os.path.getmtime(svg):
            subprocess.run(["rsvg-convert", "-f", "pdf", "-o", pdf, svg], check=True)
        return "\\includegraphics[width=\\linewidth]{" + pdf + "}"
    s = re.sub(r"\\pandocbounded\{\\includesvg\[[^\]]*\]\{([^}]+\.svg)\}\}", fig, s)
    s = s.replace("\\begin{figure}\n", "\\begin{figure}[htbp]\n")
    # tables with long prose cells: give them wrapping paragraph columns
    def widen(mm):
        block = mm.group(0)
        spec = mm.group(1)
        ncol = len(spec)
        rows = [r for r in block.split("\\\\") if "&" in r]
        longest = max((len(c.strip()) for r in rows for c in r.split("&")), default=0)
        if longest < 40:
            return block
        widths = {2: [0.34, 0.58], 3: [0.32, 0.30, 0.30]}.get(ncol, [0.92 / ncol] * ncol)
        newspec = "".join(f">{{\\raggedright\\arraybackslash}}p{{{w:.2f}\\linewidth}}" for w in widths)
        return block.replace("{@{}" + spec + "@{}}", "{@{}" + newspec + "@{}}", 1)
    s = re.sub(r"\\begin\{longtable\}\[\]\{@\{\}(l+)@\{\}\}.*?\\end\{longtable\}", widen, s, flags=re.S)
    return s


abstract_tex = texify(pandoc(abstract_md, 0))
body_tex = texify(pandoc(body_md, -1))          # ## -> \section, ### -> \subsection
preface_tex = texify(pandoc(preface, 0)).strip()
title_tex = texify(title)

# ---- preamble from the murmuration paper, up to \begin{document}
src = open(PREAMBLE_FROM, encoding="utf-8").read()
pre = src[:src.index(r"\begin{document}")]
pre = re.sub(r"\\title\{.*?\}\n(?=\\author)", "", pre, flags=re.S)
pre = re.sub(r"\\author\{.*?\}\n", "", pre)
pre = re.sub(r"\\date\{.*?\}\n", "", pre)
pre = pre.replace(r"\usepackage{longtable}", "\\usepackage{longtable}\n\\usepackage{array}\n\\usepackage{calc}\n\\usepackage{stmaryrd}")
pre += (
    "\\providecommand{\\tightlist}{\\setlength{\\itemsep}{0pt}\\setlength{\\parskip}{0pt}}\n"
    "\\setlength{\\emergencystretch}{3em}\n"
    f"\\title{{{title_tex}}}\n"
    f"\\author{{{AUTHOR}}}\n"
    "\\date{\\today}\n"
)

doc = (pre + "\n\\begin{document}\n\\maketitle\n\n"
       "\\begin{abstract}\n" + abstract_tex + "\\end{abstract}\n\n"
       "\\noindent\\emph{" + preface_tex + "}\n\n" + body_tex + "\n\\end{document}\n")
open(OUT, "w", encoding="utf-8").write(doc)
print(f"wrote {OUT}: {len(doc.splitlines())} lines; preamble from {os.path.basename(PREAMBLE_FROM)}")

if "--no-pdf" in sys.argv:
    sys.exit(0)
build = "build"
os.makedirs(build, exist_ok=True)
r = subprocess.run(["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error",
                    f"-outdir={build}", OUT], capture_output=True, text=True)
log = open(os.path.join(build, "mss.log"), encoding="utf-8", errors="replace").read() if os.path.exists(os.path.join(build, "mss.log")) else r.stdout
errs = [l for l in log.splitlines() if l.startswith("!")]
warns = [l for l in log.splitlines() if "Overfull" in l or "undefined" in l.lower()]
if r.returncode == 0 and os.path.exists(os.path.join(build, "mss.pdf")):
    shutil.copy(os.path.join(build, "mss.pdf"), "mss.pdf")
    print(f"built mss.pdf; {len(errs)} errors, {len(warns)} overfull/undefined warnings")
else:
    print("BUILD FAILED"); print("\n".join(errs[:10])); print(r.stdout[-2000:])
    sys.exit(1)
