from unittest import mock

import pytest
from pyramid.config import Configurator

from bouncer.app import app


def test_the_default_settings(config, pyramid):
    app()

    pyramid.config.Configurator.assert_called_once_with(
        settings={
            "chrome_extension_id": "bjfhmglciegochdpefhhlphglcehbmek",
            "debug": False,
            "elasticsearch_index": "hypothesis",
            "hypothesis_authority": "localhost",
            "hypothesis_url": "https://hypothes.is",
            "via_base_url": "https://via.hypothes.is",
        }
    )


@pytest.mark.parametrize(
    "envvar,base_url",
    [
        # Trailing slashes should be stripped.
        ("https://via.example.com/", "https://via.example.com"),
        # A URL without a trailing slash should go through unmodified.
        ("http://via.example.com", "http://via.example.com"),
    ],
)
def test_via_base_url(config, os, envvar, base_url, pyramid):
    os.environ["VIA_BASE_URL"] = envvar

    app()

    settings = pyramid.config.Configurator.call_args_list[0][1]["settings"]
    assert settings["via_base_url"] == base_url


@pytest.fixture
def config():
    config = mock.create_autospec(Configurator, instance=True)
    config.registry = mock.Mock(spec_set=["settings"], settings={})
    return config


@pytest.fixture(autouse=True)
def os(patch):
    os = patch("bouncer.app.os")
    os.environ = {}
    return os


@pytest.fixture(autouse=True)
def pyramid(config, patch):
    pyramid = patch("bouncer.app.pyramid")
    pyramid.config.Configurator.return_value = config
    return pyramid
