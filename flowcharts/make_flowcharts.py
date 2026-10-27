"""
Module:   make_flowcharts
Project:  Aircraft Performance Engine
Author:   M. Barsoum

Purpose:
    Exports the charts in flowcharts.html to calculation_flow.png,
    program_flow.png and flowcharts.pdf. flowcharts.html is the source.

Run:
    pip install playwright pillow
    python -m playwright install chromium
    python flowcharts/make_flowcharts.py
"""

import os

from PIL import Image
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE_HTML = os.path.join(HERE, "flowcharts.html")

# chart key in flowcharts.html -> (output name, viewport width px, viewport height px)
CHARTS = {
    "calculation": ("calculation_flow", 1300, 2150),
    "program":     ("program_flow",     2300, 1300),
}
HIDE_UI_CSS = "header, aside, .zoom, .legend .ttl button { display: none !important; }"


def export_png(page, chart_key, out_name, width_px, height_px):
    """Render one chart without the toolbar and side panel, and save it as a PNG."""
    page.set_viewport_size({"width": width_px, "height": height_px})
    page.goto(f"file://{SOURCE_HTML}#{chart_key}")
    page.wait_for_timeout(800)
    page.add_style_tag(content=HIDE_UI_CSS)
    page.evaluate("window.dispatchEvent(new Event('resize'))")     # re-fit to the full window
    page.wait_for_timeout(300)
    path = os.path.join(HERE, out_name + ".png")
    page.screenshot(path=path)
    return path


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(device_scale_factor=2)
        png_paths = [export_png(page, key, *spec) for key, spec in CHARTS.items()]
        browser.close()

    images = [Image.open(p).convert("RGB") for p in png_paths]
    pdf_path = os.path.join(HERE, "flowcharts.pdf")
    images[0].save(pdf_path, save_all=True, append_images=images[1:], resolution=200)

    for p in png_paths + [pdf_path]:
        print(f"  Saved: {os.path.relpath(p, os.path.dirname(HERE))}")


if __name__ == "__main__":
    main()
