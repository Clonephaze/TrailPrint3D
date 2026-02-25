"""Generation operators — modal (with progress) and batch (synchronous)."""

from __future__ import annotations

import os
import threading
import time

import bpy  # type: ignore

from ..context import GenerationContext
from ..elevation.base import extract_world_verts, fetch_tile_elevations, ElevationResult
from ..generation.progress import ProgressOverlay
from ..generation.validation import validate_inputs
from ..generation.loading import load_gps_data, prepare_blender_coords, reproject_after_elevation
from ..generation.terrain import create_terrain_mesh, apply_terrain_elevation
from ..generation.trail import create_trail
from ..generation.decorations import apply_decorations
from ..generation.finalize import finalize


# ── Background elevation worker ──────────────────────────────────────────


class _ElevationThread(threading.Thread):
    """Fetch elevation data in a background thread."""

    def __init__(
        self,
        world_verts: list[tuple[float, float, float]],
        api: int,
        dataset: str,
        opentopo_addr: str,
        num_subdivisions: int,
        scale_hor: float,
    ):
        super().__init__(daemon=True)
        self.world_verts = world_verts
        self.api = api
        self.dataset = dataset
        self.opentopo_addr = opentopo_addr
        self.num_subdivisions = num_subdivisions
        self.scale_hor = scale_hor

        # Shared state (read by modal timer on main thread)
        self.progress: float = 0.0
        self.message: str = ""
        self.result: ElevationResult | None = None
        self.error: str | None = None
        self._cancel = threading.Event()

    def cancel(self) -> None:
        self._cancel.set()

    @property
    def cancelled(self) -> bool:
        return self._cancel.is_set()

    def run(self) -> None:
        try:
            self.result = fetch_tile_elevations(
                self.world_verts,
                api=self.api,
                dataset=self.dataset,
                opentopoAddress=self.opentopo_addr,
                num_subdivisions=self.num_subdivisions,
                scale_hor=self.scale_hor,
                progress_callback=self._on_progress,
                cancel_event=self._cancel,
            )
        except Exception as exc:
            self.error = str(exc)

    def _on_progress(self, pct: float, msg: str) -> None:
        self.progress = pct
        self.message = msg


# ── Phase constants ──────────────────────────────────────────────────────

_INIT            = 0
_LOAD_GPS        = 1
_PREP_COORDS     = 2
_CREATE_MESH     = 3
_FETCH_ELEVATION = 4   # threaded
_APPLY_ELEVATION = 5
_REPROJECT       = 6
_CREATE_TRAIL    = 7
_DECORATIONS     = 8
_FINALIZE        = 9
_DONE            = 10


# ── Modal generation operator ────────────────────────────────────────────


class MY_OT_runGeneration(bpy.types.Operator):
    """Generate a 3D terrain map from GPS data (non-blocking, with progress)."""

    bl_idname = "wm.run_my_script"
    bl_label = "Generate"
    bl_description = "Generate path and map with current settings"
    bl_options = {'REGISTER'}

    gen_type: bpy.props.IntProperty(default=0, options={'HIDDEN'})  # type: ignore

    # Class-level guard against double invocation
    _is_running: bool = False

    # Instance state (reset each invoke)
    _timer = None
    _phase: int = _INIT
    _ctx: GenerationContext | None = None
    _start_time: float = 0.0
    _worker: _ElevationThread | None = None
    _created_objects: list = []

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def invoke(self, context, event):
        if MY_OT_runGeneration._is_running:
            self.report({'WARNING'}, "Generation already in progress")
            return {'CANCELLED'}

        MY_OT_runGeneration._is_running = True
        self._phase = _INIT
        self._ctx = None
        self._start_time = time.time()
        self._worker = None
        self._created_objects = []

        self._timer = context.window_manager.event_timer_add(
            0.05, window=context.window,
        )
        context.window_manager.modal_handler_add(self)

        ProgressOverlay.get().start()
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'ESC':
            return self._cancel(context)

        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        try:
            result = self._tick(context)
        except Exception as exc:
            return self._fail(context, str(exc))

        # Force viewport redraw so overlay updates
        self._tag_redraw(context)
        return result

    # ── Phase dispatcher ──────────────────────────────────────────────────

    def _tick(self, context):  # noqa: C901 — intentionally flat switch
        p = ProgressOverlay.get()

        # ── INIT ──────────────────────────────────────────────────────────
        if self._phase == _INIT:
            p.update(percent=0.02, phase="Initializing", message="Reading settings...")
            ctx = GenerationContext.from_scene(self.gen_type)

            # Resolve export path
            if not ctx.exportPath and ctx.gpx_file_path:
                d = os.path.dirname(ctx.gpx_file_path)
                b = os.path.splitext(os.path.basename(ctx.gpx_file_path))[0]
                ctx.exportPath = os.path.join(d, b)
            ctx.exportPath = bpy.path.abspath(ctx.exportPath) if ctx.exportPath else ""
            if ctx.gpx_file_path:
                ctx.gpx_file_path = bpy.path.abspath(ctx.gpx_file_path)
            if ctx.gpx_chain_path:
                ctx.gpx_chain_path = bpy.path.abspath(ctx.gpx_chain_path)

            ctx.opentopoAddress = "https://api.opentopodata.org/v1/"
            if ctx.selfHosted and ctx.api_index == 1:
                ctx.opentopoAddress = ctx.selfHosted

            if not validate_inputs(ctx, self.gen_type):
                return self._fail(context, "Input validation failed — check file paths")

            # Auto-name
            if not ctx.name:
                gt = self.gen_type
                if gt in (0, 4) and ctx.gpx_file_path:
                    ctx.name = os.path.splitext(os.path.basename(ctx.gpx_file_path))[0]
                elif gt == 1 and ctx.gpx_chain_path:
                    ctx.name = os.path.splitext(os.path.basename(os.path.normpath(ctx.gpx_chain_path)))[0]
                else:
                    ctx.name = "Terrain"

            if ctx.singleColorMode:
                ctx.overwritePathElevation = False

            # Ensure object mode
            if bpy.context.object and bpy.context.object.mode == 'EDIT':
                bpy.ops.object.mode_set(mode='OBJECT')
            bpy.context.scene.tool_settings.use_mesh_automerge = False

            self._ctx = ctx
            self._phase = _LOAD_GPS
            return {'RUNNING_MODAL'}

        # ── LOAD GPS ──────────────────────────────────────────────────────
        if self._phase == _LOAD_GPS:
            p.update(percent=0.06, phase="Loading GPS Data", message="Parsing files...")
            if not load_gps_data(self._ctx, self.gen_type):
                return self._fail(context, "Failed to load GPS data")
            self._ctx.elevationOffset = bpy.context.scene.tp3d.get("sElevationOffset", 0.0)
            self._phase = _PREP_COORDS
            return {'RUNNING_MODAL'}

        # ── PREP COORDS ──────────────────────────────────────────────────
        if self._phase == _PREP_COORDS:
            p.update(percent=0.10, phase="Preparing Coordinates", message="Converting projections...")
            prepare_blender_coords(self._ctx, self.gen_type)
            self._phase = _CREATE_MESH
            return {'RUNNING_MODAL'}

        # ── CREATE MESH ──────────────────────────────────────────────────
        if self._phase == _CREATE_MESH:
            p.update(percent=0.15, phase="Creating Terrain Mesh", message="Building shape...")
            if not create_terrain_mesh(self._ctx, self.gen_type):
                return self._fail(context, "Failed to create terrain mesh")
            self._created_objects.append(self._ctx.MapObject)
            self._phase = _FETCH_ELEVATION
            return {'RUNNING_MODAL'}

        # ── FETCH ELEVATION (threaded) ───────────────────────────────────
        if self._phase == _FETCH_ELEVATION:
            if self._worker is None:
                # First tick: start background thread
                p.update(percent=0.20, phase="Fetching Elevation Data", message="Starting download...")
                world_verts = extract_world_verts(self._ctx.MapObject)
                self._worker = _ElevationThread(
                    world_verts,
                    api=self._ctx.api_index,
                    dataset=self._ctx.dataset,
                    opentopo_addr=self._ctx.opentopoAddress,
                    num_subdivisions=self._ctx.num_subdivisions,
                    scale_hor=self._ctx.scaleHor,
                )
                self._worker.start()
                return {'RUNNING_MODAL'}

            if self._worker.is_alive():
                # Poll progress from thread
                wp = self._worker.progress
                p.update(
                    percent=0.20 + wp * 0.50,
                    message=self._worker.message,
                )
                return {'RUNNING_MODAL'}

            # Thread finished
            if self._worker.error:
                return self._fail(context, f"Elevation fetch error: {self._worker.error}")
            if self._worker.cancelled:
                return self._cancel(context)
            self._phase = _APPLY_ELEVATION
            return {'RUNNING_MODAL'}

        # ── APPLY ELEVATION ──────────────────────────────────────────────
        if self._phase == _APPLY_ELEVATION:
            p.update(percent=0.72, phase="Applying Elevation", message="Shaping terrain...")
            if not apply_terrain_elevation(self._ctx, self._worker.result):
                return self._fail(context, "Failed to apply elevation")
            self._phase = _REPROJECT
            return {'RUNNING_MODAL'}

        # ── REPROJECT ────────────────────────────────────────────────────
        if self._phase == _REPROJECT:
            p.update(percent=0.76, phase="Reprojecting Coordinates")
            reproject_after_elevation(self._ctx, self.gen_type)
            self._phase = _CREATE_TRAIL
            return {'RUNNING_MODAL'}

        # ── CREATE TRAIL ─────────────────────────────────────────────────
        if self._phase == _CREATE_TRAIL:
            if self.gen_type in (2, 3):
                self._phase = _DECORATIONS
                return {'RUNNING_MODAL'}
            p.update(percent=0.80, phase="Creating Trail", message="Building curve...")
            if not create_trail(self._ctx, self.gen_type):
                return self._fail(context, "Failed to create trail")
            self._phase = _DECORATIONS
            return {'RUNNING_MODAL'}

        # ── DECORATIONS ──────────────────────────────────────────────────
        if self._phase == _DECORATIONS:
            p.update(percent=0.87, phase="Adding Decorations", message="Text and flags...")
            apply_decorations(self._ctx)
            self._phase = _FINALIZE
            return {'RUNNING_MODAL'}

        # ── FINALIZE ─────────────────────────────────────────────────────
        if self._phase == _FINALIZE:
            p.update(percent=0.95, phase="Finalizing", message="Exporting and cleanup...")
            finalize(self._ctx, self.gen_type, self._start_time)
            self._phase = _DONE
            return {'RUNNING_MODAL'}

        # ── DONE ─────────────────────────────────────────────────────────
        if self._phase == _DONE:
            p.update(percent=1.0, phase="Complete!", message="Terrain generated successfully")
            return self._finish(context)

        return {'RUNNING_MODAL'}

    # ── Cleanup helpers ───────────────────────────────────────────────────

    def _finish(self, context):
        ProgressOverlay.get().finish()
        context.window_manager.event_timer_remove(self._timer)
        MY_OT_runGeneration._is_running = False
        bpy.ops.ed.undo_push()
        self.report({'INFO'}, "Generation complete")
        return {'FINISHED'}

    def _fail(self, context, message: str):
        ProgressOverlay.get().finish()
        context.window_manager.event_timer_remove(self._timer)
        MY_OT_runGeneration._is_running = False
        self.report({'ERROR'}, message)
        return {'CANCELLED'}

    def _cancel(self, context):
        # Stop background thread if running
        if self._worker and self._worker.is_alive():
            self._worker.cancel()
            self._worker.join(timeout=3)

        # Remove partially created objects
        for obj in self._created_objects:
            if obj and obj.name in bpy.data.objects:
                bpy.data.objects.remove(obj, do_unlink=True)

        ProgressOverlay.get().finish()
        context.window_manager.event_timer_remove(self._timer)
        MY_OT_runGeneration._is_running = False
        self.report({'INFO'}, "Generation cancelled")
        return {'CANCELLED'}

    @staticmethod
    def _tag_redraw(context):
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


# ── Batch operator (synchronous, no progress overlay) ────────────────────


class MY_OT_BatchGeneration(bpy.types.Operator):
    bl_idname = "wm.run_my_script2"
    bl_label = "Batch Generate"
    bl_description = "Generate single map from multiple GPX files in folder"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from ..generation.orchestrator import run_generation
        run_generation(1)
        bpy.ops.ed.undo_push()
        return {'FINISHED'}


# TODO: The following operator bl_idnames are referenced in the UI panels
# but were not implemented in the original monolith.  Add stubs or full
# implementations when the features are wired up:
#   wm.terrain           — Create map from selected object
#   wm.create_blank      — Create blank map
#   wm.extend_tile       — Extend selected tile
#   wm.fromcentergeneration          — From 1 point + radius
#   wm.fromcentergenerationwithtrail — From 1 point + radius + trail
#   wm.2pointgeneration  — From 2 points
#   wm.mergewithmap      — Merge to map
#   wm.update_special_collection — Load .blend file
#   wm.appendcollection  — Import collection
#   wm.citycoords        — Add pin at city name
