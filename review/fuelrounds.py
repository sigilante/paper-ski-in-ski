import sys, threading, os
sys.setrecursionlimit(10_000_000)
os.chdir('/Users/neal/ski-in-ski')
def main():
    from aviary_kernel.terms import Atom, App, pretty
    g={}
    exec(open("scry_namespace.py").read().split(chr(10)+"if __name__")[0], g)
    S,K,I=g['a']("S"),g['a']("K"),g['a']("I")
    Scry=g['Scry']; run=g['run_with_namespace']
    resolution={"S": Scry(K), "K": I}
    print("chained example  Scry S,  resolution {S->Scry K, K->I}")
    for fuel in range(1,8):
        print(f"   fuel={fuel}: {run(Scry(S), resolution, fuel)}")
    print()
    print("single block  I (Scry K), resolution {K->I}")
    for fuel in range(1,8):
        print(f"   fuel={fuel}: {run(App(I,Scry(K)), {'K':I}, fuel)}")
    print()
    print("baseline K I Omega under whnfF (no Scry):")
    env=g['env']; A=g['A']; a=g['a']; fast=g['fast_reduce']
    WP=g['WP']; natP=g['natP']; encP=g['encP']; decode=g['decode']
    OM=A(A(A(S,I),I),A(A(S,I),I))
    t=A(K,I,OM)
    r=fast(A(WP,natP(5),encP(t)),env,max_steps=10**7)
    print("   status:",r.status, " decoded:", pretty(decode(r.term,env,10**7).term)[:60])
threading.stack_size(1024*1024*1024)
th=threading.Thread(target=main); th.start(); th.join()
