# AF-Q5VSL9 confidence assessment — 2D cartoon (pLDDT) + PAE matrix

**Protein:** STRIP1 (Striatin-interacting protein 1), *Homo sapiens*, 837 aa —
core scaffold subunit of the STRIPAK phosphatase/kinase complex.
**Model:** AlphaFold DB AF-Q5VSL9-F1 (v6 CIF, B-factor = pLDDT; PAE from the
EBI `predicted_aligned_error` JSON).

**Figure:** `Q5VSL9_plddt_pae_300dpi.png` (3775×1869 px). Left: py2Dmol
Richardson-style 2D cartoon colored by pLDDT (colorbar 0–100). Right: PAE
matrix (colorbar 0–30 Å). Structure panel is the native py2Dmol
`saveImage(dpi=300)` export (transparent background); PAE panel re-rendered
at 600×600 native and scaled to match panel height.

## Global stats

| pLDDT band | fraction |
|---|---|
| ≥ 90 (very high) | 56.5 % |
| 70–90 (confident) | 22.0 % |
| 50–70 (low) | 6.2 % |
| < 50 (very low) | 15.3 % |

Mean pLDDT 80.9, median 91.8 → a mostly well-folded protein with two large
disordered insertions.

## Confidently folded regions (trust for construct design / mutagenesis)

- **~73–318 ("domain A")** — mean pLDDT ≈ 94–96 through this stretch, intra-region mean PAE **4.0 Å**. Begins immediately after the disordered N-terminus.
- **~422–785 ("domain B")** — mean pLDDT ≈ 90–95 (small dips at 487–502, 643–660, 744–767), intra-region mean PAE **6.4 Å**. Drawn as a large repeat/helical stack in the cartoon.
- **A and B behave as ONE rigid superdomain**: inter-region mean PAE between 73–318 and 422–785 is only **6.3 Å** — AlphaFold predicts a fixed inter-domain register despite the long internal insertion between them. Docking/orientation conclusions within 73–785 are supported.
- Short reliable extensions: 196–209 and 239–260 sit at ~87–92; 319–335 (~82) likely closes domain A; 422–443 (~89) starts domain B.

## Low-confidence / disordered segments

- **1–72 (N-terminal IDR)** — mean pLDDT ≈ 42, PAE vs everything 28–30 Å. UniProt annotates 1–67 as *Disordered*; Pro-rich (18–35), low-complexity (36–46), mixed charged (47–60) bias. Classic flexible tail.
- **~336–421 (internal IDR)** — mean pLDDT ≈ 33 (core 351–421); UniProt: *Disordered 333–423*, basic/acidic (356–377) and acidic (378–391) biases. PAE to all other regions 20–29 Å → a flexible tether threading through the superdomain, not a fixed element.
- **786–837 (C-terminus)** — nuanced: 786–796 dips (~58), and 797–837 is only moderate (~76 pLDDT; intra-PAE 10.1 Å) with **high PAE relative to the core (19.6–20 Å)**. UniProt marks 796–837 *"Required for STRIPAK core complex formation"* — consistent with a striatin-binding helix that folds on binding. In the experimental STRIPAK cryo-EM structure (PDB 7K36), STRIP1 (chain I) is resolved from ~residue 69 onward (construct numbering; isoform differs slightly) and its C-terminal region contacts striatin-3. Do not truncate it, and do not trust its isolated predicted conformation.

## Bottom line for experiments

1. **Trust:** the rigid core 73–785 — good target for crystallization/EM constructs and for interpreting point-mutant structural effects; the A/B interface geometry is reliable (PAE ≈ 6 Å).
2. **Treat as disordered:** 1–72 and 336–421 — removable in constructs or usable as flexible linker/tag sites; expect proteolysis and heterogeneity.
3. **Handle with care:** 786–837 — functionally essential (STRIPAK assembly), only moderately confident alone; design assays around its binding to striatin rather than its apo conformation.
4. **Don't over-interpret:** positioning of the N-terminal IDR or the C-terminal element relative to the core (PAE ~20–30 Å).

*Numbers computed from the raw CIF B-factors and PAE JSON (smoothing window 7
residues; minimal segment length 10). Region boundaries are approximate to
±5 residues.*
