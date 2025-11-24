import my_codex_utils.sessions as sessions


def test_iso_to_local_none():
    assert sessions.iso_to_local(None) == "?"
