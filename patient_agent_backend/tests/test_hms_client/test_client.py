import httpx
import pytest

from app.hms_client.client import HmsClient
from app.hms_client.exceptions import HmsTimeoutError


@pytest.mark.asyncio
async def test_request_retries_once_after_401(monkeypatch):
    client = HmsClient(base_url="http://test", timeout=1)
    responses = [
        httpx.Response(
            401,
            json={"code": 401, "msg": "token expired"},
            request=httpx.Request("POST", "http://test/patient/selectByPage"),
        ),
        httpx.Response(
            200,
            json={"code": 200, "result": {"items": []}},
            request=httpx.Request("POST", "http://test/patient/selectByPage"),
        ),
    ]
    login_calls = []

    async def fake_request(method, path, **kwargs):
        return responses.pop(0)

    async def fake_login_admin():
        login_calls.append("called")

    monkeypatch.setattr(client._http, "request", fake_request)
    monkeypatch.setattr(client, "login_admin", fake_login_admin)

    result = await client.post("/patient/selectByPage", json={"page": 1, "length": 20})

    assert result["code"] == 200
    assert login_calls == ["called"]


@pytest.mark.asyncio
async def test_request_raises_timeout_error(monkeypatch):
    client = HmsClient(base_url="http://test", timeout=1)

    async def raise_timeout(method, path, **kwargs):
        raise httpx.TimeoutException("boom")

    monkeypatch.setattr(client._http, "request", raise_timeout)

    with pytest.raises(HmsTimeoutError):
        await client.post("/patient/selectByPage", json={"page": 1, "length": 20})
