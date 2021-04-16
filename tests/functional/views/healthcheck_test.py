from unittest.mock import Mock

import pytest


class TestHealthcheck:
    def test_it(self, app):
        response = app.get("/_status", status=200)

        assert response.content_type == "application/json"
        assert response.json == {"status": "okay"}
        assert (
            response.headers["Cache-Control"]
            == "max-age=0, must-revalidate, no-cache, no-store"
        )

    @pytest.fixture(autouse=True)
    def Elasticsearch(self, patch):
        Elasticsearch = patch("bouncer.search.Elasticsearch")
        Elasticsearch.return_value.cluster = Mock()
        Elasticsearch.return_value.cluster.health.return_value = {"status": "green"}

        return Elasticsearch
