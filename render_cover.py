#!/usr/bin/env python3
"""Render cover.html to cover.png at 1600x2240 with proper font loading.

Uses the system Chrome (not Playwright's bundled chromium-headless-shell)
because the bundled Chrome lacks access to system Chinese fonts (PingFang SC).
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
HTML = HERE / "cover.html"
OUT = HERE / "cover.png"
if len(sys.argv) > 1:
    OUT = Path(sys.argv[1])

with sync_playwright() as p:
    # Use system Chrome to access system fonts (PingFang SC for Chinese)
    browser = p.chromium.launch(channel="chrome")
    ctx = browser.new_context(viewport={"width": 1600, "height": 2240}, device_scale_factor=1)
    page = ctx.new_page()
    page.goto(f"file://{HTML.resolve()}")
    page.wait_for_load_state("networkidle")
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(800)
    page.locator(".cover").screenshot(path=str(OUT))
    browser.close()
print(f"wrote {OUT}")
