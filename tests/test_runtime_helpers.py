from __future__ import annotations

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
