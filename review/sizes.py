import sys, threading
sys.setrecursionlimit(10_000_000)
sys.path.insert(0,'/Users/neal/ski-in-ski')
import os
os.chdir('/Users/neal/ski-in-ski')
def main():
    from aviary_kernel.terms import size as tree
    _H = open("tower_harness.py").read().split("if __name__")[0]
    g = {}
    exec(_H, g)
    env = g['env']; a = g['a']; expand = g['expand']
    for nm in ["whnfF","UQ","errArmAbs","errArmOmg","errd","wf5Abs","wf5Omg"]:
        t = expand(a(nm), env)
        print(f"{nm:12s} tree={tree(t):6d}  dag={g['size'](t):6d}")
    # OMEGA
    S,K,I = a("S"),a("K"),a("I")
    A = g['A']
    OM = A(A(A(S,I),I),A(A(S,I),I))
    print("OMEGA tree=", tree(OM))
    from aviary_kernel.terms import pretty
    print("errArmAbs =", pretty(expand(a("errArmAbs"),env)))
    print("errArmOmg =", pretty(expand(a("errArmOmg"),env)))
    print("errd      =", pretty(expand(a("errd"),env)))
threading.stack_size(1024*1024*1024)
th = threading.Thread(target=main); th.start(); th.join()
