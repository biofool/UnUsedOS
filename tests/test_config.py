from unusedos.config import Settings


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("UNUSEDOS_ANONYMIZE", "true")
    monkeypatch.setenv("UNUSEDOS_ANONYMIZE_SEGMENTS", "foo,bar")
    monkeypatch.setenv("UNUSEDOS_PROTECTED_PACKAGES", "pkg-a,pkg-b")
    monkeypatch.setattr("unusedos.config.load_dotenv", lambda *args, **kwargs: True)
    settings = Settings.from_env()
    assert settings.anonymize is True
    assert settings.anonymize_segments == ["foo", "bar"]
    assert settings.protected_packages == ["pkg-a", "pkg-b"]


def test_settings_defaults():
    settings = Settings()
    assert settings.anonymize is False
    assert settings.filesystem == "ext4"
    assert "base-files" in settings.protected_packages
