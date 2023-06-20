from yanga.core.subprocess import get_app_path


def test_get_app_path():
    assert get_app_path("python")
