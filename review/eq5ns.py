import sys, threading, os
sys.setrecursionlimit(10_000_000)
os.chdir('/Users/neal/ski-in-ski')
def main():
    from aviary_kernel.terms import Atom, App, pretty, size as tree
    g={}
    exec(open("scry_namespace.py").read().split(chr(10)+chr(105)+chr(102)+" __name__")[0], g)
    env=g['env']; a=g['a']; v=g['v']; A=g['A']; D=g['D']; AL=g['AL']
    expand=g['expand']; fast=g['fast_reduce']; encQ=g['encQ']; Scry=g['Scry']
    WN=g['WN']; natP=g['natP']; peel4=g['peel4']; identify_leaf=g['identify_leaf']
    S,K,I,Y=a("S"),a("K"),a("I"),a("Y")
    D("bT2",["x","y"],v("x")); D("bF2",["x","y"],v("y"))
    D("bAnd2",["p","q"],A(v("p"),v("q"),a("bF2")))
    AL("kkF2", A(K,A(K,a("bF2"))))
    D("e5App2",["e","t","u","t2","u2"],
      A(a("bAnd2"), A(v("e"),v("t"),v("t2")), A(v("e"),v("u"),v("u2"))))
    D("e5App1",["e","n","t","u"],
      A(v("n"), a("bF2"),a("bF2"),a("bF2"), A(a("e5App2"),v("e"),v("t"),v("u")), a("bF2")))
    D("e5N",["e","m","n"], A(v("m"),
        A(v("n"), a("bT2"),a("bF2"),a("bF2"),a("kkF2"),a("bF2")),
        A(v("n"), a("bF2"),a("bT2"),a("bF2"),a("kkF2"),a("bF2")),
        A(v("n"), a("bF2"),a("bF2"),a("bT2"),a("kkF2"),a("bF2")),
        A(a("e5App1"), v("e"), v("n")),
        A(v("n"), a("bF2"),a("bF2"),a("bF2"),a("kkF2"),a("bT2"))))
    D("e5Gen",["e","m"], A(a("e5N"), v("e"), v("m")))
    AL("EQ5", A(Y,a("e5Gen")))
    EQ5=expand(a("EQ5"),env)
    def leaves(t):
        st,out=[t],set()
        while st:
            x=st.pop()
            if isinstance(x,Atom): out.add(x.name)
            else: st.append(x.fn); st.append(x.arg)
        return out
    print("EQ5 basis:",sorted(leaves(EQ5)),"tree-atoms:",tree(EQ5))

    # namespace oracle over ARBITRARY COMPOUND paths, keyed by structural equality
    def compound_oracle(table):
        """table: list of (object-path-term, object-answer-term). Builds a pure
        SKI oracle: EQ5 p <key_i> (oJust <ans_i>) (... else ...) ending in oNotYet."""
        body = a("oNotYet")
        for path, ans in reversed(table):
            body = A(a("EQ5"), v("p"), encQ(path),
                     A(a("oJust"), encQ(ans)), body)
        nm=f"cmpOracle{len(table)}_{id(body)%9999}"
        D(nm,["p"],body)
        return expand(a(nm),env)

    def run(term, table, fuel):
        E=compound_oracle(table)
        r=fast(A(WN,E,natP(fuel),encQ(term)),env,max_steps=50_000_000)
        if r.status.value!="whnf": return ("status:"+r.status.value,None)
        return peel4(r.term)

    # Compound paths -- exactly what PAPER.md 7.2 says SK cannot do
    tests=[
      ("Scry (S K)  with namespace {(S K)->I}",      Scry(App(S,K)), [(App(S,K), I)]),
      ("Scry (S K)  with namespace {(K S)->I}",      Scry(App(S,K)), [(App(K,S), I)]),
      ("Scry (S K K) with ns {(S K)->I,(S K K)->K}", Scry(A(S,K,K)), [(App(S,K),I),(A(S,K,K),K)]),
      ("Scry (S K)  with ns {(S K K)->K,(S K)->S}",  Scry(App(S,K)), [(A(S,K,K),K),(App(S,K),S)]),
    ]
    for label,t,tab in tests:
        tag,payload=run(t,tab,30)
        leaf = identify_leaf(payload) if payload is not None else None
        print(f"  {label:<48s} -> {tag}  leaf={leaf}")
threading.stack_size(1024*1024*1024)
th=threading.Thread(target=main); th.start(); th.join()
