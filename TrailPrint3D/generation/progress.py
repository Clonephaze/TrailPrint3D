"""Progress overlay — GPU-drawn floating panel on the 3D viewport.

Provides a centered, styled progress dialog with:
- Title bar with accent stripe
- Phase / message labels
- Animated progress bar with percentage
- Elapsed-time counter
- ESC-to-cancel hint

Usage::

    from .progress import ProgressOverlay

    overlay = ProgressOverlay.get()
    overlay.start()
    overlay.update(percent=0.5, phase="Fetching Elevation", message="Tile 5/10")
    overlay.finish()
"""

from __future__ import annotations

import time

import bpy  # type: ignore
import blf  # type: ignore
import gpu  # type: ignore
from gpu_extras.batch import batch_for_shader  # type: ignore


class ProgressOverlay:
    """Singleton that manages a GPU-drawn progress panel on all 3D viewports."""

    _instance: ProgressOverlay | None = None

    # ── Public state (read by draw callback) ──────────────────────────────

    active: bool = False
    phase: str = ""
    message: str = ""
    percent: float = 0.0
    start_time: float = 0.0

    # ── Internal ──────────────────────────────────────────────────────────

    _handle = None

    # ── Singleton ─────────────────────────────────────────────────────────

    @classmethod
    def get(cls) -> ProgressOverlay:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def start(self) -> None:
        """Activate the overlay and install the draw handler."""
        self.active = True
        self.phase = "Initializing"
        self.message = ""
        self.percent = 0.0
        self.start_time = time.time()
        self._install_handler()
        self._redraw_viewports()

    def update(
        self,
        percent: float | None = None,
        message: str | None = None,
        phase: str | None = None,
    ) -> None:
        """Update progress state (any combination of fields)."""
        if percent is not None:
            self.percent = max(0.0, min(percent, 1.0))
        if message is not None:
            self.message = message
        if phase is not None:
            self.phase = phase

    def finish(self) -> None:
        """Deactivate the overlay and remove the draw handler."""
        self.active = False
        self._remove_handler()
        self._redraw_viewports()

    # ── Draw handler management ───────────────────────────────────────────

    def _install_handler(self) -> None:
        if self._handle is None:
            self._handle = bpy.types.SpaceView3D.draw_handler_add(
                self._draw, (), "WINDOW", "POST_PIXEL",
            )

    def _remove_handler(self) -> None:
        if self._handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, "WINDOW")
            self._handle = None

    @staticmethod
    def _redraw_viewports() -> None:
        """Tag every 3D viewport for redraw so the overlay appears/disappears."""
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == "VIEW_3D":
                    area.tag_redraw()

    # ── GPU draw callback ─────────────────────────────────────────────────

    # Layout constants
    _PANEL_W = 460
    _PANEL_H = 190
    _BAR_MARGIN = 30
    _BAR_H = 24

    # Colours
    _COL_SHADOW    = (0.0,  0.0,  0.0,  0.35)
    _COL_PANEL     = (0.12, 0.12, 0.16, 0.94)
    _COL_ACCENT    = (0.28, 0.56, 0.90, 1.0)
    _COL_BAR_BG    = (0.06, 0.06, 0.09, 1.0)
    _COL_BAR_FILL  = (0.28, 0.56, 0.90, 1.0)
    _COL_TITLE     = (1.0,  1.0,  1.0,  1.0)
    _COL_PHASE     = (0.82, 0.82, 0.88, 1.0)
    _COL_DETAIL    = (0.55, 0.55, 0.60, 1.0)
    _COL_HINT      = (0.38, 0.38, 0.42, 0.85)

    def _draw(self) -> None:
        if not self.active:
            return

        region = bpy.context.region
        if region is None:
            return

        rw, rh = region.width, region.height

        pw, ph = self._PANEL_W, self._PANEL_H
        px = (rw - pw) / 2
        py = (rh - ph) / 2

        bm = self._BAR_MARGIN
        bh = self._BAR_H
        bx = px + bm
        bw = pw - bm * 2
        # Bar positioned slightly above vertical centre
        by = py + ph * 0.42

        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        gpu.state.blend_set("ALPHA")

        # Shadow (slightly larger dark rect behind panel)
        _draw_rect(shader, px - 5, py - 5, pw + 10, ph + 10, self._COL_SHADOW)

        # Panel background
        _draw_rect(shader, px, py, pw, ph, self._COL_PANEL)

        # Accent stripe along the top
        _draw_rect(shader, px, py + ph - 3, pw, 3, self._COL_ACCENT)

        # Progress bar background
        _draw_rect(shader, bx, by, bw, bh, self._COL_BAR_BG)

        # Progress bar fill
        fill_w = bw * self.percent
        if fill_w > 1:
            _draw_rect(shader, bx, by, fill_w, bh, self._COL_BAR_FILL)

        gpu.state.blend_set("NONE")

        # ── Text ──────────────────────────────────────────────────────────
        cx = px + pw / 2  # horizontal centre of panel
        font = 0

        # Title
        _draw_centred(font, cx, py + ph - 28, "TrailPrint3D", 18, self._COL_TITLE)

        # Phase label (above bar)
        _draw_centred(font, cx, by + bh + 14, self.phase, 14, self._COL_PHASE)

        # Percentage (on bar)
        pct_str = f"{int(self.percent * 100)}%"
        _draw_centred(font, cx, by + 5, pct_str, 13, self._COL_TITLE)

        # Detail line (below bar): message + elapsed
        elapsed = time.time() - self.start_time
        mins, secs = divmod(int(elapsed), 60)
        detail = self.message
        if detail:
            detail += f"  ·  {mins}:{secs:02d} elapsed"
        else:
            detail = f"{mins}:{secs:02d} elapsed"
        _draw_centred(font, cx, by - 20, detail, 12, self._COL_DETAIL)

        # ESC hint
        _draw_centred(font, cx, py + 12, "Press ESC to cancel", 11, self._COL_HINT)


# ── Module-level GPU helpers ──────────────────────────────────────────────


def _draw_rect(
    shader, x: float, y: float, w: float, h: float, color: tuple,
) -> None:
    """Draw a filled rectangle."""
    verts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    indices = [(0, 1, 2), (0, 2, 3)]
    batch = batch_for_shader(shader, "TRIS", {"pos": verts}, indices=indices)
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


def _draw_centred(
    font_id: int, cx: float, y: float, text: str, size: int, color: tuple,
) -> None:
    """Draw *text* horizontally centred at (*cx*, *y*)."""
    blf.size(font_id, size)
    blf.color(font_id, *color)
    tw, _ = blf.dimensions(font_id, text)
    blf.position(font_id, cx - tw / 2, y, 0)
    blf.draw(font_id, text)
