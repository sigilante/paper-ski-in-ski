import sys, threading, io, contextlib, time, resource
sys.setrecursionlimit(10_000_000)
def mem(): return f"{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1e9:.2f}GB"
def main():
    from aviary_kernel.terms import Atom, App, pretty, size as tsize
    g={}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(open("scry_paths.py").read().split('\nif __name__ == "__main__":\n')[0], g)
    for k in ("env","a","v","A","D","AL","expand","fast_reduce","encQ","Scry","natP","peel4","WQ","WN","EQ5","S","K","I","Y","size"):
        globals()[k]=g[k]
    D("stepScP1", ["e","p","rest"], A(v("e"), v("p"), A(a("scHitN"), v("rest")), a("errdN"), a("doneN")))
    D("stepScP",  ["e","args"], A(v("args"), a("doneN"), A(a("stepScP1"), v("e"))))
    D("stepPE",   ["e","m"], A(a("spQ"), v("m"), a("nil"), a("stepSN"), a("stepKN"), a("stepIN"), A(a("stepScP"), v("e"))))
    D("wfP1",  ["e","w","m","n2"], A(a("stepPE"), v("e"), v("m"), A(v("w"), v("e"), v("n2")), A(a("rValN"), v("m")), a("rErrN"), a("rBlockN")))
    D("wfPGen", ["w","e","n","m"], A(v("n"), a("rTimeN"), A(a("wfP1"), v("e"), v("w"), v("m"))))
    AL("wfP", A(Y, a("wfPGen"))); WPP = expand(a("wfP"), env)
    D("oNotYetAll", ["p"], a("oNotYet")); E2 = expand(a("oNotYetAll"), env)
    D("oracleIn", ["p"], A(a("just"), a("encKQ"))); E0 = expand(a("oracleIn"), env)
    # level-2 resolving oracle: path K -> oJust <E0>; everything else not yet
    D("oracleK2", ["p"], A(a("spQ"), v("p"), a("nil"),
        A(K, a("oNotYet")), A(K, A(a("oJust"), encQ(E0))), A(K, a("oNotYet")), A(K, a("oNotYet"))))
    E2r = expand(a("oracleK2"), env)
    X = [Atom(f"X{i}") for i in range(1,6)]
    def spine(t):
        args=[]
        while isinstance(t, App): args.append(t.arg); t=t.fn
        return t, list(reversed(args))
    def probe(t):
        r = fast_reduce(A(t, *X), env, max_steps=2_000_000, max_size=3_000_000)
        return spine(r.term)
    def spine2(payload):
        """walk the level-2 datum's function spine only: returns (head leaf name, [arg thunks])"""
        args=[]; t=payload
        while True:
            hd, a2 = probe(t)
            if isinstance(hd, Atom) and hd.name=="X4" and len(a2)==2:
                args.append(a2[1]); t=a2[0]
            else:
                return hd.name, list(reversed(args))
    def run2(loop, E, fuel, datum, label):
        t0=time.time()
        r = fast_reduce(A(loop, E, natP(fuel), datum), env, max_steps=8_000_000, max_size=3_000_000)
        if r.status.value!="whnf":
            print(f"  {label:44s} -> status {r.status.value} after {r.steps:,} ({time.time()-t0:.0f}s)", flush=True); return None
        tag, payload = peel4(r.term)
        print(f"  {label:44s} -> {tag} in {r.steps:,} host contractions ({time.time()-t0:.0f}s, {mem()})", flush=True)
        return tag, payload
    p = App(I, Scry(I)); k1 = 5
    L = A(WQ, Scry(K), natP(k1), expand(encQ(p), env)); q = encQ(L)
    # (a) specialize
    res = run2(WPP, E2, 644, q, "specialize: wfP E2 644 <L>")
    tag, R = res
    # (b) spine of the residual
    hd, args = spine2(R)
    ph, _ = probe(args[0])
    print(f"  residual spine: head={hd} ({'Scry' if hd=='X5' else '?'}), path probes to {ph.name} ({'K' if ph.name=='X2' else '?'}), further args={len(args)-1}", flush=True)
    # (c) original at level 2 under the resolving oracle; (d) residual at level 2; (e) fuel boundary
    O = run2(WN, E2r, 900, q, "original: wfN E2r 900 <L>")
    Rv = run2(WN, E2r, 257, R, "residual: wfN E2r 257 R   (= 900-644+1)")
    Rmin = run2(WN, E2r, 249, R, "residual: wfN E2r 249 R   (minimal)")
    Rlow = run2(WN, E2r, 248, R, "residual: wfN E2r 248 R   (one short)")
    # (f) structural equality of the two final level-1 terms, at level 2
    if O and Rv and O[0]=="VAL" and Rv[0]=="VAL":
        t0=time.time()
        eq = fast_reduce(A(EQ5, O[1], Rv[1], Atom("TRUE"), Atom("FALSE")), env, whnf_only=False, max_steps=8_000_000, max_size=3_000_000)
        print(f"  EQ5 original-value residual-value -> {pretty(eq.term)} ({time.time()-t0:.0f}s)", flush=True)
threading.stack_size(1024*1024*1024); th=threading.Thread(target=main); th.start(); th.join()
