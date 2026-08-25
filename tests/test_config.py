from pathlib import Path
import unittest

from nautilus_syncthing.config import discover
from nautilus_syncthing.ignore import is_ignored


class ConfigTests(unittest.TestCase):
    def test_environment_configuration(self):
        from unittest.mock import patch
        with patch.dict("os.environ", {"SYNCTHING_API_URL": "http://127.0.0.1:8384/", "SYNCTHING_API_KEY": "not-a-real-key"}, clear=False):
            settings = discover()
        self.assertEqual(settings.url, "http://127.0.0.1:8384")
        self.assertEqual(settings.api_key, "not-a-real-key")


    def test_ignore_patterns(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".stignore").write_text("*.part\n# comment\n")
            self.assertTrue(is_ignored(root, root / "movie.part"))
            self.assertFalse(is_ignored(root, root / "movie.mkv"))

    def test_current_state_directory_is_discovered(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        import os
        with TemporaryDirectory() as directory:
            config = Path(directory) / "syncthing" / "config.xml"
            config.parent.mkdir()
            config.write_text("<configuration><gui><address>127.0.0.1:8384</address><apikey>test-key</apikey></gui></configuration>")
            os.chmod(config, 0o600)
            with patch.dict("os.environ", {"XDG_STATE_HOME": directory}, clear=True):
                settings = discover()
            self.assertEqual(settings.url, "http://127.0.0.1:8384")
