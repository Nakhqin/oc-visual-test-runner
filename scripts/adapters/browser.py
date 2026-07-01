from __future__ import annotations

import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Browser, BrowserContext, Page, Playwright, Video

DEFAULT_VIEWPORT_WIDTH = 1280
DEFAULT_VIEWPORT_HEIGHT = 900
DEFAULT_ACTION_WAIT_MS = 300
FIGMA_POST_LOAD_WAIT_MS = 3000
RECORDING_FILENAME = "ux_test_recording.webm"
CURSOR_MARKER_ELEMENT_ID = "oc-visual-test-runner-cursor"
CURSOR_MARKER_PAINT_MS = 50


@dataclass(frozen=True)
class ObservationFrame:
    step: int
    image_path: Path
    url: str
    viewport_width: int
    viewport_height: int
    cursor_x: int
    cursor_y: int
    phase: str = "observe"


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
        record_video_path: Path | None = None,
    ) -> None:
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.navigation_timeout_ms = navigation_timeout_ms
        self._record_video_path = record_video_path
        self._record_video_dir: Path | None = None
        self._finalized_recording_path: Path | None = None
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

    def show_cursor_marker(self) -> None:
        """Overlay a visible pointer marker for VLM observation frames."""
        x, y = self._cursor_x, self._cursor_y
        marker_id = CURSOR_MARKER_ELEMENT_ID
        script = """
            ({ markerId, x, y }) => {
                const size = 24;
                let el = document.getElementById(markerId);
                if (!el) {
                    el = document.createElement("div");
                    el.id = markerId;
                    el.setAttribute("data-oc-visual-test-runner", "cursor-marker");
                    el.style.position = "fixed";
                    el.style.width = size + "px";
                    el.style.height = size + "px";
                    el.style.marginLeft = (-size / 2) + "px";
                    el.style.marginTop = (-size / 2) + "px";
                    el.style.border = "2px solid #E53935";
                    el.style.borderRadius = "50%";
                    el.style.background = "rgba(229, 57, 53, 0.28)";
                    el.style.pointerEvents = "none";
                    el.style.zIndex = "2147483647";
                    el.style.boxShadow = "0 0 0 1px rgba(255,255,255,0.85)";
                    document.documentElement.appendChild(el);
                }
                el.style.left = x + "px";
                el.style.top = y + "px";
                el.style.display = "block";
            }
        """
        self.page.evaluate(script, {"markerId": marker_id, "x": x, "y": y})
        self.wait(CURSOR_MARKER_PAINT_MS)

    def hide_cursor_marker(self) -> None:
        marker_id = CURSOR_MARKER_ELEMENT_ID
        self.page.evaluate(
            """
            (markerId) => {
                const el = document.getElementById(markerId);
                if (el) {
                    el.style.display = "none";
                }
            }
            """,
            marker_id,
        )

    @property
    def recording_path(self) -> Path | None:
        return self._finalized_recording_path

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
        context_kwargs: dict = {
            "viewport": {
                "width": self.viewport_width,
                "height": self.viewport_height,
            }
        }
        if self._record_video_path is not None:
            self._record_video_dir = self._record_video_path.parent / ".playwright-video"
            self._record_video_dir.mkdir(parents=True, exist_ok=True)
            context_kwargs["record_video_dir"] = str(self._record_video_dir)
            context_kwargs["record_video_size"] = {
                "width": self.viewport_width,
                "height": self.viewport_height,
            }
        self._context = self._browser.new_context(**context_kwargs)
        self._page = self._context.new_page()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        video: Video | None = None
        if self._page is not None and self._page.video is not None:
            video = self._page.video

        if self._context is not None:
            self._context.close()

        if video is not None and self._record_video_path is not None:
            try:
                raw_path = Path(video.path())
                if raw_path.exists():
                    self._record_video_path.parent.mkdir(parents=True, exist_ok=True)
                    if self._record_video_path.exists():
                        self._record_video_path.unlink()
                    shutil.move(str(raw_path), str(self._record_video_path))
                    self._finalized_recording_path = self._record_video_path
            except Exception:
                self._finalized_recording_path = None

        if self._record_video_dir is not None and self._record_video_dir.exists():
            try:
                self._record_video_dir.rmdir()
            except OSError:
                pass

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
        # Figma prototypes keep long-lived connections; networkidle often never fires.
        try:
            self.page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=self.navigation_timeout_ms,
            )
        except Exception as exc:
            raise BrowserAdapterError(f"Failed to open {url}: {exc}") from exc
        if target == "figma":
            self.wait(FIGMA_POST_LOAD_WAIT_MS)

    def capture_frame(
        self,
        *,
        step: int,
        output_dir: Path,
        phase: str = "observe",
        filename_suffix: str = "",
    ) -> ObservationFrame:
        screenshots_dir = output_dir / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        image_path = screenshots_dir / f"step-{step:03d}{filename_suffix}.png"
        try:
            self.show_cursor_marker()
            self.page.screenshot(path=str(image_path), full_page=False)
        except Exception as exc:
            raise BrowserAdapterError(f"Failed to capture screenshot: {exc}") from exc

        return ObservationFrame(
            step=step,
            image_path=image_path,
            url=self.page.url,
            viewport_width=self.viewport_width,
            viewport_height=self.viewport_height,
            cursor_x=self._cursor_x,
            cursor_y=self._cursor_y,
            phase=phase,
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
