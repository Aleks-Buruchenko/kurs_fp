from sync_server.schedule_data import resolve_publish_version


def test_resolve_publish_version_first_publish():
    assert resolve_publish_version(explicit=None, file_exists=False, current_version=0) == 1


def test_resolve_publish_version_increment():
    assert resolve_publish_version(explicit=None, file_exists=True, current_version=3) == 4


def test_resolve_publish_version_explicit():
    assert resolve_publish_version(explicit=10, file_exists=True, current_version=3) == 10
