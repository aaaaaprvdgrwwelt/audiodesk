from unittest.mock import patch

from PySide6.QtCore import QSettings

from audiodesk.config import Settings


def make_settings(tmp_path) -> QSettings:
    return QSettings(str(tmp_path / "test.ini"), QSettings.IniFormat)


def test_volume_defaults_to_80(tmp_path):
    settings = make_settings(tmp_path)
    loaded = Settings.load(settings)
    assert loaded.volume == 80


def test_volume_roundtrips_through_save_and_load(tmp_path):
    with patch("deskkit.secrets.available", return_value=False):
        settings = make_settings(tmp_path)
        cfg = Settings(volume=35)
        cfg.save(settings)

        settings2 = make_settings(tmp_path)
        loaded = Settings.load(settings2)
    assert loaded.volume == 35
