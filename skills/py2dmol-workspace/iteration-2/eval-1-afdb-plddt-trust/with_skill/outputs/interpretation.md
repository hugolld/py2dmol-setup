# Q5VSL9 (STRIP1) — AlphaFold confidence read-out

**Figure:** `q5vsl9_plddt_pae.png` — 2D Richardson-style cartoon colored by pLDDT (dark blue ≥90 → orange <50), PAE matrix alongside. Model: AF-Q5VSL9-F1 (AlphaFold DB v6), 837 residues, human Striatin-interacting protein 1 (STRIP1, STRIPAK complex core subunit).

## Verdict at a glance

| Region | pLDDT | PAE (internal / vs rest) | Read |
|---|---|---|---|
| 1–73 (N-tail) | ~43 | 21 Å / ~28 Å | Disordered |
| **74–318 (NTD)** | ~94 | 4 Å / well-placed | **Confidently folded domain** |
| 319–349 | ~72 | ~10 Å | Flexible linker |
| 350–442 (middle) | ~46 | 21 Å / 24–26 Å | Disordered insert |
| **443–742 (CTD)** | ~93 | 4–7 Å / well-placed | **Confidently folded solenoid** |
| 743–837 (C-tail) | ~76–80 | 7–9 Å internal / 18–24 Å vs CTD | Locally helical, positionally unplaced |

Overall: 79% of residues ≥70 pLDDT, 15% <50. Two large, confidently predicted globular regions separated by a long disordered insert.

## Trust these for structure work

- **74–318 — N-terminal domain.** Mean pLDDT 94, internal PAE ~4 Å across both halves (74–209 ↔ 210–318 mutual PAE 4.4 Å): one coherent, rigidly predicted fold, not two wobbling subdomains.
- **443–742 — C-terminal repeat/solenoid core.** Mean pLDDT ~93, internal PAE 4–7 Å; the figure shows it as the long blue superhelical body of the drawing. Minor dips (487–503, 531–546, 643–661, pLDDT 77–83) are inter-repeat loops, not domain uncertainty.
- Notably, NTD ↔ CTD relative placement is itself confident (PAE ~6 Å): the model predicts a defined arrangement of the two domains even though the segment between them is flexible.

## Treat as low-confidence / disordered

- **1–73 (N-terminus).** pLDDT ~43, no PAE signal (drawn as a drifting yellow/orange tail). UniProt independently annotates 1–67 as disordered.
- **350–442 (middle insert).** pLDDT ~46, PAE 24–26 Å to both neighbors — a ~90-residue flexible tether inside the chain (UniProt: disordered 333–423). This is the yellow band separating the two blue regions in the figure and the bright off-diagonal band in the PAE matrix.
- **743–837 (C-tail) — the interesting one.** Locally it looks helical and reasonably confident (pLDDT 76–80, internal PAE ~7–9 Å), but its *position relative to the rest of the protein* is uncertain (PAE ~18–24 Å; visible as the pale block in the bottom-right of the PAE panel). Classic signature of a segment folded only upon binding — and indeed UniProt annotates 796–837 as required for STRIPAK core complex formation. Expect it to be stabilized in complex with striatin/PP2A subunits.

## Experiment-design implications

- Constructs for crystallography/cryo-EM: **~70–320 (NTD)** and **~440–745 (CTD)**; truncating the disordered 1–73 and 333–442 segments should help crystallizability without touching confident structure.
- The 350–442 insert is a natural flexible linker but a poor candidate for structure determination on its own.
- For the 796–837 STRIPAK-recruitment motif, design binding assays (pull-down, ITC, crosslinking-MS) or attempt structure determination **in complex** with its STRIPAK partner rather than in isolation.
