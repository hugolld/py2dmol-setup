# Q5VSL9 — AlphaFold confidence interpretation

**Figure:** `q5vsl9_plddt_pae.png` (300 dpi, transparent background) — Jane-Richardson-style
2D cartoon colored by pLDDT (dark blue ≥90, light blue 70–90, yellow 50–70, orange <50)
with the predicted aligned error (PAE) matrix alongside. Data: AlphaFold DB model
`AF-Q5VSL9-F1` (837 residues, chain A; mean pLDDT 80.9; 79% of residues ≥70).

## Confidently folded regions

| Region | Length | Mean pLDDT | Internal PAE | Notes |
|---|---|---|---|---|
| **66–335** | 270 res | ~95 (nearly all ≥90) | ~5 Å | Main folded domain; helical core, only short surface loops drop into the 70–90 band (196–207, 320–335) |
| **421–535** | 115 res | ~90 (445–532 ≥90) | ~6 Å | Second lobe; short 50–70 dip at 493–500 |
| **541–784** | 244 res | ~94 | ~5 Å | Third lobe; flexible-ish patches at 643–659 (70–90) and 745–767 (70–90) |

Critically, the **inter-lobe PAE values are low**: core 66–335 vs 421–535 ≈ 8–10 Å, vs
541–784 ≈ 6–7 Å, and 421–535 vs 541–784 ≈ 7–8 Å. The three confident segments therefore
form **one rigid, well-defined assembly** — their relative arrangement is trusted, not just
their individual backbones. In the figure this reads as the compact blue core with a dark
PAE block in the upper-left of the matrix.

## Low-confidence / likely disordered segments

| Region | Length | pLDDT | PAE vs rest | Notes |
|---|---|---|---|---|
| **1–65** (N-terminus) | 65 res | <50 (mean ~35) | 19–31 Å | Classic disordered tail — no fixed position relative to the core; visible as the long orange strand snaking away from the core in the cartoon |
| **336–420** (internal insert) | 85 res | <50 (mean ~32) | 28–30 Å | Disordered loop/string between lobes 1 and 2; the bright off-diagonal bands in the PAE matrix |
| **536–540** | 5 res | ~48–67 | — | Short flexible linker between lobes 2 and 3 |
| **785–796** | 12 res | ~55–59 | — | Local dip at the start of the C-terminal segment |
| **797–837** (C-terminus) | 41 res | 70–90 (mean ~79) | **19–26 Å vs core** | Ambiguous: locally somewhat ordered but its position relative to the core is poorly determined (bright rows/columns in PAE). Treat as weakly packed / possibly induced upon binding, not a trusted placement |

## Practical take for experiment design

- **Best crystallization/EM construct candidates:** the rigid core is **~66–335** alone, or
  the multi-domain assembly **66–335 + 421–784** if inter-domain contacts are of interest
  (their arrangement is confident). For the full assembly, remove the floppy internal insert
  **336–420** (e.g., 66–335 fused via a short linker to 421–784) — 85 residues of disorder
  will hurt crystal packing and smear cryo-EM class averages.
- **Trim for stability:** delete the N-terminal tail **1–65** and consider ending constructs
  near **~830**; residues 785–837 add positional noise.
- **Don't over-interpret:** any interface involving regions 1–65, 336–420, or 797–837 in
  this model is unreliable — the cartoon places them in one arbitrary conformation.
- Antibody/design work targeting the confident surface should focus on 66–335 and 541–784
  (the largest ≥90 stretches).

*Numbers computed directly from the AlphaFold DB model (pLDDT = CIF B-factor column; PAE
from the `predicted_aligned_error` scores file), not estimated from the figure. Cached
source files: `AF-Q5VSL9.cif`, `AF-Q5VSL9-pae.json`. PAE block means (Å):*

|  | N-dis | core1 | ins | core2a | core2b | C-tail |
|---|---|---|---|---|---|---|
| **N-dis 1–65** | 19.2 | 30.2 | 28.3 | 30.3 | 29.3 | 30.6 |
| **core1 66–335** | 25.0 | 4.9 | 23.0 | 7.8 | 6.2 | 20.0 |
| **ins 336–420** | 28.5 | 29.4 | 20.1 | 28.6 | 28.1 | 30.5 |
| **core2a 421–535** | 25.9 | 9.8 | 22.4 | 6.1 | 8.0 | 18.5 |
| **core2b 541–784** | 25.0 | 6.5 | 21.9 | 6.8 | 5.1 | 19.6 |
| **C-tail 785–837** | 29.4 | 27.3 | 29.2 | 23.7 | 26.4 | 10.4 |
