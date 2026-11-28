"""Split Stage-1 triaged URLs into balanced Stage-2 batches for 2 browser agents."""

import argparse
import csv
from pathlib import Path

PROMPT_HEADER = """# Stage 2 Per-Page Inspection — {agent_label} ({mode_upper})

**Browser:** {browser_hint}
**Account:** {account_hint}
**Pacing Rule:** {pacing_rule}

Rules:
- Strictly ONE `chrome_devtools` tool call per turn.
- Stop immediately on any `429 / RESOURCE_EXHAUSTED` or login/rate-limit wall and report how far you got.
- Do NOT download videos or bypass any auth/CAPTCHA.

URLs assigned to this agent ({count} total):
"""


def load_candidates(csv_path: Path, min_score: int, tags: set[str]) -> list[dict]:
    """Load and filter rows from a triage CSV or 01_references.csv."""
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    out = []
    for r in rows:
        tag = (r.get("tag") or r.get("primary_category") or "").strip().upper()
        if tag == "SKIP" or (tags and tag not in tags):
            continue
        raw_score = (r.get("score") or r.get("fit") or r.get("priority_score") or "0").strip()
        try:
            score = float(raw_score)
        except ValueError:
            score = 0.0
        if score >= min_score:
            url = (r.get("instagram_url") or r.get("url") or "").strip()
            if url:
                out.append({
                    "url": url,
                    "tag": tag,
                    "score": raw_score,
                    "reason": (r.get("reason") or r.get("subject") or "").strip(),
                })
    return out


def format_prompt(items: list[dict], agent_label: str, browser_hint: str, account_hint: str, mode: str) -> str:
    """Render a copy-pasteable Stage 2 prompt for one agent."""
    pacing = (
        "Open 1 Instagram page at a time (~2s pause between navigations) to avoid account throttling."
        if mode == "instagram"
        else "Full speed (1 tool call per turn); read-only inspection, do NOT click Add to library / Buy."
    )
    lines = [PROMPT_HEADER.format(
        agent_label=agent_label,
        mode_upper=mode.upper(),
        browser_hint=browser_hint,
        account_hint=account_hint,
        pacing_rule=pacing,
        count=len(items),
    )]
    for i, item in enumerate(items, 1):
        lines.append(f"{i}. {item['url']} (`{item['tag']}` • Score {item['score']}) — {item['reason']}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Split Stage-1 triage CSV into 2 Stage-2 agent batches.")
    parser.add_argument("--input", type=Path, default=Path(__file__).parent / "triage_229.csv")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).parent / "stage2_batches")
    parser.add_argument("--min-score", type=int, default=3)
    parser.add_argument("--tags", type=str, default="LOOK,STAGING,FX,STORY")
    parser.add_argument("--mode", choices=["instagram", "fab"], default="instagram")
    parser.add_argument("--dry-run", action="store_true", help="Print split summary without writing files.")
    args = parser.parse_args()

    allowed_tags = {t.strip().upper() for t in args.tags.split(",") if t.strip()}
    items = load_candidates(args.input, args.min_score, allowed_tags)
    mid = (len(items) + 1) // 2
    batch1, batch2 = items[:mid], items[mid:]

    print(f"Input: {args.input} | Matched: {len(items)} (min_score>={args.min_score}, tags={sorted(allowed_tags)})")
    print(f"Split -> Agent 1: {len(batch1)} URLs | Agent 2: {len(batch2)} URLs")

    if args.dry_run:
        return

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for idx, (batch, browser, acct) in enumerate(
        [
            (batch1, "Chrome Profile 1 (port 9222)", "Google Pro Account #1"),
            (batch2, "Chrome Profile 2 (port 9223 via launch_browser2.ps1)", "Google Pro Account #2 (launch_gemini_agent2.ps1)"),
        ],
        start=1,
    ):
        (args.out_dir / f"stage2_agent{idx}_urls.txt").write_text(
            "\n".join(x["url"] for x in batch) + ("\n" if batch else ""), encoding="utf-8"
        )
        (args.out_dir / f"stage2_agent{idx}_prompt.md").write_text(
            format_prompt(batch, f"Agent {idx}", browser, acct, args.mode), encoding="utf-8"
        )
    print(f"Wrote Stage-2 batches to {args.out_dir}")


if __name__ == "__main__":
    main()
