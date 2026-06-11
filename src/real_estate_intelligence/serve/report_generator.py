from pathlib import Path


def generate_report(insights: list[dict], output_path: str | Path, ai_brief: dict | None = None) -> None:
    output_path = Path(output_path)
    lines = [
        "# Real Estate Market Intelligence Report",
        "",
        "This report summarizes the strongest market signals found in the current listing dataset.",
        "",
    ]

    if ai_brief:
        lines.extend(
            [
                "## AI Market Brief",
                "",
                ai_brief["executive_summary"],
                "",
                "### Persona Recommendations",
                "",
            ]
        )
        for recommendation in ai_brief["persona_recommendations"]:
            lines.extend(
                [
                    f"**{recommendation['persona']}:** {recommendation['headline']}",
                    "",
                    f"- Reasoning: {recommendation['reasoning']}",
                    f"- Next step: {recommendation['next_step']}",
                    "",
                ]
            )

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
