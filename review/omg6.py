import sys, threading, os
sys.setrecursionlimit(10_000_000)
os.chdir('/Users/neal/ski-in-ski')
def main():
    from aviary_kernel.terms import Atom, App, pretty, size as tree
    from aviary_kernel.reduce import Status
    g={}
    exec(open("tower_harness.py").read().split("if __name__")[0], g)
    env=g['env']; a=g['a']; v=g['v']; A=g['A']; D=g['D']; AL=g['AL']
    expand=g['expand']; fast=g['fast_reduce']; enc5=g['enc5']; natP=g['natP']
    S,K,I=a("S"),a("K"),a("I")
    OM=A(A(A(S,I),I),A(A(S,I),I))
    AL("errArmOmg6", OM)                      # 6 atoms, no K wrapper
    D("st5Omg6",["m"], A(a("sp5"), v("m"), a("nil"),
                         a("q5S"), a("q5K"), a("q5I"), a("errArmOmg6")))
    D("wf5Omg61",["w","m","n2"], A(a("st5Omg6"), v("m"),
        A(v("w"), v("n2")), A(a("rVal"), v("m")), a("rErr")))
    D("wf5Omg6Gen",["w","n","m"], A(v("n"), a("rTime"), A(a("wf5Omg61"), v("w"), v("m"))))
    AL("wf5Omg6", A(g['Y'], a("wf5Omg6Gen")))
    print("errArmOmg6 =", pretty(expand(a("errArmOmg6"),env)),
          " tree-atoms =", tree(expand(a("errArmOmg6"),env)))
    WA=expand(a("wf5Abs"),env); WO6=expand(a("wf5Omg6"),env)
    DT=expand(a("decodeTag"),env); enc5P=lambda x: expand(enc5(x),env)
    Err=Atom("Err")
    rows=[("Err",Err),("Err K",App(Err,K)),("K I Err",App(App(K,I),Err)),
          ("I K",App(I,K)),("Omega",OM)]
    print(f"    {'object term':<14s}{'absorbing':>16s}{'hidden(6-atom)':>18s}")
    for label,ot in rows:
        cells=[]
        for Wt in (WA,WO6):
            r=fast(A(DT,A(Wt,natP(20),enc5P(ot))),env,whnf_only=False,max_steps=400_000)
            cells.append(pretty(r.term) if r.status in (Status.NORMAL,Status.WHNF) else "<host diverges>")
        print(f"    {label:<14s}{cells[0]:>16s}{cells[1]:>18s}")
threading.stack_size(1024*1024*1024)
th=threading.Thread(target=main); th.start(); th.join()
