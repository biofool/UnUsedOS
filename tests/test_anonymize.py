from unusedos.anonymize import Anonymizer


def test_anonymize_disabled_returns_original():
    anon = Anonymizer(enabled=False, segments=("vigilent",))
    assert anon.anonymize_path("/customer/vigilent/app") == "/customer/vigilent/app"


def test_anonymize_replaces_configured_segments():
    anon = Anonymizer(enabled=True, path_replacement="/redacted", segments=("vigilent",))
    assert anon.anonymize_path("/disk/data/vigilent/app") == "/disk/data/redacted/app"
