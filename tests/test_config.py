from unittest.mock import patch

from PySide6.QtCore import QSettings

from audiodesk.config import Settings


def make_settings(tmp_path) -> QSettings:
    return QSettings(str(tmp_path / "test.ini"), QSettings.IniFormat)


def test_save_and_load_roundtrip_without_keyring(tmp_path):
    with patch("deskkit.secrets.available", return_value=False):
        settings = make_settings(tmp_path)
        cfg = Settings(discogs_token="abc123", lastfm_key="def456")
        cfg.save(settings)

        settings2 = make_settings(tmp_path)
        loaded = Settings.load(settings2)
    assert loaded.discogs_token == "abc123"
    assert loaded.lastfm_key == "def456"


def test_save_does_not_store_secrets_in_plaintext_when_keyring_available(tmp_path):
    with patch("deskkit.secrets.available", return_value=True), \
         patch("deskkit.secrets.keyring") as mock_keyring:
        settings = make_settings(tmp_path)
        cfg = Settings(discogs_token="abc123", lastfm_key="def456")
        cfg.save(settings)

    settings.beginGroup("audiodesk")
    stored_discogs = settings.value("discogs_token")
    stored_lastfm = settings.value("lastfm_key")
    settings.endGroup()
    assert stored_discogs is None
    assert stored_lastfm is None
    mock_keyring.set_password.assert_any_call("audiodesk", "discogs_token", "abc123")
    mock_keyring.set_password.assert_any_call("audiodesk", "lastfm_key", "def456")


def test_load_migrates_legacy_plaintext_keys_into_keyring(tmp_path):
    settings = make_settings(tmp_path)
    settings.beginGroup("audiodesk")
    settings.setValue("discogs_token", "legacy-token")
    settings.endGroup()

    with patch("deskkit.secrets.available", return_value=True), \
         patch("deskkit.secrets.keyring") as mock_keyring:
        mock_keyring.get_password.return_value = None
        loaded = Settings.load(settings)

    assert loaded.discogs_token == "legacy-token"
    mock_keyring.set_password.assert_any_call(
        "audiodesk", "discogs_token", "legacy-token")
