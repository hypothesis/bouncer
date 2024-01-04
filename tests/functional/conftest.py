import pytest
from webtest import TestApp

from bouncer.app import create_app


@pytest.fixture
def app():
    return TestApp(create_app())
