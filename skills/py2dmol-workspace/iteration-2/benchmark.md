# Skill Benchmark: py2dmol

**Model**: glm-5.3 (session default; 8 concurrent subagents)
**Date**: 2026-08-17T16:18:23Z
**Evals**: 0, 1, 2, 3 (1 runs each per configuration)

## Summary

| Metric | Old Skill | With Skill | Delta |
|--------|------------|---------------|-------|
| Pass Rate | 92% ± 16% | 100% ± 0% | -0.08 |
| Time | 453.6s ± 23.2s | 432.7s ± 66.4s | +20.8s |
| Tokens | 0 ± 0 | 0 ± 0 | +0 |

## Notes

- Columns are ordered old_skill | with_skill (alphabetical); Delta = old - with, so -0.08 pass rate means the new skill is +8.2 points (100% vs 91.8%).
- Both old-skill failures are in eval-1: its PNG (2181x2181, ratio 1.00) contains no PAE panel at all - saveImage exports only the structure canvas, and only the new skill documents the --page path. The sole capability-differentiated eval; every other eval passed for both configs.
- Pass rates understate the gap: old-skill runners compensated manually wherever the snapshot lacked a feature - eval-2 hand-injected JS (renderer.animationSpeed=185) after --seconds 8 yielded 4.66s, eval-3 hand-authored a spec.json because no styling flags existed, eval-0 hand-picked style/color flags because no default path existed. New-skill runners used --speed, one-line shorthand flags, and zero-flag defaults respectively.
- Timing is mtime-derived (first->last artifact) under 8-way concurrent execution: indicative only. The one clean contrast is eval-2: 336s (new, --speed) vs 421s (old, JS injection). Token counts were not captured this round (executor completions arrived without usage stats).
- Grader critique accepted: eval-0's 'default applied' and eval-3's config-echo assertions are outcome-level and don't discriminate versions (a competent runner pins flags by hand). A future eval could grade commands.log for a bare invocation. Strength of this round's evals: eval-1's --page dependency and eval-2's 6-12s duration band.
- New skill gaps surfaced by runners (queued for next revision): no documented way to export a still of a specific trajectory frame (both e2 runners extracted MODEL N to a separate PDB; renderer.setFrame(i) suggests an export.py --frame N); 'file is multi-MB at 300 dpi' verification heuristic is wrong for tube renders and single-chain monomers (0.45-1.06 MB observed).
- Verified this round: PyPI has no py2Dmol 1.7.0 (latest 1.6.5, 2026-05-06) - iteration-1's '1.7.0 trap' claim was wrong; references corrected to state the verified situation.