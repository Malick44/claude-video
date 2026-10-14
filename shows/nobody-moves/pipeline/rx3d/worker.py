"""The worker: runs inside Blender (docs/BLENDER_REENACTMENTS.md §7), always in its own process.

  python-with-bpy pipeline/blender_reenact.py --worker <job.json>
  blender -b --factory-startup --python-exit-code 1 -P pipeline/blender_reenact.py -- --worker <job.json>

For each job: a clean factory scene, the template builds the set, subjects and camera and keys the motion
(one sample per frame), then the worker
  1. steps through every clip frame and dumps motion.json (matrices, screen boxes and convex hulls, headings,
     mesh hashes, beam clearances, prop anchors on screen, the feet's visibility on the last shown frame),
  2. asserts the rules: locked camera, static props, constant yaw, no mesh deformation, stillness before
     the move, Lorraine's facing, no beam touching the subject, opaque glare sources, rough dark surfaces
     (any failure is a StagingError: nothing is rendered),
  3. renders the requested frames (skipping frames already on disk, so an interrupted render resumes) and
     measures each one (mean and spread of luma, subject and backdrop luma) with bpy + numpy, so no PIL is needed,
  4. writes result.json: the Blender version and build hash, the device actually used, seconds per frame,
     frame stats, facts and errors.
A job file holds one job or {"jobs": [...]} (the selftest renders every template in one process).
"""
import json
import math
import os
import random
import sys
import time
import traceback

import bpy
from mathutils import Vector

from . import look, proxies, templates

W, H = 1080, 1920
BEAM_MIN_CLEARANCE_M = 0.25 * 0.0254          # the never-touch rule: a quarter inch between any beam and the subject
SOFTWARE_GL = ("llvmpipe", "softpipe", "swiftshader", "microsoft basic render", "swrast")


class StagingError(RuntimeError):
    pass


def blender_info():
    h = bpy.app.build_hash
    return {"version": bpy.app.version_string.split()[0], "version_tuple": list(bpy.app.version),
            "hash": h.decode() if isinstance(h, bytes) else str(h)}


class Ctx:
    """What a template sees: the job, a seeded rng, beats in clip frames, and the build helpers."""

    def __init__(self, job):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        try:
            bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
        except Exception:
            pass
        self.job = job
        self.scene = bpy.context.scene
        self.col = self.scene.collection
        self.fps = job["fps"]
        self.nframes = job["frames"]
        self.last_shown = job["last_shown"]
        self.rng = random.Random(job["seed"])
        self.opts = job["options"]
        self.cam_spec = job["camera"]
        self.cam_lens = float(job["camera"]["lens"])
        self.props = [p["name"] for p in job.get("props", [])]
        self.haze = job["render"]["haze"]
        self.quality = job["render"]["quality"]
        self.zones = job.get("zones", {})          # screen rectangles in 1080x1920 px: {"tag": [x0, y0, x1, y1]}
        self.facts, self.tracks = {}, {}
        self.movers, self.prop_subjects, self.fx_objs, self.all_subjects = [], [], [], []
        self.beams = []                             # (name, centre, unit direction, half length, radius)
        self.exposure, self.facing, self.mist = 0.0, None, None
        self.keep_clear = ["subject"]               # tracks that must stay out of the tag zone (driver check)
        self.coverage = {}                          # {track: {"min_frac", "by_frame"}}: an effect big enough to read
        sc = self.scene
        sc.frame_start, sc.frame_end = 1, self.nframes
        sc.render.fps = self.fps

    # beats are clip frames (0-based); Blender frame = clip frame + 1. A "start" beat (move, move2, tip) is the
    # last still frame: the motion shows from the next frame. An "event" beat (land, flare) happens on its frame.
    def has_beat(self, name):
        return bool(self.job["beats"].get(name))

    def beat_frame(self, name):
        b = self.job["beats"].get(name)
        return int(b["frame"]) if b else None

    def beat_t(self, name):
        f = self.beat_frame(name)
        return None if f is None else f / self.fps

    def beat_word(self, name):
        b = self.job["beats"].get(name)
        return b.get("word_t") if b else None

    def subject(self, outfit=None):
        s = self.job["subject"]
        sub = proxies.add_subject(s["name"], s, self.col, "subject", outfit=outfit)
        self.all_subjects.append(sub)
        return sub

    def prop(self, name):
        p = next(p for p in self.job["props"] if p["name"] == name)
        sub = proxies.add_subject(name, p, self.col, "prop")
        self.prop_subjects.append(sub)
        self.all_subjects.append(sub)
        return sub

    def mover(self, sub):
        self.movers.append(sub)

    def fx(self, ob, kind="fx"):
        ob["rx_fx"] = kind
        self.fx_objs.append(ob)

    def fx_tag(self, ob, kind):
        """Mark an effect object (dust, ember, spark, fireball): it may never hide the subject's feet."""
        ob["rx_fx"] = kind

    def track(self, name, objs):
        self.tracks[name] = list(objs)

    def fact(self, key, value):
        self.facts[key] = value

    def beam(self, name, centre, direction, half_len, radius):
        self.beams.append((name, Vector(centre), Vector(direction).normalized(), float(half_len), float(radius)))

    def key_rigid(self, ob, k, loc, rot=(0.0, 0.0, 0.0)):
        """Key a subject root on clip frame k: location, and roll/pitch (X/Y). Index 2 (yaw) is never keyed."""
        if abs(rot[2]) > 1e-12:
            raise StagingError(f"yaw changed: {ob.get('cast', ob.name)} never turns (key_rigid got a yaw)")
        ob.location = loc
        ob.rotation_euler[0], ob.rotation_euler[1] = rot[0], rot[1]
        ob.keyframe_insert("location", frame=k + 1)
        ob.keyframe_insert("rotation_euler", index=0, frame=k + 1)
        ob.keyframe_insert("rotation_euler", index=1, frame=k + 1)

    def make_camera(self, loc, tilt, pan_deg, focus, parent=None):
        c = self.cam_spec
        cd = bpy.data.cameras.new("rx_cam")
        cd.lens = float(c["lens"])
        cd.sensor_fit = "VERTICAL"
        cd.sensor_width, cd.sensor_height = 36.0, templates.SENSOR_H
        cd.clip_start, cd.clip_end = 0.01, 400.0
        if focus is not None:
            cd.dof.use_dof = True
            cd.dof.focus_object = focus
            cd.dof.aperture_fstop = float(c.get("fstop", 2.8))
        ob = bpy.data.objects.new("rx_cam", cd)
        self.col.objects.link(ob)
        ob.parent = parent
        ob.location = loc
        ob.rotation_euler = (math.pi / 2 + tilt, 0.0, math.radians(pan_deg or 0.0))
        self.scene.camera = ob
        return ob

    def _points_per_frame(self, meshes, frames):
        import numpy as np
        out = []
        for k in frames:
            self.scene.frame_set(k + 1)
            pts = []
            for ob in meshes:
                co = _local_verts(ob)
                m = np.array(ob.matrix_world)
                pts.append(co @ m[:3, :3].T + m[:3, 3])
            out.append(np.concatenate(pts))
        return out

    def fit_camera(self, cam, meshes, frames, max_w=0.86, max_h=0.90, center_y=0.0, anchor_cx=None, x_bounds=None,
                   iters=24):
        """Frame a whole move from the subject's real vertices: dolly the (locked) camera back along its view
        axis until the union of the silhouettes over `frames` fits max_w x max_h of the frame, and put its vertical
        centre at `center_y` (ndc, +1 top) with the tilt. Horizontally: centre the union, or with `anchor_cx`
        (0..1 from the left) truck the camera so the FIRST frame's box is centred there (the hard cut back to the
        real still matches the reenactment's first frame), dollying back until the whole move stays inside
        `x_bounds` (0..1). Called after the motion is keyed and before anything is placed from screen positions."""
        import numpy as np
        frames = list(frames)
        if frames[0] != 0:
            frames = [0] + frames
        P_all = self._points_per_frame(meshes, frames)
        P = np.concatenate(P_all)
        P0 = P_all[0]
        tv = (templates.SENSOR_H / 2) / cam.data.lens
        th = tv * W / H
        C = np.array(cam.location)
        C0 = C.copy()
        tilt = cam.rotation_euler[0] - math.pi / 2
        lo_b, hi_b = (2 * x_bounds[0] - 1, 2 * x_bounds[1] - 1) if x_bounds else (-max_w, max_w)

        def ndc(Q, R):
            q = (Q - C) @ R
            d = -q[:, 2]
            return q[:, 0] / d / th, q[:, 1] / d / tv, d
        for _ in range(iters):
            R = np.array(cam.rotation_euler.to_matrix())
            x, y, depth = ndc(P, R)
            dmean = float(np.median(depth))
            fwd = R @ np.array([0, 0, -1.0])
            wf, hf = (x.max() - x.min()) / 2, (y.max() - y.min()) / 2
            if anchor_cx is None:
                scale = max(wf / max_w, hf / max_h)
            else:
                x0, _, _ = ndc(P0, R)
                shift = (x0.max() + x0.min()) / 2 - (2 * anchor_cx - 1)
                xs = x - shift                              # where the union lands once frame 0 is anchored
                over = max(xs.max() / hi_b if xs.max() > 0 else 0, xs.min() / lo_b if xs.min() < 0 else 0)
                scale = max(over, hf / max_h)
            if os.environ.get("RX_DEBUG_FIT"):
                print("FIT", round(scale, 3), [round(float(v), 3) for v in (x.min(), x.max(), y.min(), y.max())],
                      round(dmean, 3), [round(float(c), 3) for c in C], flush=True)
            # dolly level (a tilted camera backing along its own axis would sink): back while the move doesn't fit,
            # forward again (damped) while it has room, never closer than the solved distance, so the start pose
            # keeps as much of its `fill` as the move allows
            fh = np.array([fwd[0], fwd[1], 0.0])
            fh /= max(np.linalg.norm(fh), 1e-9)
            if scale > 1.001:
                C = C - fh * dmean * (scale - 1) * 0.7
            elif scale < 0.99:
                step = min(dmean * (1 - scale) * 0.5, float(np.dot(C0 - C, -fh)))
                if step > 1e-4:
                    C = C + fh * step
            R = np.array(cam.rotation_euler.to_matrix())
            if anchor_cx is None:
                x, _, _ = ndc(P, R)
                C[0] += (x.max() + x.min()) / 2 * th * dmean
            else:
                x0, _, d0 = ndc(P0, R)
                C[0] += ((x0.max() + x0.min()) / 2 - (2 * anchor_cx - 1)) * th * float(np.median(d0))
            _, y, _ = ndc(P, R)
            tilt += math.atan((y.max() + y.min()) / 2 * tv) - math.atan(center_y * tv)
            cam.location = tuple(C)
            cam.rotation_euler = (math.pi / 2 + tilt, cam.rotation_euler[1], cam.rotation_euler[2])
        R = np.array(cam.rotation_euler.to_matrix())
        x, y, _ = ndc(P, R)
        x0, y0, _ = ndc(P0, R)
        self.scene.frame_set(1)
        res = {"x": [round(float(x.min()), 3), round(float(x.max()), 3)],
               "y": [round(float(y.min()), 3), round(float(y.max()), 3)],
               "frame0_cx": round(float((x0.max() + x0.min()) / 4 + 0.5), 4),
               "frame0_h": round(float((y0.max() - y0.min()) / 2), 4),
               "tilt_deg": round(math.degrees(tilt), 3), "loc": [round(float(c), 4) for c in C]}
        if x_bounds and (x.min() < lo_b - 0.01 or x.max() > hi_b + 0.01):
            raise StagingError(f"the move leaves x {x_bounds[0]:.2f}-{x_bounds[1]:.2f} of the frame "
                               f"({(x.min() + 1) / 2:.3f}-{(x.max() + 1) / 2:.3f}) even after dollying back")
        return res

    def screen_point(self, cam, sx, sy, depth):
        """World point at screen (sx, sy) (0..1 from the top left) at `depth` metres along the view axis."""
        tv = (templates.SENSOR_H / 2) / cam.data.lens
        th = tv * W / H
        d = Vector(((sx - 0.5) * 2 * th, (0.5 - sy) * 2 * tv, -1.0)) * depth
        return cam.location + cam.rotation_euler.to_matrix() @ d

    def to_screen(self, cam, p):
        """(x, y) in 1080x1920 px of world point p, and its depth."""
        tv = (templates.SENSOR_H / 2) / cam.data.lens
        th = tv * W / H
        q = cam.rotation_euler.to_matrix().transposed() @ (Vector(p) - cam.location)
        d = -q.z
        return (0.5 + 0.5 * q.x / d / th) * W, (0.5 - 0.5 * q.y / d / tv) * H, d


# ---------------------------------------------------------------- motion dump and the rules
def _mat(m):
    return [round(v, 6) + 0.0 for row in m for v in row]


_VERTS = {}


def _local_verts(ob, full=False):
    """A fixed vertex subsample (<= ~600) of a mesh in object space: screen boxes from real geometry, not from the
    conservative bound_box corners of a rotated figure. Cached for rigid meshes; an effect mesh with modifiers
    (the fireball's billowing displacement) is evaluated on the current frame."""
    import numpy as np
    animated = bool(ob.modifiers)
    key = (ob.name, full)
    if animated or key not in _VERTS:
        if animated:
            dg = bpy.context.evaluated_depsgraph_get()
            ev = ob.evaluated_get(dg)
            me = ev.to_mesh()
            n = len(me.vertices)
            co = np.empty(n * 3)
            me.vertices.foreach_get("co", co)
            ev.to_mesh_clear()
        else:
            n = len(ob.data.vertices)
            co = np.empty(n * 3)
            ob.data.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        if not full:
            co = co[:: max(1, n // 600)]
        if animated:
            return co
        _VERTS[key] = co
    return _VERTS[key]


def _project(cam, objs):
    import numpy as np
    R = np.array(cam.matrix_world.to_3x3())
    C = np.array(cam.matrix_world.translation)
    tv = (templates.SENSOR_H / 2) / cam.data.lens
    th = tv * W / H
    xs, ys = [], []
    for ob in objs:
        if ob.type != "MESH" or not len(ob.data.vertices):
            continue
        m = np.array(ob.matrix_world)
        if not ob.visible_get() or ob.hide_render or (abs(np.linalg.det(m[:3, :3])) < 1e-12):
            continue
        p = _local_verts(ob) @ m[:3, :3].T + m[:3, 3]
        q = (p - C) @ R
        d = -q[:, 2]
        ok = d > 1e-4
        if not ok.any():
            continue
        xs.append((0.5 + 0.5 * q[ok, 0] / d[ok] / th) * W)
        ys.append((0.5 - 0.5 * q[ok, 1] / d[ok] / tv) * H)
    if not xs:
        return None
    return np.concatenate(xs), np.concatenate(ys)


def _bbox_px(cam, objs):
    pr = _project(cam, objs)
    if pr is None:
        return None
    xs, ys = pr
    return [round(float(xs.min()), 2), round(float(ys.min()), 2), round(float(xs.max()), 2), round(float(ys.max()), 2)]


def _hull_px(cam, objs):
    """Convex hull of the projected vertices, integer px (monotone chain). Lets the driver test a round effect
    against the tag zone without a bounding box's false corners, and re-test it when the tag widens."""
    pr = _project(cam, objs)
    if pr is None:
        return None
    pts = sorted(set(zip((int(round(float(x))) for x in pr[0]), (int(round(float(y))) for y in pr[1]))))
    if len(pts) <= 2:
        return [list(p) for p in pts]

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return [list(p) for p in lower[:-1] + upper[:-1]]


def _heading(m):
    f = -m.col[1].to_3d()          # the figure's front, local -Y, in world space
    return math.atan2(f.y, f.x)


def _facing(m, cam_m):
    """(angle of the front to the image plane in deg, + toward the camera; screen-x sign of the front)."""
    f = (-m.col[1].to_3d()).normalized()
    fwd = -cam_m.col[2].to_3d().normalized()        # camera looks along its local -Z
    right = cam_m.col[0].to_3d().normalized()
    toward = -f.dot(fwd)
    return math.degrees(math.asin(max(-1.0, min(1.0, toward)))), f.dot(right)


_BVH = {}


def _beam_clearance(ctx, sub):
    """Smallest distance (m) between any beam's surface and the subject's SURFACE on the current frame (negative:
    the beam passes through it). Beam points every 1 mm near the subject are tested against a BVH of each rigid
    mesh in its own space (vertices alone miss a beam that crosses a face between them)."""
    from mathutils.bvhtree import BVHTree
    if not ctx.beams:
        return None
    best = 1e9
    for ob in sub.meshes:
        if ob.name not in _BVH:
            dg = bpy.context.evaluated_depsgraph_get()
            _BVH[ob.name] = BVHTree.FromObject(ob, dg)
        tree = _BVH[ob.name]
        Mi = ob.matrix_world.inverted()
        s = ob.matrix_world.to_scale()[0]               # normalization is uniform
        centre = ob.matrix_world @ Vector(ob.bound_box[0]).lerp(Vector(ob.bound_box[6]), 0.5)
        rad = (ob.matrix_world @ Vector(ob.bound_box[6]) - ob.matrix_world @ Vector(ob.bound_box[0])).length / 2 + 0.05
        for _, c, d, half, r in ctx.beams:
            t0 = (centre - c).dot(d)
            lo, hi = max(-half, t0 - rad), min(half, t0 + rad)
            if hi <= lo or ((c + d * t0) - centre).length > rad:
                continue
            p0, p1 = Mi @ (c + d * lo), Mi @ (c + d * hi)
            hit = tree.ray_cast(p0, (p1 - p0).normalized(), (p1 - p0).length)
            if hit[0] is not None:
                best = min(best, -r)
                continue
            n = max(2, int((hi - lo) / 0.001))
            for i in range(n + 1):
                q = Mi @ (c + d * (lo + (hi - lo) * i / n))
                near = tree.find_nearest(q)
                if near[0] is not None:
                    best = min(best, near[3] * s - r)
    return best if best < 1e8 else None


def _feet_visibility(ctx, sub, cam):
    """Ray-test the subject's base (vertices within 5% of its height of the ground) from the camera on the current
    frame: the fraction hidden by an effect (dust, embers ...) and by anything else (a step's nosing)."""
    import numpy as np
    dg = bpy.context.evaluated_depsgraph_get()
    v = proxies._verts_local(sub.meshes, sub.root)
    low = np.where(v[:, 2] < 0.05 * sub.height)[0]
    if not len(low):
        return None
    allp = []
    for ob in sub.meshes:
        m = np.array(ob.matrix_world)
        allp.append(_local_verts(ob, full=True) @ m[:3, :3].T + m[:3, 3])
    allp = np.concatenate(allp)
    idx = low[:: max(1, len(low) // 160)]
    meshes = {o.name for o in sub.meshes}
    origin = cam.matrix_world.translation.copy()
    n_fx = n_other = n = 0
    for i in idx:
        p = Vector(allp[i])
        d = p - origin
        hit, loc, _, _, ob, _ = ctx.scene.ray_cast(dg, origin, d.normalized(), distance=d.length + 0.01)
        if not hit:
            continue
        n += 1
        name = ob.original.name if ob is not None else ""
        if name in meshes:
            continue
        if ob is not None and ob.original.get("rx_fx"):
            n_fx += 1
        else:
            n_other += 1
    if not n:
        return None
    return {"n": n, "fx": round(n_fx / n, 3), "other": round(n_other / n, 3)}


def dump_motion(ctx, tpl, path):
    sc = ctx.scene
    cam = sc.camera
    n = ctx.nframes
    rec = {"frames": n, "fps": ctx.fps, "w": W, "h": H, "template": ctx.job["template"],
           "camera": [], "objects": {}, "screen": {k: [] for k in ctx.tracks}, "hull": {k: [] for k in ctx.tracks},
           "heading_deg": {}, "facing": {}, "mesh_hash": {}, "beam_clearance_m": [], "prop_anchors": {}}
    movers = {s.name: s for s in ctx.movers}
    props = {s.name: s for s in ctx.prop_subjects}
    fx = {o.name: o for o in ctx.fx_objs}
    for name in list(movers) + list(props) + list(fx):
        rec["objects"][name] = []
    for name in movers:
        rec["heading_deg"][name] = []
        rec["mesh_hash"][name] = []
        if ctx.facing:
            rec["facing"][name] = []
    for k in range(n):
        sc.frame_set(k + 1)
        rec["camera"].append(_mat(cam.matrix_world))
        for name, s in movers.items():
            m = s.root.matrix_world
            rec["objects"][name].append(_mat(m))
            rec["heading_deg"][name].append(round(math.degrees(_heading(m)), 6) + 0.0)
            rec["mesh_hash"][name].append(proxies.mesh_hash(s.meshes))
            if ctx.facing:
                ang, sx = _facing(m, cam.matrix_world)
                rec["facing"][name].append([round(ang, 4) + 0.0, round(sx, 4) + 0.0])
        if ctx.beams and ctx.movers:
            c = _beam_clearance(ctx, ctx.movers[0])
            rec["beam_clearance_m"].append(None if c is None else round(c, 5) + 0.0)
        for name, s in props.items():
            rec["objects"][name].append(_mat(s.root.matrix_world))
        for name, o in fx.items():
            rec["objects"][name].append(_mat(o.matrix_world))
        for name, objs in ctx.tracks.items():
            rec["screen"][name].append(_bbox_px(cam, objs))
            rec["hull"][name].append(_hull_px(cam, objs))
        if k == 0:
            for name, s in props.items():
                for a, p in sorted(s.anchors.items()):
                    if a in ("head", "beak_tip"):
                        x, y, d = ctx.to_screen(cam, s.root.matrix_world @ Vector(p))
                        rec["prop_anchors"].setdefault(name, {})[a] = [round(x, 1), round(y, 1), round(d, 4)]
        if k == ctx.last_shown and ctx.movers:
            rec["feet_visibility"] = _feet_visibility(ctx, ctx.movers[0], cam)
    casts = {}
    for o in bpy.data.objects:
        if "cast" in o.keys() and (o.name.startswith(("subj_", "prop_")) or o.name == "chime_root"):
            casts[o["cast"]] = casts.get(o["cast"], 0) + 1
    rec["cast_count"] = dict(sorted(casts.items()))
    rec["subjects"] = {s.name: {"kind": s.kind, "height_m": round(s.height, 5),
                                "foot": {k: round(v, 5) for k, v in s.foot.items()},
                                "tris": getattr(s, "tris", None), "stripped": getattr(s, "stripped", [])}
                       for s in ctx.all_subjects}
    rec["zones"] = ctx.zones
    rec["keep_clear"] = list(ctx.keep_clear)
    rec["coverage_rules"] = ctx.coverage
    rec["last_shown"] = ctx.last_shown
    rec["facts"] = ctx.facts
    check_rules(ctx, tpl, rec)
    with open(path + ".tmp", "w") as f:
        json.dump(rec, f, sort_keys=True, separators=(",", ":"))
    os.replace(path + ".tmp", path)
    return rec


def material_problems():
    """Look rules the materials must keep (no template can repeat these mistakes):
    * nothing that feeds the glare (an emitter or an AOV writer) is BLENDED: on Eevee a blended material writes
      no render passes, so its bloom, streaks or flare would silently vanish from the final;
    * dark surfaces (doors, windows) are rough (>= 0.45) and uncoated: a glossy door mirrored the key light as
      'a light under the door'."""
    errs = []
    for m in bpy.data.materials:
        if not m.users or not m.node_tree:
            continue
        has_aov = any(n.bl_idname == "ShaderNodeOutputAOV" for n in m.node_tree.nodes)
        feeds_glare = has_aov or m.get("rx_kind") == "emissive"
        if feeds_glare and getattr(m, "surface_render_method", "DITHERED") == "BLENDED":
            errs.append(f"material {m.name}: BLENDED but it feeds the glare (emission/AOV); Eevee would drop it from "
                        f"the passes. Make it opaque and key its scale to 0 to hide it")
        if m.get("rx_kind") == "dark_surface":
            b = m.node_tree.nodes.get("Principled BSDF")
            if b is not None and (b.inputs["Roughness"].default_value < look.DARK_MIN_ROUGH - 1e-6
                                  or b.inputs["Coat Weight"].default_value > 1e-6):
                errs.append(f"material {m.name}: a dark surface must be rough (>= {look.DARK_MIN_ROUGH}) and uncoated")
    return errs


def check_rules(ctx, tpl, rec):
    """The rules a template must keep. Any failure is a StagingError: the clip is not rendered."""
    errs = []
    if tpl["locked_camera"] and any(m != rec["camera"][0] for m in rec["camera"]):
        errs.append("camera moved: the camera is locked off in every reenactment")
    for name in rec["objects"]:
        if name in {s.name for s in ctx.prop_subjects}:
            seq = rec["objects"][name]
            if any(m != seq[0] for m in seq):
                errs.append(f"prop moved: {name} is a still prop (nothing touches it)")
    move = ctx.job["beats"].get("move")
    for name in rec["heading_deg"]:
        hd = rec["heading_deg"][name]
        if tpl["yaw_locked"]:
            for k, v in enumerate(hd):
                d = (v - hd[0] + 180) % 360 - 180
                if abs(d) > 1e-3:
                    errs.append(f"yaw changed: {name} never turns (frame {k}: {v:.3f} deg vs {hd[0]:.3f} deg)")
                    break
        hs = rec["mesh_hash"][name]
        if any(h != hs[0] for h in hs):
            k = next(i for i, h in enumerate(hs) if h != hs[0])
            errs.append(f"mesh deformed: {name} changed shape at frame {k}; subjects are rigid")
        if move and tpl["yaw_locked"]:
            seq = rec["objects"][name]
            km = int(move["frame"])
            if any(seq[k] != seq[0] for k in range(min(km + 1, len(seq)))):
                errs.append(f"{name} moved before its beat (frame {km}): stillness first")
    if ctx.facing:
        allow = ctx.facing.get("allow")
        for name, seq in rec["facing"].items():
            angs = [a for a, _ in seq]
            sxs = [s for _, s in seq]
            if not allow and (max(angs) > 60.0 or min(angs) < 0.0):
                errs.append(f"{name} faces {'the camera' if max(angs) > 60 else 'away (her back)'}: angle to the "
                            f"image plane {min(angs):.1f}-{max(angs):.1f} deg (allowed 0-60; frame 418's secret)")
            if not allow and max(sxs) >= 0:
                errs.append(f"{name}'s beak must point to frame left")
    bc = [c for c in rec["beam_clearance_m"][: ctx.last_shown + 1] if c is not None]
    if bc and min(bc) < BEAM_MIN_CLEARANCE_M - 1e-5:
        k = rec["beam_clearance_m"].index(min(bc))
        errs.append(f"a beam comes within {min(bc) * 1000:.1f} mm of {ctx.movers[0].name} on frame {k}: nothing touches "
                    f"the subject (never-touch rule: keep {BEAM_MIN_CLEARANCE_M * 1000:.1f} mm, a quarter inch)")
    errs += material_problems()
    if errs:
        raise StagingError("; ".join(errs))


# ---------------------------------------------------------------- build, render, frame stats, probe
def build(job):
    tpl = templates.TEMPLATES[job["template"]]
    ctx = Ctx(job)
    tpl["fn"](ctx)
    sc = ctx.scene
    g = job["render"]["glare"]
    look.compositor(sc, job["render"]["quality"], ghosts=0.9 if g else 0.0, streaks=0.55 if g else 0.0,
                    bloom=0.7 if g else 0.0, glint_streaks=1.0 if g else 0.0, mist=ctx.mist, nframes=ctx.nframes)
    look.colour(sc, ctx.exposure + float(job["render"].get("exposure", 0.0)))
    ctx.device = look.apply_render(sc, job["render"], job["seed"])
    return ctx, tpl


def frame_stats(path, box=None):
    """Mean and spread of luma (0-255, PIL's L weights) of a rendered PNG, plus the mean inside the subject's screen
    box and outside it, read with bpy + numpy (no PIL in Blender's or the bpy wheel's Python)."""
    import numpy as np
    im = bpy.data.images.load(path, check_existing=False)
    try:
        w, h = im.size
        a = np.empty(w * h * im.channels, dtype=np.float32)
        im.pixels.foreach_get(a)
        a = a.reshape(h, w, im.channels)[::-1]
        lum = (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]) * 255.0
        st = {"mean": round(float(lum.mean()), 2), "std": round(float(lum.std()), 2), "w": w, "h": h}
        gy, gx = h // 16 * 16, w // 9 * 9                 # a 9x16 luma thumbnail: pixel comparisons without PIL
        st["thumb"] = [round(float(v), 1) for v in lum[:gy, :gx].reshape(16, gy // 16, 9, gx // 9).mean(axis=(1, 3)).ravel()]
        if box:
            s = w / W
            x0, y0 = max(0, int(box[0] * s)), max(0, int(box[1] * s))
            x1, y1 = min(w, int(math.ceil(box[2] * s))), min(h, int(math.ceil(box[3] * s)))
            if x1 > x0 and y1 > y0:
                inside = lum[y0:y1, x0:x1]
                st["subject_mean"] = round(float(inside.mean()), 2)
                mask = np.ones_like(lum, dtype=bool)
                mask[y0:y1, x0:x1] = False
                if mask.any():
                    st["backdrop_mean"] = round(float(lum[mask].mean()), 2)
        return st
    finally:
        bpy.data.images.remove(im)


def render_frames(ctx, job, boxes):
    sc = ctx.scene
    out_dir = job["frames_dir"]
    os.makedirs(out_dir, exist_ok=True)
    pattern = job.get("frame_name", "{:04d}.png")
    times, stats = {}, {}
    for k in job["render_frames"]:
        path = os.path.join(out_dir, pattern.format(k))
        if not os.path.exists(path):
            sc.frame_set(k + 1)
            tmp = path[:-4] + ".part.png"
            sc.render.filepath = tmp
            t0 = time.time()
            bpy.ops.render.render(write_still=True)
            dt = time.time() - t0
            os.replace(tmp, path)
            times[str(k)] = round(dt, 2)
            print(f"RX frame {k} {dt:.2f}s -> {path}", flush=True)
        stats[str(k)] = frame_stats(path, boxes[k] if boxes and k < len(boxes) else None)
    return times, stats


def run_job(job):
    _VERTS.clear()
    _BVH.clear()
    t0 = time.time()
    res = {"ok": False, "template": job["template"], "render_s": {}, "errors": [], "blender": blender_info()}
    try:
        ctx, tpl = build(job)
        res["device"] = ctx.device
        res["build_s"] = round(time.time() - t0, 2)
        os.makedirs(os.path.dirname(job["motion_path"]), exist_ok=True)
        rec = dump_motion(ctx, tpl, job["motion_path"])
        res["facts"] = rec["facts"]
        res["motion_s"] = round(time.time() - t0 - res["build_s"], 2)
        if job.get("save_blend"):
            bpy.ops.wm.save_as_mainfile(filepath=job["save_blend"], copy=True)
        res["render_s"], res["frame_stats"] = render_frames(ctx, job, rec["screen"].get("subject"))
        res["ok"] = True
    except StagingError as e:
        res["errors"].append(f"STAGING: {e}")
    except Exception as e:
        res["errors"].append(f"{type(e).__name__}: {e}")
        res["traceback"] = traceback.format_exc()
    res["total_s"] = round(time.time() - t0, 2)
    if job.get("result_path"):
        os.makedirs(os.path.dirname(job["result_path"]), exist_ok=True)
        with open(job["result_path"] + ".tmp", "w") as f:
            json.dump(res, f, indent=1, sort_keys=True)
        os.replace(job["result_path"] + ".tmp", job["result_path"])
    for e in res["errors"]:
        print("RX ERROR", e, flush=True)
    return res


def probe():
    info = {**blender_info(), "python": sys.version.split()[0], "gpu": {}}
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for t in look.GPU_TYPES:
            try:
                prefs.compute_device_type = t
                try:
                    prefs.refresh_devices()
                except Exception:
                    prefs.get_devices()
                devs = [d.name for d in prefs.devices if d.type == t]
                if devs:
                    info["gpu"][t] = devs
            except Exception:
                pass
    except Exception as e:
        info["gpu_error"] = str(e)
    print("RXPROBE " + json.dumps(info), flush=True)


def eevee_probe(out):
    """A 16x16 Eevee render (a missing EGL aborts the process: the driver runs this in its own subprocess), then
    a timed 64x64 one with the shaders compiled. Reports the GL renderer when Blender exposes it, so a software
    rasterizer (llvmpipe, SwiftShader ...) is not mistaken for a GPU."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    bpy.ops.mesh.primitive_cube_add()
    cam = bpy.data.objects.new("c", bpy.data.cameras.new("c"))
    sc.collection.objects.link(cam)
    cam.location = (0, -5, 0)
    cam.rotation_euler = (math.pi / 2, 0, 0)
    sc.camera = cam
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x = sc.render.resolution_y = 16
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    sc.render.resolution_x = sc.render.resolution_y = 64
    sc.eevee.taa_render_samples = 16
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    info = {"second_render_s": round(time.time() - t0, 3), "renderer": None, "vendor": None}
    try:
        import gpu
        info["renderer"] = gpu.platform.renderer_get()
        info["vendor"] = gpu.platform.vendor_get()
    except Exception as e:
        info["renderer_error"] = f"{type(e).__name__}: {e}"
    for k in ("LIBGL_ALWAYS_SOFTWARE", "GALLIUM_DRIVER", "MESA_LOADER_DRIVER_OVERRIDE"):
        if os.environ.get(k):
            info.setdefault("env", {})[k] = os.environ[k]
    print("RXEEVEE ok " + json.dumps(info), flush=True)


def export_proxy(name, out, yaw_deg, scale):
    """Test fixture: a proxy written as a GLB the way another tool might (front turned to yaw_deg, wrong units),
    so the selftest can file it with `model add` and check the normalization on import."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sub = proxies.add_proxy(name, proxies.HEIGHTS[name], bpy.context.scene.collection)
    sub.place.rotation_euler = (0, 0, math.radians(yaw_deg))
    sub.place.scale = (scale, scale, scale)
    bpy.context.view_layer.update()
    bpy.ops.export_scene.gltf(filepath=out, export_format="GLB")
    print("RXEXPORT ok", out, flush=True)


def swatch(out_dir):
    """Emitter calibration: the laser (look.beam) and the fireball (look.fire) under AgX - Punchy, as a template
    renders them. Writes swatch.png and swatch.json with the sRGB saturation of the laser's sheath and of the
    fire's mid tones; the selftest fails when either drops under 0.6 (salmon-pink lasers, peach fire)."""
    import numpy as np
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.device = "CPU"
    s.cycles.samples = 16
    s.cycles.use_denoising = False
    s.render.resolution_x, s.render.resolution_y = 240, 240
    s.render.resolution_percentage = 100
    look.world(s, "#0E0A1E", "#0E0A1E", 1.0)
    cd = bpy.data.cameras.new("c")
    cd.type = "ORTHO"
    cd.ortho_scale = 4.0
    cam = bpy.data.objects.new("c", cd)
    s.collection.objects.link(cam)
    s.camera = cam
    cam.location = (0, -6, 0)
    cam.rotation_euler = (math.pi / 2, 0, 0)
    from . import geo
    b = geo.Builder()
    b.cyl(look.beam("laser", look.PAL["laser"]), (-2.5, 0, 1.0), 0.4, 5.0, rot=(0, math.radians(90), 0), seg=48)
    b.to_object("laser", s.collection)
    fb = geo.Builder()
    fb.ico(look.fire("fire"), (0, 0, -0.8), 1.0, subdiv=4)
    fb.to_object("fire", s.collection)
    look.colour(s)
    path = os.path.join(out_dir, "swatch.png")
    s.render.filepath = path
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(path)
    w, h = im.size
    a = np.empty(w * h * im.channels, dtype=np.float32)
    im.pixels.foreach_get(a)
    a = a.reshape(h, w, im.channels)[::-1][..., :3] * 255.0

    def sat(px):
        mx, mn = px.max(axis=-1), px.min(axis=-1)
        return np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    px_per_m = w / 4.0
    yc = int(round(h / 2 - 1.0 * px_per_m))
    r = 0.4 * px_per_m
    cols = slice(int(w * 0.2), int(w * 0.8))
    sheath_rows = [y for y in range(h) if 0.55 * r <= abs(y - yc) <= 0.85 * r]
    core_rows = [y for y in range(h) if abs(y - yc) <= 0.12 * r]
    sheath = a[sheath_rows, cols].reshape(-1, 3)
    core = a[core_rows, cols].reshape(-1, 3)
    fyc, fr = int(round(h / 2 + 0.8 * px_per_m)), 1.0 * px_per_m
    yy, xx = np.mgrid[0:h, 0:w]
    disc = (yy - fyc) ** 2 + (xx - w / 2) ** 2 <= (0.9 * fr) ** 2
    fire_px = a[disc]
    lum = 0.299 * fire_px[:, 0] + 0.587 * fire_px[:, 1] + 0.114 * fire_px[:, 2]
    mid = fire_px[(lum > 40) & (lum < 200)]
    res = {"laser_sheath_rgb": [round(float(v)) for v in np.median(sheath, axis=0)],
           "laser_sheath_sat": round(float(np.median(sat(sheath))), 3),
           "laser_core_luma": round(float((core @ np.array([0.299, 0.587, 0.114])).mean()), 1),
           "laser_sheath_luma": round(float((sheath @ np.array([0.299, 0.587, 0.114])).mean()), 1),
           "fire_mid_rgb": [round(float(v)) for v in np.median(mid, axis=0)] if len(mid) else None,
           "fire_mid_sat": round(float(np.median(sat(mid))), 3) if len(mid) else 0.0,
           "fire_mid_share": round(float(len(mid) / max(1, len(fire_px))), 3),
           "fire_core_luma": round(float(lum.max()), 1)}
    with open(os.path.join(out_dir, "swatch.json"), "w") as f:
        json.dump(res, f, indent=1, sort_keys=True)
    print("RXSWATCH " + json.dumps(res), flush=True)


def main(argv):
    if "--worker-export-proxy" in argv:
        i = argv.index("--worker-export-proxy")
        export_proxy(argv[i + 1], argv[i + 2], float(argv[i + 3]), float(argv[i + 4]))
        return 0
    if "--worker-probe" in argv:
        probe()
        return 0
    if "--worker-eevee-probe" in argv:
        eevee_probe(argv[argv.index("--worker-eevee-probe") + 1])
        return 0
    if "--worker-swatch" in argv:
        swatch(argv[argv.index("--worker-swatch") + 1])
        return 0
    path = argv[argv.index("--worker") + 1]
    with open(path) as f:
        spec = json.load(f)
    jobs = spec["jobs"] if "jobs" in spec else [spec]
    ok = True
    for job in jobs:
        res = run_job(job)
        ok = ok and (res["ok"] or job.get("expect_error"))
    return 0 if ok else 1
