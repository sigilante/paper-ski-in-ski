import sys, threading, os
sys.setrecursionlimit(10_000_000)
os.chdir('/Users/neal/ski-in-ski')
def main():
    from aviary_kernel.terms import Atom, App, pretty, size as tree
    g={}
    exec(open("tower_harness.py").read().split("if __name__")[0], g)
    env=g['env']; a=g['a']; v=g['v']; A=g['A']; D=g['D']; AL=g['AL']
    expand=g['expand']; fast=g['fast_reduce']; enc=g['enc']
    S,K,I,Y=a("S"),a("K"),a("I"),a("Y")

    # Booleans: T x y = x, F x y = y
    D("bT",["x","y"],v("x"))
    D("bF",["x","y"],v("y"))
    D("bAnd",["p","q"], A(v("p"), v("q"), a("bF")))
    # constant-F in the 2-ary app slot
    AL("kkF", A(K, A(K, a("bF"))))
    # eqGen e m n
    D("eqApp2",["e","t","u","t2","u2"],
      A(a("bAnd"), A(v("e"), v("t"), v("t2")), A(v("e"), v("u"), v("u2"))))
    D("eqApp1",["e","n","t","u"],
      A(v("n"), a("bF"), a("bF"), a("bF"), A(a("eqApp2"), v("e"), v("t"), v("u"))))
    D("eqN",["e","m","n"], A(v("m"),
        A(v("n"), a("bT"), a("bF"), a("bF"), a("kkF")),
        A(v("n"), a("bF"), a("bT"), a("bF"), a("kkF")),
        A(v("n"), a("bF"), a("bF"), a("bT"), a("kkF")),
        A(a("eqApp1"), v("e"), v("n"))))
    D("eqGen",["e","m"], A(a("eqN"), v("e"), v("m")))
    AL("EQ", A(Y, a("eqGen")))
    EQ=expand(a("EQ"), env)
    def leaves(t):
        st,out=[t],set()
        while st:
            x=st.pop()
            if isinstance(x,Atom): out.add(x.name)
            else: st.append(x.fn); st.append(x.arg)
        return out
    print("EQ basis:", sorted(leaves(EQ)), " tree-atoms:", tree(EQ))

    encP=lambda t: expand(enc(t), env)
    def test(t1,t2):
        r=fast(A(EQ, encP(t1), encP(t2), Atom("TRUE"), Atom("FALSE")),
               env, whnf_only=False, max_steps=2_000_000)
        return pretty(r.term), r.steps
    SKK=A(S,K,K)
    cases=[(I,I),(SKK,SKK),(SKK,I),(I,SKK),(K,K),(K,S),
           (A(K,I),A(K,I)),(A(K,I),A(I,K)),
           (A(S,A(K,K),K), A(S,A(K,K),K)),
           (A(S,A(K,K),K), A(S,A(K,K),I)),
           (A(A(S,I),I), A(A(S,I),I)),
           (A(A(S,I),I), A(A(S,I),K)),
           (A(S,K,K,I,K), A(S,K,K,I,K)),
           (A(S,K,K,I,K), A(S,K,K,K,K)),
          ]
    for t1,t2 in cases:
        r,st=test(t1,t2)
        print(f"  EQ <{pretty(t1)}> <{pretty(t2)}>  =>  {r}   ({st} steps)")
threading.stack_size(1024*1024*1024)
th=threading.Thread(target=main); th.start(); th.join()
