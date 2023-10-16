import pytest


@pytest.mark.django_db(databases=['default'])
def test_setup():
    assert 1 == 1
