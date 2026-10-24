"""Generate a synthetic multi-model MD trajectory PDB for eval use:
two helices joined by a flexible linker that bends over the frames."""
import numpy as np


def helix(n, start_res, x0=0.0):
    s = np.arange(n)
    return np.column_stack([2.3 * np.cos(s * 3.4) + x0, 2.3 * np.sin(s * 3.4), 1.5 * s]), start_res + s


def main() -> None:
    h1, r1 = helix(18, 1)
    lk, rl = helix(6, 19)
    lk[:, 2] += h1[:, 2].max() + 1.5
    h2, r2 = helix(18, 25)
    h2[:, 2] += lk[:, 2].max() + 1.5

    base = np.vstack([h1, lk, h2])
    resn = np.array(["ALA"] * 18 + ["GLY"] * 6 + ["ALA"] * 18)
    frames = 40
    with open("md_traj.pdb", "w") as f:
        for k, t in enumerate(np.linspace(0, 1, frames)):
            bend = np.zeros_like(base)
            bend[:, 0] = 8 * t * np.sin(np.pi * np.arange(len(base)) / len(base))
            coords = base + bend
            f.write(f"MODEL     {k + 1}\n")
            for i, (x, y, z) in enumerate(coords):
                f.write(f"ATOM  {i + 1:5d}  CA  {resn[i]:>3s} A{r1[0] + i:4d}    "
                        f"{x:8.3f}{y:8.3f}{z:8.3f}  1.00  {60 + 30 * t:5.2f}           C\n")
            f.write("TER\nENDMDL\n")
    print(f"wrote md_traj.pdb ({frames} models, {len(base)} CA atoms/model)")


if __name__ == "__main__":
    main()
