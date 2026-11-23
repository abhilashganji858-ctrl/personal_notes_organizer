"""Shared test helper: a service that writes to a temporary folder."""

import tempfile
import unittest
from pathlib import Path

from notes_organizer.service import NoteService
from notes_organizer.storage import JsonStorage


class TempServiceTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "notes.json"
        self.svc = self.new_service()

    def new_service(self):
        return NoteService(JsonStorage(self.path))
