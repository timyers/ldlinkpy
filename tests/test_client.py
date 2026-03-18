from __future__ import annotations

import threading

import pytest
import responses

from ldlinkpy.client import LDlinkClient
from ldlinkpy.exceptions import APIError


@responses.activate
def test_token_added_as_query_param() -> None:
    client = LDlinkClient(token="abc123", api_root="https://ldlink.nih.gov/LDlinkRest")

    url = "https://ldlink.nih.gov/LDlinkRest/ldproxy"
    responses.add(responses.GET, url, body="ok", status=200)

    out = client.get("ldproxy", params={"foo": "bar"})
    assert out == "ok"
    assert len(responses.calls) == 1

    called_url = responses.calls[0].request.url
    assert "token=abc123" in called_url
    assert "foo=bar" in called_url


@responses.activate
def test_non_200_raises_apierror_with_status_and_endpoint() -> None:
    client = LDlinkClient(token="t", api_root="https://ldlink.nih.gov/LDlinkRest")

    url = "https://ldlink.nih.gov/LDlinkRest/ldproxy"
    responses.add(responses.GET, url, body="bad request", status=400)

    with pytest.raises(APIError) as excinfo:
        client.get("ldproxy")

    msg = str(excinfo.value)
    assert "400" in msg
    assert "ldproxy" in msg


@responses.activate
def test_api_root_and_endpoint_combine_correctly_no_double_slashes() -> None:
    client = LDlinkClient(token="t", api_root="https://example.org/LDlinkRest/")

    url = "https://example.org/LDlinkRest/ldproxy"
    responses.add(responses.GET, url, body="ok", status=200)

    out = client.get("/ldproxy")
    assert out == "ok"
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url.startswith(url)


@responses.activate
def test_lock_exists_and_two_sequential_calls_recorded() -> None:
    client = LDlinkClient(token="t", api_root="https://example.org/LDlinkRest")

    assert hasattr(client, "_lock")
    assert isinstance(client._lock, type(threading.Lock()))

    url = "https://example.org/LDlinkRest/ldproxy"
    responses.add(responses.GET, url, body="first", status=200)
    responses.add(responses.GET, url, body="second", status=200)

    out1 = client.get("ldproxy")
    out2 = client.get("ldproxy")

    assert out1 == "first"
    assert out2 == "second"
    assert len(responses.calls) == 2
