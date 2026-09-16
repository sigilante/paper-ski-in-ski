import sys, threading, io, contextlib, time
sys.setrecursionlimit(10_000_000)
def main():
    from aviary_kernel.terms import Atom, App, pretty, size as tsize
    g = {}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(open("scry_paths.py").read().split('\nif __name__ == "__main__":\n')[0], g)
    for k in ("env","a","v","A","D","AL","expand","fast_reduce","encQ","Scry","natP","peel4","decode_path",
              "WQ","WN","S","K","I","Y","mkAppQ","identify_leaf"):
        globals()[k] = g[k]
    import resource
    def mem(): return f"{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1e9:.2f} GB"
    # ---- Stage 1: inert unknowns
    D("stepScP1", ["e","p","rest"], A(v("e"), v("p"), A(a("scHitN"), v("rest")), a("errdN"), a("doneN")))
    D("stepScP",  ["e","args"], A(v("args"), a("doneN"), A(a("stepScP1"), v("e"))))
    D("stepPE",   ["e","m"], A(a("spQ"), v("m"), a("nil"), a("stepSN"), a("stepKN"), a("stepIN"), A(a("stepScP"), v("e"))))
    D("wfP1",  ["e","w","m","n2"], A(a("stepPE"), v("e"), v("m"), A(v("w"), v("e"), v("n2")), A(a("rValN"), v("m")), a("rErrN"), a("rBlockN")))
    D("wfPGen", ["w","e","n","m"], A(v("n"), a("rTimeN"), A(a("wfP1"), v("e"), v("w"), v("m"))))
    AL("wfP", A(Y, a("wfPGen")))
    WPP = expand(a("wfP"), env)
    D("oNotYetAll", ["p"], a("oNotYet"))
    E2 = expand(a("oNotYetAll"), env)
    def leaves(t):
        st,out=[t],set()
        while st:
            x=st.pop()
            if isinstance(x,Atom): out.add(x.name)
            else: st.append(x.fn); st.append(x.arg)
        return out
    print("wfP tree-atoms", tsize(WPP), "basis", sorted(leaves(WPP)))
    def runP(E, t, fuel, enc=True, max_steps=20_000_000):
        q = encQ(t) if enc else t
        r = fast_reduce(A(WPP, E, natP(fuel), q), env, max_steps=max_steps, max_size=30_000_000)
        if r.status.value != "whnf": return ("status:"+r.status.value, None, r.steps)
        tag, payload = peel4(r.term)
        return (tag, payload, r.steps)
    a_ = Atom  # noqa
    OMEGA = App(App(App(S,I),I),App(App(S,I),I))
    cases = [("I K", App(I,K)), ("K (Scry S) Omega", App(App(K, Scry(S)), OMEGA)),
             ("S K K (Scry S)", App(App(App(S,K),K), Scry(S))), ("Scry S K", App(Scry(S), K)), ("Scry S", Scry(S))]
    for label, t in cases:
        tag, payload, st = runP(E2, t, 10)
        d = decode_path(payload) if payload is not None else None
        print(f"  {label:22s} -> {tag:5s} residual={pretty(d) if d else None}")
    # oJust / oNothing still work
    D("oJustS_I", ["p"], A(a("oJust"), a("encIQ")))   # every path -> I
    D("oNothingAll", ["p"], a("oNothing"))
    for label, E in [("all->I", expand(a("oJustS_I"), env)), ("nothing", expand(a("oNothingAll"), env))]:
        tag, payload, st = runP(E, Scry(S), 10)
        print(f"  Scry S under {label:8s} -> {tag} {pretty(decode_path(payload)) if payload is not None else ''}")
    tag, payload, st = runP(E2, OMEGA, 5); print("  Omega fuel 5 ->", tag)

    # ---- (P1) fuel equation on t = S K K (Scry S), E' = S -> I
    def runN(E, t, fuel):
        r = fast_reduce(A(WN, E, natP(fuel), encQ(t)), env, max_steps=50_000_000)
        tag, payload = peel4(r.term); return tag, (decode_path(payload) if payload is not None else None)
    Ep = expand(a("oJustS_I"), env)
    t = App(App(App(S,K),K), Scry(S))
    tagP, payP, _ = runP(E2, t, 10); r = decode_path(payP)
    s = 3  # 2 contractions + the attempt that met the unknown
    for k in (4, 6):
        o = runN(Ep, t, k); rr = runN(Ep, r, k - s + 1)
        print(f"  (P1) k={k}: original -> {o[0]} {pretty(o[1])}; residual at k-s+1={k-s+1} -> {rr[0]} {pretty(rr[1])}")

    if 'futamura' not in sys.argv: return
    # ---- Futamura, stage 1 only: specialize wfQ (Scry K) k <p> with p = I (Scry I)
    p = App(I, Scry(I)); k1 = 5
    L = A(WQ, Scry(K), natP(k1), expand(encQ(p), env))          # level-1 term, E unknown as `Scry K`
    print("level-1 term atoms", tsize(L))
    t0 = time.time()
    tag, payload, st = runP(E2, L, 1500)
    print(f"  level-2 wfP: {tag} in {st:,} host contractions, {time.time()-t0:.1f}s, maxrss {mem()}", flush=True)
    if payload is None: return
    r = decode_path(payload)
    print("  decoded", mem(), flush=True)
    # spine of residual
    hd, args = r, []
    while isinstance(hd, App): args.append(hd.arg); hd = hd.fn
    args.reverse()
    print("  residual head:", hd.name, "| path:", pretty(args[0]), "| further args:", len(args)-1, "| atoms:", tsize(r))
    # instantiate: substitute E0 for the placeholder `Scry K`
    D("oracleIn", ["p"], A(a("just"), a("encKQ")))     # level-1 Maybe oracle: every path -> <K>
    E0 = expand(a("oracleIn"), env)
    def subst(t):
        if isinstance(t, App):
            if isinstance(t.fn, Atom) and t.fn.name == "Scry" and isinstance(t.arg, Atom) and t.arg.name == "K":
                return E0
            return App(subst(t.fn), subst(t.arg))
        return t
    rE = subst(r)
    orig = A(WQ, E0, natP(k1), expand(encQ(p), env))
    def run1(term):
        res = fast_reduce(term, env, max_steps=50_000_000)
        un = fast_reduce(A(res.term, Atom("C1"), Atom("C2"), Atom("C3")), env, max_steps=200_000)
        txt = pretty(un.term)
        if txt.startswith("C1 "):
            X = [Atom(f"X{i}") for i in range(1,6)]
            pr = fast_reduce(A(un.term.arg, *X), env, whnf_only=False, max_steps=200_000)
            return "VAL", pretty(pr.term), res.steps
        return txt, None, res.steps
    o = run1(orig); rr = run1(rE)
    print(f"  original wfQ E0 {k1} <p> -> {o[0]} payload-probe={o[1]} in {o[2]:,} host contractions")
    print(f"  residual[E0]             -> {rr[0]} payload-probe={rr[1]} in {rr[2]:,} host contractions")
    print(f"  saved: {o[2]-rr[2]:,} host contractions ({100*(o[2]-rr[2])/o[2]:.0f}%)")
threading.stack_size(1024*1024*1024); th=threading.Thread(target=main); th.start(); th.join()
