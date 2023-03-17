from orionutils.utils import increment_version


def test_increment_version():
    v1 = "1.1.1"
    v2 = increment_version(v1)
    assert v2 == "1.1.2"
