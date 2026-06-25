from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Browser, BrowserContext, Page, Playwright

DEFAULT_VIEWPORT_WIDTH = 1280
DEFAULT_VIEWPORT_HEIGHT = 900
DEFAULT_ACTION_WAIT_MS = 300


@dataclass(frozen=True)
class ObservationFrame:
    step: int
    image_path: Path
    url: str
    viewport_width: int
    viewport_height: int


class BrowserAdapterError(RuntimeError):
    """Raised when browser automation fails."""


class BrowserPlatformAdapter:
    """Shared browser adapter for figma and web targets."""

    def __init__(
        self,
        *,
        viewport_width: int = DEFAULT_VIEWPORT_WIDTH,
        viewport_height: int = DEFAULT_VIEWPORT_HEIGHT,
        navigation_timeout_ms: int = 30_000,
    ) -> None:
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.navigation_timeout_ms = navigation_timeout_ms
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._cursor_x = viewport_width // 2
        self._cursor_y = viewport_height // 2

    @property
    def cursor_position(self) -> dict[str, int]:
        return {"x": self._cursor_x, "y": self._cursor_y}

    def move_to(self, x: int, y: int) -> None:
        self.page.mouse.move(x, y)
        self._cursor_x = x
        self._cursor_y = y

    def move_by_delta(self, delta_x: int, delta_y: int) -> None:
        self.move_to(self._cursor_x + delta_x, self._cursor_y + delta_y)

    def click(self, x: int, y: int) -> None:
        self.move_to(x, y)
        self.page.mouse.click(x, y)

    def click_current(self) -> None:
        self.page.mouse.click(self._cursor_x, self._cursor_y)

    def scroll(self, delta_y: int) -> None:
        self.page.mouse.wheel(0, delta_y)

    def wait(self, wait_ms: int) -> None:
        time.sleep(max(wait_ms, 0) / 1000)

    def type_text(self, text: str) -> None:
        self.page.keyboard.type(text)

    def pause_for_feedback(self, wait_ms: int = DEFAULT_ACTION_WAIT_MS) -> None:
        self.wait(wait_ms)

    def __enter__(self) -> BrowserPlatformAdapter:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise BrowserAdapterError(
                "Playwright is not installed. Run: pip install -r requirements.txt "
                "&& playwright install chromium"
            ) from exc

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)
        self._context = self._browser.new_context(
            viewport={
                "width": self.viewport_width,
                "height": self.viewport_height,
            }
        )
        self._page = self._context.new_page()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._context is not None:
            self._context.close()
        if self._browser is not None:
            self._browser.close()
        if self._playwright is not None:
            self._playwright.stop()
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None

    @property
    def page(self) -> Page:
        if self._page is None:
            raise BrowserAdapterError("Browser adapter is not open")
        return self._page

    def open(self, url: str, *, target: str) -> None:
        wait_until = "networkidle" if target == "figma" else "domcontentloaded"
        try:
            self.page.goto(
                url,
                wait_until=wait_until,
                timeout=self.navigation_timeout_ms,
            )
        except Exception as exc:
            raise BrowserAdapterError(f"Failed to open {url}: {exc}") from exc

    def capture_frame(self, *, step: int, output_dir: Path) -> ObservationFrame:
        screenshots_dir = output_dir / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        image_path = screenshots_dir / f"step-{step:03d}.png"
        try:
            self.page.screenshot(path=str(image_path), full_page=False)
        except Exception as exc:
            raise BrowserAdapterError(f"Failed to capture screenshot: {exc}") from exc

        return ObservationFrame(
            step=step,
            image_path=image_path,
            url=self.page.url,
            viewport_width=self.viewport_width,
            viewport_height=self.viewport_height,
        )


def run_initial_capture(
    *,
    target: str,
    url: str,
    output_dir: Path,
    timeout_seconds: int,
) -> ObservationFrame:
    """Open the target URL and capture the first observation frame."""
    output_dir.mkdir(parents=True, exist_ok=True)
    navigation_timeout_ms = max(timeout_seconds, 1) * 1000

    with BrowserPlatformAdapter(navigation_timeout_ms=navigation_timeout_ms) as adapter:
        adapter.open(url, target=target)
        return adapter.capture_frame(step=0, output_dir=output_dir)
