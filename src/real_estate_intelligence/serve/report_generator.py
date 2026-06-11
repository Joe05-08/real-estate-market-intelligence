from pathlib import Path


def generate_report(insights: list[dict], output_path: str | Path) -> None:
    output_path = Path(output_path)
    lines = [
        "# Real Estate Market Intelligence Report",
        "",
        "This report summarizes the strongest market signals found in the current listing dataset.",
        "",
    ]

    for index, insight in enumerate(insights, start=1):
        lines.extend(
            [
                f"## {index}. {insight['title']}",
                "",
                f"**Type:** {insight['insight_type']}",
                "",
                f"**Summary:** {insight['summary']}",
                "",
                f"**Recommendation:** {insight['recommendation']}",
                "",
                f"**Confidence:** {int(insight['confidence_score'] * 100)}%",
                "",
            ]
        )

    output_path.write_text("\n".join(lines), encoding="utf-8")
