"""Statistics and simple text charts (used by the CLI and the dashboard)."""

from collections import Counter
from datetime import datetime, timedelta


def text_bar_chart(data: dict, width: int = 30) -> str:
    """Draw a horizontal bar chart using plain characters."""
    if not data:
        return "(nothing to show yet)"
    biggest = max(data.values()) or 1
    label_width = max(len(str(k)) for k in data)
    lines = []
    for label, value in data.items():
        bar = "#" * max(1, round(value / biggest * width)) if value else ""
        lines.append(f"{str(label):<{label_width}} | {bar} {value}")
    return "\n".join(lines)


def notes_per_day(notes, days: int = 7) -> dict:
    """Count notes created on each of the last `days` days (oldest first)."""
    today = datetime.now().date()
    counts = Counter(n.created_at[:10] for n in notes)
    result = {}
    for offset in range(days - 1, -1, -1):
        day = (today - timedelta(days=offset)).isoformat()
        result[day] = counts.get(day, 0)
    return result


def summary(notes) -> dict:
    total_words = sum(len(n.content.split()) for n in notes)
    return {
        "total_notes": len(notes),
        "pinned_notes": sum(1 for n in notes if n.pinned),
        "unique_tags": len({t for n in notes for t in n.tags}),
        "total_words": total_words,
        "untagged_notes": sum(1 for n in notes if not n.tags),
    }
