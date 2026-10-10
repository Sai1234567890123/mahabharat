# Report R-004: Canon QA Integration & Baseline Hero Frame Audit

**Task**: `T-004-canon-check-in-qa`  
**Owner**: Antigravity  
**Date**: 2026-10-10  
**Status**: Review  

---

## 1. Executive Summary

Canonical textual validation from `data/canon_checks.json` and the Ganguli translation of the *Bhishma Parva* (`B06-bhishma.txt`) has been successfully integrated into `scripts/paint_over.py`.

The QA evaluator (`gemini-3.8-flash`) now performs dual scoring:
1. **Style & Layout Score** (0–10 scale, layout fidelity, visible brushwork, lighting, color palette).
2. **Strict Canon Verification** (`canon.pass: bool`, `failed_must: []`, `found_must_not: []`).
   - If *any* `must` rule is unsatisfied or *any* `must_not` prohibited element is detected, the frame is marked `Canon: FAIL` regardless of its stylistic quality.

---

## 2. Automated Baseline Audit Results vs. R-003

Running `python scripts/paint_over.py --qa-only --shots SH010,SH050,SH070,SH090,SH130,SH150,SH170,SH180` verified the 8 hero frames. The automated evaluation agreed **100%** with the manual findings in Claude's Report `R-003`:

| Shot ID | Evaluated Version | Style Score | Canon Verdict | Automated Violations Detected (agrees with R-003) |
|---|---|---|---|---|
| **SH010** | `SH010_v02.png` | 3/10 | ❌ **FAIL** | • Arjuna drawing/firing bow before conches<br>• Ape banner on separate pole away from chariot<br>• Turbaned charioteer who is not Krishna |
| **SH050** | `SH050_v03.png` | 4/10 | ❌ **FAIL** | • Ape banner drawn as a cartoon monkey/chimp face<br>• Car body itself lacks internal fiery radiance |
| **SH070** | `SH070_v03.png` | 4/10 | ❌ **FAIL** | • War horn / trumpet on chariot (belongs to Kauravas)<br>• Flagstaff empty with missing ape banner |
| **SH090** | `SH090_v02.png` | 4/10 | ❌ **FAIL** | • Foreground Kaurava soldiers are faceless posts with no physical recoil or terror reaction |
| **SH130** | `SH130_v02.png` | 5/10 | ❌ **FAIL** | • Gandiva bow held upright rather than sliding out of limp hand toward car floor |
| **SH150** | `SH150_v02.png` | 4/10 | ❌ **FAIL** | • Garuda/Eagle emblem on Arjuna's flagstaff instead of ape<br>• Form rendered as 8-armed icon rather than boundless form of countless arms & faces |
| **SH170** | `SH170_v02.png` | 3/10 | ❌ **FAIL** | • **Krishna holding Gandiva** and Arjuna missing from frame |
| **SH180** | `SH180_v02.png` | 3/10 | ❌ **FAIL** | • Chariot/figure perched on top of flagstaff |

---

## 3. Implementation Details

- **Code Updates in `scripts/paint_over.py`**:
  - `load_b06_lines()` & `get_epic_snippet()`: Extracts precise line references cited in `canon_checks.json` from `B06-bhishma.txt`.
  - `build_prompt()`: Injects canonical `must` requirements as mandatory directives and `must_not` items into negative prompts.
  - `qa()`: Evaluates painted frames against 3D layout proxies AND the canonical text rules.
  - `--qa-only`: Standalone CLI mode to audit existing files without repainting.
- **Persistence**: Results are logged in `art/painted/qa.json` under each image entry with the complete `canon` inspection payload.

`T-004` is ready for review. Proceeding directly to **T-003** (generating new canonical takes for all 8 hero shots).
