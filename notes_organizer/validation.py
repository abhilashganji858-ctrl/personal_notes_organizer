"""Input validation. Every note goes through here before it is saved."""

import re
from datetime import datetime

from .errors import ValidationError

MAX_TITLE = 100
MAX_CONTENT = 10_000
MAX_TAGS = 10
MAX_TAG_LENGTH = 30

# letters, digits, dash, underscore - no spaces so tags stay easy to type
TAG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
# strip control characters (except newline and tab) from free text
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_text(text: str) -> str:
    return _CONTROL_CHARS.sub("", text)


def validate_title(title) -> str:
    if not isinstance(title, str):
        raise ValidationError("Title must be text.")
    title = clean_text(title).strip()
    if not title:
        raise ValidationError("Title cannot be empty.")
    if "\n" in title:
        raise ValidationError("Title must be a single line.")
    if len(title) > MAX_TITLE:
        raise ValidationError(f"Title is too long (max {MAX_TITLE} characters).")
    return title


def validate_content(content) -> str:
    if content is None:
        return ""
    if not isinstance(content, str):
        raise ValidationError("Content must be text.")
    content = clean_text(content).strip()
    if len(content) > MAX_CONTENT:
        raise ValidationError(f"Content is too long (max {MAX_CONTENT} characters).")
    return content


def normalize_tag(tag: str) -> str:
    """Lowercase and trim a single tag, then check it."""
    if not isinstance(tag, str):
        raise ValidationError("Tags must be text.")
    tag = tag.strip().lstrip("#").lower()
    if not tag:
        raise ValidationError("Tag cannot be empty.")
    if len(tag) > MAX_TAG_LENGTH:
        raise ValidationError(f"Tag '{tag}' is too long (max {MAX_TAG_LENGTH} characters).")
    if not TAG_PATTERN.match(tag):
        raise ValidationError(
            f"Tag '{tag}' is invalid. Use letters, digits, '-' or '_' only."
        )
    return tag


def validate_tags(tags) -> list:
    """Accepts a list or a comma separated string. Returns unique, sorted tags."""
    if tags is None:
        return []
    if isinstance(tags, str):
        tags = tags.split(",")
    cleaned = {normalize_tag(t) for t in tags if str(t).strip()}
    if len(cleaned) > MAX_TAGS:
        raise ValidationError(f"Too many tags (max {MAX_TAGS}).")
    return sorted(cleaned)


def validate_date(text: str) -> str:
    """Check a YYYY-MM-DD date string used for date filtering."""
    try:
        datetime.strptime(text, "%Y-%m-%d")
    except (ValueError, TypeError):
        raise ValidationError(f"'{text}' is not a valid date. Use YYYY-MM-DD.") from None
    return text
