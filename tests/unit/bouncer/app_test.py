import json
from unittest import mock

import pytest
from pyramid.config import Configurator

from bouncer.app import create_app


def test_the_default_settings(config, pyramid):
    create_app()

    pyramid.config.Configurator.assert_called_once_with(
        settings={
            "chrome_extension_id": {"default": "bjfhmglciegochdpefhhlphglcehbmek"},
            "debug": False,
            "elasticsearch_index": "hypothesis",
            "hypothesis_authority": "localhost",
            "hypothesis_url": "https://hypothes.is",
            "via_base_url": "https://via.hypothes.is",
        }
    )


@pytest.mark.parametrize(
    "envvar,extension_id",
    [
        ("abc", {"default": "abc"}),
        (
            json.dumps({"default": "abc", "bar.com": "def"}),
            {"default": "abc", "bar.com": "def"},
        ),
    ],
)
def test_chrome_extension_id(config, os, envvar, extension_id, pyramid):
    os.environ["CHROME_EXTENSION_ID"] = envvar

    create_app()

    settings = pyramid.config.Configurator.call_args_list[0][1]["settings"]
    assert settings["chrome_extension_id"] == extension_id


def test_raises_if_chrome_extension_id_invalid(config, os, pyramid):
    os.environ["CHROME_EXTENSION_ID"] = "{}"

    with pytest.raises(
        Exception, match='CHROME_EXTENSION_ID map must have a "default" key'
    ):
        create_app()


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

    create_app()

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
