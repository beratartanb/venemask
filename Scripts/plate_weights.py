"""Plate blend shares of M_Projection at the K poses and in between (pure Python, no Unreal needed).

Weights follow Scripts/ue_hybrid.py: w_i = 1 / (d_i^4 + 1e-6), d_i = distance (m) from the render
camera to plate camera i, normalised over the plates. Run to regenerate the table in the report.
"""
import math

K0 = (-150.0, -75.0, 130.0)
K1 = (-129.875, -115.249, 130.0)
K2 = (-116.724, -64.347, 127.941)
P = {"K0": K0, "K1": K1, "K2": K2}


def dist_m(a, b):
    return math.dist(a, b) / 100.0


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def shares(pos, wf):
    w = {k: wf(dist_m(pos, v)) for k, v in P.items()}
    s = sum(w.values())
    return {k: w[k] / s for k in P}


FORMULAS = {"1/(d^2+1) [v2.0]": lambda d: 1 / (d * d + 1), "1/(d^4+1e-6) [v2.1]": lambda d: 1 / (d ** 4 + 1e-6)}

if __name__ == "__main__":
    print("pairwise distances (m): K0-K1 %.3f  K1-K2 %.3f  K0-K2 %.3f" % (dist_m(K0, K1), dist_m(K1, K2), dist_m(K0, K2)))
    for name, wf in FORMULAS.items():
        print("==", name)
        samples = list(P.items()) + [("K0->K1 25%", lerp(K0, K1, .25)), ("K0->K1 50%", lerp(K0, K1, .5)), ("K0->K1 75%", lerp(K0, K1, .75)),
                                     ("K1->K2 25%", lerp(K1, K2, .25)), ("K1->K2 50%", lerp(K1, K2, .5)), ("K1->K2 75%", lerp(K1, K2, .75))]
        for pose, pos in samples:
            s = shares(pos, wf)
            print("  %-11s %s" % (pose, "  ".join("%s=%5.1f%%" % (k, s[k] * 100) for k in P)))
