from app import tools


def test_is_empty_with_empty_list():
    assert tools.is_empty([]) is True
