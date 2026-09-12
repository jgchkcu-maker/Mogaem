from __future__ import annotations

from pathlib import Path

import httpx
import pytest


def test_webapp_menu_button_requires_https():
    from mogaem.configure_webapp import menu_button_for_url, validate_webapp_url

    url = validate_webapp_url("https://demo.trycloudflare.com")
    assert url == "https://demo.trycloudflare.com"
    button = menu_button_for_url(url)
    assert button.text == "⚔️ Mogaem"
    assert button.web_app.url == url

    with pytest.raises(ValueError):
        validate_webapp_url("http://example.com")
    with pytest.raises(ValueError):
        validate_webapp_url("not-a-url")


@pytest.mark.asyncio
async def test_fastapi_serves_built_spa_and_keeps_api_404(tmp_path):
    from mogaem.api import create_app
    from mogaem.config import Settings

    (tmp_path / "index.html").write_text("<html>miniapp-shell</html>", encoding="utf-8")
    app = create_app(settings=Settings(bot_token="123456:TEST"), dist_dir=tmp_path)
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        root = await client.get("/")
        assert root.status_code == 200
        assert "miniapp-shell" in root.text

        fallback = await client.get("/leaderboard")
        assert fallback.status_code == 200
        assert "miniapp-shell" in fallback.text

        missing_api = await client.get("/api/does-not-exist")
        assert missing_api.status_code == 404


def test_runtime_waits_for_quick_tunnel_dns_and_public_health():
    workflow = (Path(__file__).parents[1] / ".github" / "workflows" / "bot.yml").read_text(encoding="utf-8")

    assert 'curl --fail --retry 10 --retry-delay 2 "$PUBLIC_URL/health"' not in workflow
    assert 'for i in $(seq 1 90); do' in workflow
    assert 'curl --silent --show-error --fail --connect-timeout 5 --max-time 10 "$PUBLIC_URL/health"' in workflow
    assert 'Quick Tunnel URL did not become reachable in time' in workflow

    readiness_block = workflow.split("PUBLIC_READY=0", 1)[1].split("python -m mogaem.configure_webapp", 1)[0]
    assert 'kill -0 "$(cat .tunnel.pid)"' in readiness_block
    assert 'kill -0 "$(cat .api.pid)"' in readiness_block
    assert 'FastAPI process exited while waiting for the Quick Tunnel URL' in readiness_block
