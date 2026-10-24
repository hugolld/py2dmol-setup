# Q5VSL9 (human STRIP1) — AlphaFold confidence assessment

**Deliverable:** `q5vsl9_plddt_pae.png` — 2D Richardson-style cartoon (py2Dmol) colored by
pLDDT with the PAE matrix alongside, 4200×3000 transparent PNG (page capture at device
scale 3; the 700-px structure panel renders at 2100×2100 px ≈ the dpi-300 export class).
Re-exportable artifact: `q5vsl9_plddt_pae_viewer.html` (self-contained; re-run
`export.py` on it for other sizes/formats).

**Data:** AlphaFold DB model + PAE (v6) for Q5VSL9 — Striatin-interacting protein 1
(STRIP1 / FAM40A), 837 residues. All numbers below were extracted from the exact
pLDDT/PAE arrays embedded in the rendered figure (PAE stored by py2Dmol in 1/8 Å units;
verified identical to the official AF-Q5VSL9-F1-pae JSON).

Palette reminder: dark blue ≥90 · light blue 70–90 · yellow 50–70 · orange <50.

## Headline

The model is a two-disordered-tapestry sandwiching a large, very confident α-helical
core: **57% of residues have pLDDT ≥90 and 79% ≥70**, while two long internal segments
(1–66 and 335–421) are frankly disordered (pLDDT ≈ 38). UniProt independently annotates
1–67 and 333–423 as disordered regions — the pLDDT/PAE picture matches the curated
annotation exactly.

## Segment table (residue numbers are UniProt 1–837)

| Region | Residues | pLDDT (mean) | Intra-region PAE | Verdict |
|---|---|---|---|---|
| N-terminal tail | 1–66 | 38 | ~25 Å | Disordered |
| **Core I** | **71–320** | **94** | **4.3 Å** | Confidently folded, rigid |
| Internal insert | 335–421 | 38 | ~24 Å | Disordered |
| Core II | 426–540 | 88 | 7.6 Å | Folded, moderately confident |
| **Core III** | **545–645** | **95** | **3.8 Å** | Confidently folded, rigid |
| **Core IV** | **650–750** | **92** | **4.5 Å** | Confidently folded, rigid |
| C-terminal region | 751–837 | 78 | ~18 Å | Partly ordered; see note |

Inter-region PAE (Å, from the displayed matrix): cores I–III 4.3 · I–IV 6.9 · III–IV 5.1
→ cores I + III + IV are mutually well anchored and behave as **one rigid superdomain**.
Core II is internally folded but only semi-rigidly attached (10.2 Å to core I). The
N-tail, the 335–421 insert, and the far C-terminus show 17–28 Å PAE against everything —
they are flexibly tethered.

## Confidently folded — trust these

- **71–320 (Core I, ~250 res):** pLDDT 94, intra-PAE 4.3 Å, ~65% helical. Best part of
  the model — reliable for structure-guided design, epitope/mutagenesis choices.
- **545–645 (Core III):** pLDDT 95, intra-PAE 3.8 Å, ~68% helical — the most confident
  segment in the protein.
- **650–750 (Core IV):** pLDDT 92, intra-PAE 4.5 Å, ~62% helical.
- **426–540 (Core II):** pLDDT 88, intra-PAE 7.6 Å — folded (sub-segments 432–445,
  458–488, 502–533 all ≥90) but its position relative to Core I is less certain
  (inter-PAE ~10 Å); treat the internal fold as trustworthy, the inter-domain geometry
  as indicative.
- 761–780 (within the C-region): locally pLDDT ~89 — a small reliable element.

## Low confidence / disordered — do not rely on the modeled conformation

- **1–66 (N-tail):** pLDDT 38, 86% of residues <50, PAE ~25 Å to the rest. Classic
  intrinsically disordered tail. UniProt: "Region 1–67 Disordered".
- **335–421 (internal insert):** pLDDT 38, 79% <50, PAE ~24 Å to the rest — an 87-residue
  flexible linker separating Core I from Core II. UniProt: "Region 333–423 Disordered".
  In the figure this segment renders as the long orange appendage.
- **784–837 (far C-terminus):** pLDDT drops to ~62–79 with intra-PAE ~18 Å — partially
  ordered/extended, not a reliable folded unit. Note 796–837 is UniProt-annotated
  "Required for STRIPAK core complex formation": likely a binding motif that folds upon
  binding its partner — keep it in binding assays, but don't trust its isolated
  conformation (or use it for structure-based design without the partner).

## Reading the PAE matrix in the figure

Dark (low-error) squares along the diagonal at ~70–320 and ~545–750 = the rigid cores;
bright red bands off the diagonal wherever the disordered tail/insert or the C-terminal
region face the rest of the protein = no fixed relative orientation. The single dark
block spanning Cores I/III/IV (inter-PAE 4–7 Å) is the visual signature of the rigid
superdomain described above.

## Practical suggestions for experiment design

- Crystallization / cryo-EM constructs: start from **71–320** alone (self-contained,
  rigid), or the **71–320 + 426–750** supercore with the 335–421 insert deleted (expect
  the Core II placement to breathe); delete 1–66 and 784–837 for particle-size discipline.
- Avoid epitopes/labels in 1–66 and 335–421 (flexible, poor immunogens/anchors, will
  smear class averages).
- For STRIPAK assembly work, constructs must retain 796–837 despite its low pLDDT —
  disorder in isolation is expected for a binding motif, not evidence of unimportance.

## Reproducibility

Render: `render.py --afdb Q5VSL9 --color plddt --pae --size 700 700 -o viewer.html`;
export: `export.py viewer_clean.html -o q5vsl9_plddt_pae.png --page --scale 3` (page mode
includes the PAE panel; interactive toolbar hidden via injected CSS in the scratch copy
only — see commands.log). Full command history: `commands.log`.
