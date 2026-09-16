import sys, threading, io, contextlib, time, resource
sys.setrecursionlimit(10_000_000)
def mem(): return f"{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1e9:.2f}GB"
def main():
    from aviary_kernel.terms import Atom, App, pretty, size as tsize
    g={}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(open("scry_paths.py").read().split('\nif __name__ == "__main__":\n')[0], g)
    for k in ("env","a","v","A","D","AL","expand","fast_reduce","encQ","Scry","natP","peel4","WQ","S","K","I","Y","size"):
        globals()[k]=g[k]
    D("stepScP1", ["e","p","rest"], A(v("e"), v("p"), A(a("scHitN"), v("rest")), a("errdN"), a("doneN")))
    D("stepScP",  ["e","args"], A(v("args"), a("doneN"), A(a("stepScP1"), v("e"))))
    D("stepPE",   ["e","m"], A(a("spQ"), v("m"), a("nil"), a("stepSN"), a("stepKN"), a("stepIN"), A(a("stepScP"), v("e"))))
    D("wfP1",  ["e","w","m","n2"], A(a("stepPE"), v("e"), v("m"), A(v("w"), v("e"), v("n2")), A(a("rValN"), v("m")), a("rErrN"), a("rBlockN")))
    D("wfPGen", ["w","e","n","m"], A(v("n"), a("rTimeN"), A(a("wfP1"), v("e"), v("w"), v("m"))))
    AL("wfP", A(Y, a("wfPGen"))); WPP = expand(a("wfP"), env)
    D("oNotYetAll", ["p"], a("oNotYet")); E2 = expand(a("oNotYetAll"), env)
    D("oracleIn", ["p"], A(a("just"), a("encKQ"))); E0 = expand(a("oracleIn"), env)
    X = [Atom(f"X{i}") for i in range(1,6)]
    def spine(t):
        args=[]
        while isinstance(t, App): args.append(t.arg); t=t.fn
        return t, list(reversed(args))
    def subst(t, memo):
        if id(t) in memo: return memo[id(t)]
        if isinstance(t, App):
            if isinstance(t.fn, Atom) and t.fn.name=="Scry" and isinstance(t.arg, Atom) and t.arg.name=="K": r = E0
            else: r = App(subst(t.fn, memo), subst(t.arg, memo))
        else: r = t
        memo[id(t)] = r; return r
    def run1(term, label):
        res = fast_reduce(term, env, max_steps=50_000_000, max_size=5_000_000)
        un = fast_reduce(A(res.term, Atom("C1"), Atom("C2"), Atom("C3")), env, max_steps=200_000)
        txt = pretty(un.term)
        out = txt
        if txt.startswith("C1 "):
            pr = fast_reduce(A(un.term.arg, *X), env, whnf_only=False, max_steps=200_000)
            out = "VAL " + pretty(pr.term)
        print(f"  {label:34s} -> {out:10s} in {res.steps:,} host contractions", flush=True)
        return out, res.steps
    p = App(I, Scry(I)); k1 = 5
    L = A(WQ, Scry(K), natP(k1), expand(encQ(p), env))
    # (1) host-side Stage-1 semantics: WHNF with Scry inert
    rh = fast_reduce(L, env, max_steps=5_000_000, max_size=5_000_000)
    hd, args = spine(rh.term)
    print(f"host residual: head={pretty(hd)} path={pretty(args[0])} further-args={len(args)-1} prefix-contractions={rh.steps} dag={size(rh.term)}", flush=True)
    o = run1(A(WQ, E0, natP(k1), expand(encQ(p), env)), "original  wfQ E0 5 <I (Scry I)>")
    h = run1(subst(rh.term, {}), "host residual[E0]")
    print(f"  saved by host residual: {o[1]-h[1]:,} host contractions = prefix {rh.steps} + splice bookkeeping", flush=True)
    # (2) level-2: the specializer itself
    q = encQ(L); fuel = rh.steps + 1
    t0=time.time()
    rr = fast_reduce(A(WPP, E2, natP(fuel), q), env, max_steps=5_000_000, max_size=3_000_000)
    print(f"level-2 wfP fuel={fuel}: status={rr.status.value} steps={rr.steps:,} {time.time()-t0:.0f}s {mem()}", flush=True)
    if rr.status.value != "whnf": return
    tag, payload = peel4(rr.term); print("  outer tag:", tag, flush=True)
    if tag != "VAL": return
    # memoized behavioral decode of the level-2 datum back to a level-1 term
    memo = {}
    def decode(t):
        if id(t) in memo: return memo[id(t)]
        r = fast_reduce(A(t, *X), env, max_steps=2_000_000, max_size=3_000_000)
        hd, args = spine(r.term)
        if isinstance(hd, Atom) and hd.name in ("X1","X2","X3","X5") and not args:
            out = Atom({"X1":"S","X2":"K","X3":"I","X5":"Scry"}[hd.name])
        elif isinstance(hd, Atom) and hd.name=="X4" and len(args)==2:
            out = App(decode(args[0]), decode(args[1]))
        else:
            raise RuntimeError("undecodable node: " + pretty(r.term)[:80])
        memo[id(t)] = out; return out
    t0=time.time(); r1 = decode(payload)
    hd, args = spine(r1)
    print(f"  level-2 residual decoded ({time.time()-t0:.0f}s, {len(memo)} nodes, {mem()}): head={pretty(hd)} path={pretty(args[0])} further-args={len(args)-1}", flush=True)
    l = run1(subst(r1, {}), "level-2 residual[E0]")
    print("  agreement: host residual value == level-2 residual value ==", o[0], ":", h[0]==l[0]==o[0])
threading.stack_size(1024*1024*1024); th=threading.Thread(target=main); th.start(); th.join()
