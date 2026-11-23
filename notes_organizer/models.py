"""The Note data model."""

from dataclasses import dataclass, field, asdict
from datetime import datetime

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def now_string() -> str:
    """Current local time in the format we store in the file."""
    return datetime.now().strftime(TIME_FORMAT)


@dataclass
class Note:
    id: int
    title: str
    content: str
    tags: list = field(default_factory=list)
    pinned: bool = False
    created_at: str = field(default_factory=now_string)
    updated_at: str = field(default_factory=now_string)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Note":
        return cls(
            id=int(data["id"]),
            title=data["title"],
            content=data.get("content", ""),
            tags=list(data.get("tags", [])),
            pinned=bool(data.get("pinned", False)),
            created_at=data.get("created_at") or now_string(),
            updated_at=data.get("updated_at") or now_string(),
        )

    def preview(self, length: int = 60) -> str:
        """One-line preview of the content, used in lists."""
        flat = " ".join(self.content.split())
        return flat if len(flat) <= length else flat[: length - 3] + "..."
