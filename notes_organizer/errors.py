"""Custom exceptions, so callers can catch app errors without hiding real bugs."""


class NotesError(Exception):
    """Base class for every error raised on purpose by this package."""


class ValidationError(NotesError):
    """User input did not pass validation."""


class NoteNotFoundError(NotesError):
    """No note exists with the requested id."""


class StorageError(NotesError):
    """The data file could not be read or written."""


class ImportExportError(NotesError):
    """An import or export file was unreadable or in the wrong format."""
