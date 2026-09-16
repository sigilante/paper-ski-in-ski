import sys, threading, os
sys.setrecursionlimit(10_000_000)
os.chdir('/Users/neal/ski-in-ski')
def main():
    from aviary_kernel.terms import Atom, App, pretty, size as tree
    g={}
    exec(open("tower_harness.py").read().split("if __name__")[0], g)
    env=g['env']; a=g['a']; A=g['A']; expand=g['expand']; fast=g['fast_reduce']
    WP=g['WP']; natP=g['natP']; encP=g['encP']; enc=g['enc']
    S,K,I=a("S"),a("K"),a("I")
    def build_left(n):   # I I I ... I K  (left-assoc), n copies of I
        t=I
        for _ in range(n-1): t=App(t,I)
        return App(t,K)
    def build_right(n):  # I (I (... (I K)))
        t=K
        for _ in range(n): t=App(I,t)
        return t
    for name,mk in (("left-assoc I^n K",build_left),("right-nested I^n K",build_right)):
        for n in (31,):
            t=mk(n)
            # host reduction step count to WHNF
            r=fast(t, env, max_steps=10**7)
            print(f"{name} n={n}: host steps to WHNF = {r.steps}, term={pretty(r.term)}")
            # emulator: find minimal fuel giving a value
            found=None
            for k in range(0,40):
                res=fast(A(WP,natP(k),encP(t)),env,max_steps=10**7)
                out=g['decode'](res.term,env,10**7)
                txt=pretty(out.term)
                tag = 'NO' if txt.strip()=='NO' else 'JU'
                if tag=='JU':
                    found=k; break
            print(f"   minimal object fuel k for a value: {found}")
    # Omega applied to an argument: does it still diverge (host)?
    OM=A(A(A(S,I),I),A(A(S,I),I))
    r=fast(App(OM,Atom("x")),env,max_steps=5000)
    print("Omega x status:",r.status)
    r=fast(OM,env,max_steps=5000)
    print("Omega   status:",r.status)
threading.stack_size(1024*1024*1024)
th=threading.Thread(target=main); th.start(); th.join()
