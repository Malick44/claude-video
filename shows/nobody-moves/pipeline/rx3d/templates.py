"""Reenactment templates: `heist`, `action`, `showcase` (CLI only) and the `@template` registry (docs/BLENDER_REENACTMENTS.md §5).

The registry, the camera presets and the camera solver are plain Python, so the driver imports this module
without Blender. Each builder imports bpy (through geo/look/proxies) only when it runs inside the worker.

Rules every episode template follows (the worker asserts them after building, docs/BLENDER_REENACTMENTS.md §5.1):
  * randomness only from ctx.rng (seeded); no timestamps;
  * motion sampled in Python, one sample per clip frame, keyed on every frame (ctx.key_rigid);
  * rigid only: a subject's root gets location keys and, for a rock or a tip, X/Y rotation keys about a
    contact point; its yaw lives on the static place_<name> parent and is never keyed;
  * the camera is never keyed (showcase is the one exception);
  * nothing is written into the picture: label and stamp are burned in by render.py;
  * the top left stays clear: no subject, beam or effect reaches the AI tag zone (job["zones"]["tag"]);
  * the first frame frames the subject where the cut-back still shows it (camera "anchor": "start").
"""
import math

TEMPLATES = {}


def template(name, version, subject, props=(), camera=None, beats=(), optional_beats=(), multi_move=False,
             options=None, cli_only=False, locked_camera=True, yaw_locked=True):
    """beats: required (word or seconds, else a default with a WARN); optional_beats: only when the episode gives
    them. multi_move: `move_on`/`move_at` may be a list (one rock per word: beats move, move2, move3)."""
    def deco(fn):
        TEMPLATES[name] = {"name": name, "version": version, "fn": fn, "subject": subject, "props": tuple(props),
                           "camera": camera, "beats": tuple(beats), "optional_beats": tuple(optional_beats),
                           "multi_move": multi_move, "options": dict(options or {}), "cli_only": cli_only,
                           "locked_camera": locked_camera, "yaw_locked": yaw_locked}
        return fn
    return deco


# Camera presets. The distance and tilt are solved from the subject's real size unless given ("dist", "tilt").
# lens on a vertical-fit 24 mm sensor (35 mm -> 37.8 deg vertical, 21.8 deg horizontal at 9:16).
# start_cx/start_cy: where the subject's FIRST frame is centred (0..1 from the top left), so the hard cut to the
# real still matches it (docs/BLENDER_REENACTMENTS.md §6, "the cut-back matches the reenactment's first frame").
CAMERAS = {
    # grass height, where Deb stands: the locked lens IS her point of view. He fills `fill` of the frame height
    # with his cap tip `top_at` down the frame (g_deny: cap 0.224, boots 0.932, centre x 0.515)
    "beside_deb": {"lens": 35.0, "height": 0.08, "fill": 0.68, "top_at": 0.25, "fstop": 2.8, "pan": 0.0,
                   "anchor": "start", "start_cx": 0.51, "start_cy": None},
    # low on the front walk; the start pose is anchored where l_deny shows the real goose, and the camera dollies
    # back until the whole move stays inside x 0.04-0.96
    "hero_low": {"lens": 35.0, "height": 0.30, "fill": 0.50, "top_at": None, "fstop": 2.8, "pan": 0.0,
                 "anchor": "start", "start_cx": 0.59, "start_cy": 0.55},
    # showcase: the figurine on the grey sheet ground at its mid height
    "sheet": {"lens": 50.0, "height": None, "fill": 0.80, "top_at": 0.10, "fstop": 8.0, "pan": 0.0,
              "anchor": None, "start_cx": None, "start_cy": None},
}
CAMERA_KEYS = {"preset", "lens", "dist", "height", "tilt", "pan", "fill", "top_at", "fstop", "anchor", "start_cx",
               "start_cy"}
SENSOR_H = 24.0
ASPECT = 9 / 16
INCH = 0.0254
# Every laser is ONE cylinder whose emission strength runs from 1.4 on the sheath to 6.0 in a thin core
# (look.beam): AgX - Punchy keeps 1.4 a saturated red, (212,50,30), and only the core blooms. A flat strength of
# 9 rendered salmon-pink (255,166,157).
LASER_LO, LASER_HI = 1.4, 6.0


# ---------------------------------------------------------------- camera solving (pure math)
def _v(pt, D, th, h, t):
    """Vertical frame coordinate (+1 top, -1 bottom) of point pt=(y, z) seen from (y=-D, z=h), pitched up th."""
    a = math.atan2(pt[1] - h, D + pt[0]) - th
    if abs(a) >= math.pi / 2 - 1e-6:          # behind the image plane: far off the frame on that side
        return math.copysign(1e9, a)
    return math.tan(a) / t


def solve_camera(lens, h, top, bot, v_top, v_bot):
    """Distance D and tilt (rad) so that `top` lands at v_top and `bot` at v_bot. Points are (y, z) with y
    measured from the subject plane, away from the camera. Bisection; the subject shrinks as D grows."""
    t = (SENSOR_H / 2) / lens

    def tilt_for(D):
        return math.atan2(top[1] - h, D + top[0]) - math.atan(v_top * t)

    def f(D):
        return _v(bot, D, tilt_for(D), h, t) - v_bot

    lo, hi = 0.05 - min(top[0], bot[0], 0.0), 60.0
    if f(lo) > 0:
        raise ValueError(f"camera can't frame it: even at {lo:.2f} m the subject is under the requested fill "
                         f"(lens {lens} mm, height {h} m)")
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(mid) > 0:
            hi = mid
        else:
            lo = mid
    D = (lo + hi) / 2
    return D, tilt_for(D)


def solve_union(lens, h, top_a, bot_a, bot_b, fill):
    """Frame a move: pose A fills `fill` of the frame height, and A's top and B's bottom sit symmetric about the
    centre (both poses in frame, centred). Returns (D, tilt)."""
    t = (SENSOR_H / 2) / lens

    def tilt_for(D):
        lo, hi = -1.4, 1.4      # v(top)+v(bot_b) falls as the tilt rises
        for _ in range(100):
            mid = (lo + hi) / 2
            if _v(top_a, D, mid, h, t) + _v(bot_b, D, mid, h, t) > 0:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    def g(D):
        th = tilt_for(D)
        return _v(top_a, D, th, h, t) - _v(bot_a, D, th, h, t) - 2 * fill

    lo, hi = 0.05 - min(top_a[0], bot_a[0], bot_b[0], 0.0), 60.0
    if g(lo) < 0:
        raise ValueError("camera can't frame the move at that fill; lower `fill` or use a shorter lens")
    for _ in range(200):
        mid = (lo + hi) / 2
        if g(mid) > 0:
            lo = mid
        else:
            hi = mid
    D = (lo + hi) / 2
    return D, tilt_for(D)


def smoothstep(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def rect_dist(px, py, rect):
    """Distance (px) from a point to a rectangle [x0, y0, x1, y1]; 0 inside."""
    dx = max(rect[0] - px, 0.0, px - rect[2])
    dy = max(rect[1] - py, 0.0, py - rect[3])
    return math.hypot(dx, dy)


def flicker(rng, n=3):
    """A deterministic flicker in [-1, 1]: a sum of `n` seeded sines (fire, laser hum)."""
    parts = [(rng.uniform(1.3, 4.1), rng.uniform(0, 2 * math.pi)) for _ in range(n)]
    return lambda t: sum(math.sin(2 * math.pi * f * t + p) for f, p in parts) / n


# ---------------------------------------------------------------- shared set pieces (inside Blender)
def _frame_width(ctx, depth):
    return 2 * depth * (SENSOR_H / 2) / ctx.cam_lens * ASPECT


def _camera_only(ob):
    """Cards and sprites are seen by the camera only: no bounce, reflection or shadow ray ever shades them."""
    for attr in ("visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter",
                 "visible_shadow"):
        setattr(ob, attr, False)


def _anchor_start(ctx, cam, meshes, cx, frame=0):
    """Truck the locked camera along its own X so the subject's box on `frame` is centred at `cx` (0..1)."""
    import numpy as np
    from mathutils import Vector
    from . import worker
    for _ in range(4):
        P = ctx._points_per_frame(meshes, [frame])[0]
        R = np.array(cam.rotation_euler.to_matrix())
        q = (P - np.array(cam.location)) @ R
        d = -q[:, 2]
        tv = (SENSOR_H / 2) / cam.data.lens
        th = tv * worker.W / worker.H
        x = q[:, 0] / d / th
        shift = ((x.max() + x.min()) / 2 - (2 * cx - 1)) * th * float(np.median(d))
        cam.location = cam.location + Vector(R[:, 0]) * shift
    ctx.scene.frame_set(1)


def _haze(ctx, cam, depths, strength, slowmo, box=None, hexc=None, density=0.016, drift=3.0):
    """Final: a drifting Principled Volume (box), its density modulated by 4D noise. Preview/draft: compositor mist
    (the Mist pass x a drifting noise, nearly free on a CPU). The drift is `drift` x the old 0.35 x slowmo, so a
    long hold before the move reads as live video, not a still."""
    from . import geo, look
    if ctx.haze == "off" or strength <= 0:
        return
    hexc = hexc or look.PAL["haze"]
    speed = 0.35 * slowmo * drift
    w0 = ctx.rng.uniform(0, 10)
    if ctx.haze == "volume" and box:
        (x0, y0, z0), (x1, y1, z1) = box
        m = look.haze_volume("haze_vol", density * strength, hexc, noise_scale=1.4)
        b = geo.Builder()
        b.box(m, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0))
        ob = b.to_object("haze_volume", ctx.col)
        ob.visible_shadow = False
        nz = m.node_tree.nodes["noise"]
        for k in range(ctx.nframes):
            nz.inputs["W"].default_value = w0 + speed * k / ctx.fps
            nz.inputs["W"].keyframe_insert("default_value", frame=k + 1)
        ctx.mist = {"strength": 0.2 * strength, "start": depths[0] * 0.55, "depth": depths[-1] * 1.6,
                    "w0": w0, "speed": speed, "hex": hexc}
        return
    ctx.mist = {"strength": 0.15 * strength, "start": depths[0] * 0.55, "depth": depths[-1] * 1.6,
                "w0": w0, "speed": speed, "hex": hexc}     # matched to the final's volume + mist (measured luma)


def _godray(ctx, cam, src, target, hexc, energy, angle_deg, strength):
    """A spot through the haze. In final the volume shows the shaft; otherwise an additive cone card does."""
    from mathutils import Vector
    from . import geo, look
    look.spot("godray", src, target, hexc, energy, angle_deg=angle_deg, blend=0.6, collection=ctx.col)
    if ctx.haze in ("off", "volume") or strength <= 0:     # the volume shows the shaft by itself
        return
    d = Vector(target) - Vector(src)
    ln = d.length * 1.1
    r = ln * math.tan(math.radians(angle_deg) / 2)
    m = look.additive("godray_card", hexc, 0.06 * strength, noise=True, facing=True, noise_scale=0.8)   # ~ the final's shaft
    b = geo.Builder()
    b.cone(m, (0, 0, -ln), r, 0.01, ln, seg=32, smooth=True, cap=False)
    ob = b.to_object("godray_cone", ctx.col)
    ob.location = src
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    _camera_only(ob)
    nz = m.node_tree.nodes["noise"]
    for k in range(ctx.nframes):
        nz.inputs["W"].default_value = 0.15 * k / ctx.fps
        nz.inputs["W"].keyframe_insert("default_value", frame=k + 1)


def _siding(name, P):
    """Vinyl siding in the template's palette: horizontal bands, a little gloss."""
    from . import look
    m = look.plastic(name, P["siding"], rough=0.45, coat=0.2)
    N, L = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    wave = N.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "Z"
    wave.wave_profile = "SAW"
    wave.inputs["Scale"].default_value = 3.2
    L.new(tc.outputs["Object"], wave.inputs["Vector"])
    mix = N.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = look.rgba(P["siding_band"])
    mix.inputs[7].default_value = look.rgba(P["siding"])
    L.new(wave.outputs["Factor"], mix.inputs[0])
    L.new(mix.outputs[2], b.inputs["Base Color"])
    return m


def _echinacea(ctx, spots):
    """Proxy echinacea: green stem, ring of drooping magenta petals, orange-brown cone. One object."""
    from . import geo, look
    stem = look.matte("echi_stem", look.PAL["stem"], 0.5)
    petal = look.plastic("echi_petal", look.PAL["petal"], rough=0.35, coat=0.6)
    cone = look.matte("echi_cone", look.PAL["cone"], 0.7, noise_hex="#5A2A10", noise_scale=300)
    leaf = look.matte("echi_leaf", "#2E7D32", 0.5)
    b = geo.Builder()
    for (x, y, hgt) in spots:
        tilt = ctx.rng.uniform(-0.12, 0.12)
        top = (x + math.sin(tilt) * hgt, y, hgt)
        b.tube(stem, [(x, y, 0), ((x + top[0]) / 2, y, hgt / 2), top], [0.004, 0.0035, 0.003], seg=8)
        b.sphere(cone, top, 0.018, scale=(1, 1, 0.8), seg=(16, 8))
        n = 12
        a0 = ctx.rng.uniform(0, math.pi)
        for i in range(n):
            a = a0 + 2 * math.pi * i / n
            c = (top[0] + 0.035 * math.cos(a), top[1] + 0.035 * math.sin(a), top[2] - 0.012)
            b.sphere(petal, c, 1.0, scale=(0.032, 0.009, 0.0025), rot=(0, math.radians(28), a), seg=(10, 6))
        for s in (-1, 1):
            b.sphere(leaf, (x + s * 0.03, y, hgt * 0.35), 1.0, scale=(0.045, 0.012, 0.004),
                     rot=(0, s * math.radians(-30), ctx.rng.uniform(-0.5, 0.5)), seg=(10, 6))
    return b.to_object("echinacea", ctx.col)


def _house(ctx, P, x0, x1, y, z_roof, door=None, windows=(), lantern=None):
    """The house as a set flat: siding wall, fascia (the roofline), roof slope, a black door, dark windows,
    a brass lantern sconce (the one emissive light at window height). Every window is dark, and the door and
    windows are rough and uncoated (look.dark), so no light's reflection reads as a light inside the house."""
    from . import geo, look
    wall = _siding("siding", P)
    trim = look.plastic("trim", look.PAL["trim"], rough=0.3)
    roof = look.matte("roof", "#2B2733", 0.6)
    win = look.dark("window_dark", look.PAL["window"], rough=0.5)
    blk = look.dark("door_black", look.PAL["door"], rough=0.55)
    b = geo.Builder()
    b.box(wall, ((x0 + x1) / 2, y + 0.05, z_roof / 2), (x1 - x0, 0.1, z_roof))
    fascia = look.plastic("fascia", P["fascia"], rough=0.35) if P.get("fascia") else trim
    b.box(fascia, ((x0 + x1) / 2, y - 0.04, z_roof - 0.06), (x1 - x0, 0.06, 0.16))
    b.box(roof, ((x0 + x1) / 2, y + 1.6, z_roof + 0.55), (x1 - x0, 3.4, 0.08), rot=(math.radians(18), 0, 0))
    if door:
        dx, dz0, dw, dh = door
        b.box(trim, (dx, y - 0.01, dz0 + dh / 2 + 0.03), (dw + 0.14, 0.04, dh + 0.1))
        b.box(blk, (dx, y - 0.04, dz0 + dh / 2), (dw, 0.05, dh))
        b.sphere(look.plastic("door_knob", look.PAL["brass"], metal=1.0, rough=0.2), (dx + dw * 0.38, y - 0.08, dz0 + 1.0),
                 0.03)
    for (wx, wz, ww, wh) in windows:
        b.box(trim, (wx, y - 0.01, wz), (ww + 0.12, 0.04, wh + 0.12))
        b.box(win, (wx, y - 0.04, wz), (ww, 0.04, wh))
        b.box(trim, (wx, y - 0.06, wz), (0.03, 0.02, wh))
    ob = b.to_object("house", ctx.col)
    if lantern:
        lx, lz = lantern
        brass = look.plastic("lantern_brass", look.PAL["brass"], metal=1.0, rough=0.25)
        glow = look.emissive("lantern_glow", look.PAL["lantern"], 6.0)
        lb = geo.Builder()
        lb.box(brass, (lx, y - 0.08, lz + 0.16), (0.16, 0.16, 0.03))
        lb.box(glow, (lx, y - 0.08, lz), (0.11, 0.11, 0.24))
        lb.box(brass, (lx, y - 0.08, lz - 0.14), (0.14, 0.14, 0.03))
        lb.to_object("lantern", ctx.col)
        look.point("lantern_light", (lx, y - 0.25, lz), look.PAL["lantern"], 6.0, collection=ctx.col)
    return ob


def _moon(ctx, cam, sx, sy, depth, frac, hexc, strength):
    from . import geo, look
    m = look.emissive("moon", hexc, strength)
    r = frac * 2 * depth * (SENSOR_H / 2) / ctx.cam_lens
    b = geo.Builder()
    b.disc(m, (0, 0, 0), r, seg=64)
    ob = b.to_object("moon", ctx.col)
    ob.location = ctx.screen_point(cam, sx, sy, depth)
    ob.rotation_euler = cam.rotation_euler
    return ob


def _lawn(ctx, P):
    from . import geo, look
    m = look.matte("lawn", P["lawn"], 0.95, noise_hex=P["lawn_noise"], noise_scale=25, spec=0.05)
    b = geo.Builder()
    b.quad(m, (0, 0, 0), (40, 40))
    return b.to_object("lawn", ctx.col)


def _on_plane_y(ctx, cam, sx, sy, y):
    """World point where the ray through screen (sx, sy) (0..1 from the top left) meets the plane Y = y."""
    p0 = ctx.screen_point(cam, sx, sy, 0.5)
    p1 = ctx.screen_point(cam, sx, sy, 5.0)
    u = (y - p0.y) / (p1.y - p0.y)
    return p0 + u * (p1 - p0)


def _line_hits_zone(ctx, cam, centre, direction, half_len, zone, n=200):
    """Does a straight beam, seen from `cam`, cross the screen rectangle `zone` (px)?"""
    from mathutils import Vector
    if not zone:
        return False
    c, d = Vector(centre), Vector(direction).normalized()
    for i in range(n + 1):
        p = c + d * (-half_len + 2 * half_len * i / n)
        x, y, dep = ctx.to_screen(cam, p)
        if dep > 0.05 and zone[0] <= x <= zone[2] and zone[1] <= y <= zone[3]:
            return True
    return False


# ---------------------------------------------------------------- heist
@template("heist", version=2, subject="garrison", props=(), camera="beside_deb", beats=("move",),
          optional_beats=("flare",),
          options={"path": "left", "toward": 0.0, "travel": 0.25, "accel_s": 0.35, "beams": 7,
                   "beam_hex": "#FF1A1A", "clearance_in": 1.5, "clearance_end_in": 0.30, "front_beams": True,
                   "glint": True, "glint_strength": 150.0, "haze": 0.5, "slowmo": 0.5, "fill": 0.68,
                   "top_at": 0.25, "fstop": 2.8, "start_cx": 0.51, "kicker": True, "sweat_mm": 6.0})
def heist(ctx):
    """Garrison dead still in a red laser grid, then a rigid ease-in glide across the frame, cut mid-glide.
    The locked lens is Deb's point of view (she is not in the frame: from grass height her head can't be)."""
    from mathutils import Matrix, Vector
    from . import geo, look
    o, rng, fps = ctx.opts, ctx.rng, ctx.fps
    P = look.palette("heist")
    look.world(ctx.scene, P["sky_lo"], P["sky_hi"], 0.9)
    g = ctx.subject()
    H = g.height
    lo, hi = g.local_bbox()
    c = ctx.cam_spec
    zone = ctx.zones.get("tag")
    if c.get("dist") and c.get("tilt") is not None:
        D, tilt = float(c["dist"]), math.radians(float(c["tilt"]))
    else:
        v_top = 1 - 2 * c["top_at"]
        D, tilt = solve_camera(c["lens"], c["height"], (0.0, H), (float(lo[1]), 0.0), v_top, v_top - 2 * c["fill"])
    focus = geo.empty("focus", parent=g.root, loc=(0, float(lo[1]) * 0.6, 0.55 * H), collection=ctx.col)
    cam = ctx.make_camera((0.0, -D, c["height"]), tilt, c.get("pan", 0.0), focus)
    if c.get("anchor") == "start" and c.get("start_cx") is not None:
        _anchor_start(ctx, cam, g.meshes, float(c["start_cx"]))
    ctx.fact("camera_solved", {"dist": round(D, 4), "tilt_deg": round(math.degrees(tilt), 3),
                               "x": round(cam.location.x, 4)})

    # --- motion: still until move, then an ease-in glide; no ease-out (the cut lands mid-glide)
    t_move = ctx.beat_t("move")
    T_end = ctx.last_shown / fps - t_move
    width = _frame_width(ctx, D)
    travel = o["travel"] * width
    acc = o["accel_s"]
    if T_end <= 0:
        raise RuntimeError("heist: the move comes after the last frame")
    if T_end <= acc:
        a = 2 * travel / T_end ** 2
    else:
        a = travel / (acc * (T_end - acc / 2))

    def s_of(t):
        if t <= 0:
            return 0.0
        if t < acc:
            return 0.5 * a * t * t
        return 0.5 * a * acc * acc + a * acc * (t - acc)

    sgn = -1.0 if o["path"] == "left" else 1.0
    path = []
    for k in range(ctx.nframes):
        s = s_of(k / fps - t_move)
        loc = (sgn * s, -o["toward"] * s, 0.0)
        path.append(loc)
        ctx.key_rigid(g.root, k, loc)
    ctx.fact("travel_m", round(travel, 4))
    ctx.fact("speed_frame_widths_per_s", round(a * acc / width, 3))
    xs = [p[0] for p in path]
    xmin, xmax = min(xs) + float(lo[0]), max(xs) + float(hi[0])
    x_cut = sgn * s_of(ctx.last_shown / fps - t_move)

    # --- set: lawn, flower bed, echinacea, the house flat, sky and moon
    _lawn(ctx, P)
    soil = look.matte("soil", look.PAL["soil"], 0.95, noise_hex="#1A0F08", noise_scale=60, spec=0.05)
    sb = geo.Builder()                     # the bed is behind him: the lawn runs from his boots to the lens
    sb.cyl(soil, (sgn * travel / 2, 0.45, -0.004), 0.6, 0.01, seg=64, scale=(1.8, 1, 1))
    sb.to_object("flower_bed", ctx.col)
    spots = []
    tries = 0
    n_fl = rng.randint(8, 12)
    while len(spots) < n_fl and tries < 500:
        tries += 1
        x = rng.uniform(-0.75, 0.55)
        y = rng.uniform(-0.05, 0.9)
        if xmin - 0.08 < x < xmax + 0.08 and y < 0.22:      # keep his glide corridor clear
            continue
        if y < 0.05 and abs(x) < 0.35:                       # nothing in front of him
            continue
        if any((x - a_) ** 2 + (y - b_) ** 2 < 0.12 ** 2 for a_, b_, _ in spots):
            continue
        spots.append((x, y, rng.uniform(0.22, 0.42)))
    _echinacea(ctx, spots)
    yw = 5.2
    roof = _on_plane_y(ctx, cam, 0.5, 0.15, yw - 0.04).z         # the roofline 15% down the frame: sky above it
    _house(ctx, P, -6, 6, yw, roof, door=(1.0, 0.25, 0.95, min(2.1, roof - 0.5)),
           windows=((-0.9, min(1.55, roof - 1.0), 0.9, 1.0), (2.6, min(1.55, roof - 1.0), 0.9, 1.0)),
           lantern=(1.75, min(1.75, roof - 0.7)))
    _moon(ctx, cam, 0.68, 0.075, 40.0, 0.06, P["moon"], 1.6)

    # --- Deb (only if an episode asks for her as a prop): static, facing frame left. The template no longer adds
    # her by default: at grass height her head is ~34 cm above the frame, so only two pink blobs showed.
    if "deb" in ctx.props:
        deb = ctx.prop("deb")
        hd = deb.height
        deb.place.rotation_euler = (0, 0, math.radians(-90))
        z_body = 0.52 * hd
        p_near = ctx.screen_point(cam, 0.80, 0.06, 0.2)
        p_far = ctx.screen_point(cam, 0.80, 0.06, 2.0)
        u = (z_body - p_near.z) / (p_far.z - p_near.z)
        breast = p_near + u * (p_far - p_near)
        deb.place.location = (breast.x + 0.195 * hd, breast.y, 0.0)
        ctx.fact("deb_depth_m", round(breast.y + D, 3))

    # --- laser grid. The low beam crosses over his cap and DESCENDS toward his travel: clearance_in (1.5 in) over
    # the cap tip at the start, clearance_end_in (0.30 in) at the cut, so the cut lands just before contact.
    beam_r = 0.0025
    lm = look.beam("laser", o["beam_hex"], LASER_LO, LASER_HI)
    c0, c1 = o["clearance_in"] * INCH, o["clearance_end_in"] * INCH
    slope = (c1 - c0) / x_cut if abs(x_cut) > 1e-6 else 0.0          # dz/dx along his path
    a_low = math.radians(rng.uniform(-4, 4))                          # nearly square to the lens
    phi = math.atan(slope)
    low_dir = Vector((math.cos(a_low) * math.cos(phi), math.sin(a_low) * math.cos(phi), math.sin(phi)))
    low_c = Vector((0.0, 0.0, H + c0 + beam_r))

    def low_z(x):
        return low_c.z + slope * x

    def beam(name, center, direction, length=5.0):
        b = geo.Builder()
        b.cyl(lm, (-length / 2, 0, 0), beam_r, length, rot=(0, math.radians(90), 0), seg=10)
        ob = b.to_object(name, ctx.col)
        d = Vector(direction).normalized()
        ob.matrix_world = Matrix.Translation(Vector(center)) @ Vector((1, 0, 0)).rotation_difference(d).to_matrix().to_4x4()
        ob.visible_shadow = False
        ctx.beam(name, center, d, length / 2, beam_r)
        ctx.track(f"beam:{name}", [ob])
        return ob

    def clear_beam(name, make, tries=24):
        """Draw seeded beams until one stays out of the AI tag zone (the top left is kept clear)."""
        for _ in range(tries):
            center, direction, length = make()
            if not _line_hits_zone(ctx, cam, center, direction, length / 2, zone):
                return beam(name, center, direction, length)
        ctx.fact(f"{name}_skipped", "every draw crossed the tag zone")
        return None

    beam("laser_low", low_c, low_dir)
    ctx.fact("low_beam_deg", round(math.degrees(phi), 2))
    ctx.fact("low_beam_clearance_in", [o["clearance_in"], o["clearance_end_in"]])
    ctx.fact("cap_tip_z_m", round(H, 5))
    n_mid = min(2, max(0, o["beams"] - 1))
    for i in range(n_mid):
        def mk():
            b_ang = math.radians(rng.uniform(10, 25)) * (1 if rng.random() < 0.5 else -1)
            reach = max(abs(xmin), abs(xmax)) + 0.25
            z0 = low_z(0) + 0.03 + reach * math.tan(abs(b_ang) + abs(phi)) + rng.uniform(0.02, 0.15)
            return (0, rng.uniform(0.02, 0.12), z0), (math.cos(b_ang), 0, math.sin(b_ang)), 5.0
        clear_beam(f"laser_mid{i}", mk)
    # the flare: on the `flare` beat (peak 2 frames after the word's onset), else 60% of the glide; at the point of
    # the low beam right above his cap tip, where a back beam crosses it on screen
    if ctx.has_beat("flare"):
        k_g = min(ctx.beat_frame("flare") + 2, ctx.last_shown - 2)
    else:
        t_g = t_move + max(0.4, min(0.6 * T_end, T_end - 0.2))
        k_g = min(int(round(t_g * fps)), ctx.last_shown - 3)
    cap_x = sgn * s_of(k_g / fps - t_move)
    Pg = Vector((cap_x, cap_x * math.tan(a_low), low_z(cap_x)))
    C = cam.location.copy()
    n_back = max(0, o["beams"] - 1 - n_mid - (2 if o["front_beams"] else 0))
    for i in range(n_back):
        def mk(i=i):
            yb = rng.uniform(0.45, 1.3)
            ang = math.radians(rng.uniform(12, 25)) * (1 if i % 2 == 0 else -1)
            if i == 0:
                s = (yb - C.y) / (Pg.y - C.y)
                Q = C + s * (Pg - C)
            else:
                Q = Vector((rng.uniform(-0.3, 0.3), yb, rng.uniform(0.05, 0.75)))
            return Q, (math.cos(ang), 0, math.sin(ang)), 7.0
        clear_beam(f"laser_back{i}", mk)
    if o["front_beams"]:   # sandwich him in the grid: one at boot height, one across the upper right, ~0.3 m in front
        yf = -0.30
        beam("laser_front_low", (0.0, yf, 0.03), (math.cos(math.radians(4)), 0.0, math.sin(math.radians(4))))
        pa, pb = _on_plane_y(ctx, cam, 1.04, 0.40, yf), _on_plane_y(ctx, cam, 0.70, -0.04, yf)
        clear_beam("laser_front_high", lambda: ((pa + pb) / 2, pb - pa, 3.0))
    hum = flicker(rng, 2)
    sn = lm.node_tree.nodes["strength"]
    for k in range(ctx.nframes):   # the hum: +-12% at 2 Hz (not slowed: it tells a phone viewer this is video)
        t = k / fps
        sn.outputs[0].default_value = 1.0 + 0.12 * (0.7 * math.sin(2 * math.pi * 2.0 * t) + 0.3 * hum(t))
        sn.outputs[0].keyframe_insert("default_value", frame=k + 1)
    if o["glint"]:
        gm = look.emissive("glint", "#FFE9E0", 0.0, aov="glint")       # opaque: Eevee keeps it in the passes
        # a horizontal sliver and a dot: the anamorphic streak turns them into a line (a vertical bar streaked
        # sideways rendered as a white box at final quality)
        b = geo.Builder()
        b.quad(gm, (0, 0, 0), (0.05, 0.0016))
        b.sphere(gm, (0, 0, 0), 0.0035, seg=(10, 6))
        gob = b.to_object("glint", ctx.col)
        gob.location = Pg
        gob.rotation_euler = cam.rotation_euler
        _camera_only(gob)
        spike = {k_g - 3: 0.1, k_g - 2: 0.35, k_g - 1: 0.8, k_g: 1.0, k_g + 1: 0.55, k_g + 2: 0.2}
        sn = gm.node_tree.nodes["strength"]
        for k in range(ctx.nframes):
            v = spike.get(k, 0.0)
            sn.outputs[0].default_value = o["glint_strength"] * v
            sn.outputs[0].keyframe_insert("default_value", frame=k + 1)
            s = 1.0 if v > 0 else 0.0                                  # hidden by scale, not by transparency
            gob.scale = (s, s, s)
            gob.keyframe_insert("scale", frame=k + 1)
        ctx.fact("glint_frame", k_g)
    if "nose" in g.anchors and o["sweat_mm"]:   # a single painted bead of sweat on his nose, big enough to see
        nx, ny, nz = g.anchors["nose"]
        r = o["sweat_mm"] / 1000
        bb = geo.Builder()
        bb.sphere(look.glass("sweat"), (nx + 0.008, ny + 0.002, nz + 0.012), r, seg=(16, 8))
        bb.to_object("sweat_bead", ctx.col, parent=g.root)

    # --- lights: warm key, magenta/cyan gel rims raking the cap edge and the bell, top spot, a low fill, the set flood,
    # the god-ray; a pink kicker from frame right (Deb, off screen); a tiny eye light at the lens for catchlights.
    # The subject's lights are linked to him alone, so the set stays dark (backdrop 60-80) and he carries the frame.
    tgt = (0, 0, 0.5 * H)
    him = list(g.meshes) + [o for o in ctx.col.objects if o.name == "sweat_bead"]
    look.link(look.area("key", (0.55, -0.75, 0.75), tgt, look.PAL["key"], 150, size=0.6, collection=ctx.col), him)
    look.area("fill", (-0.7, -0.9, 0.35), tgt, P["fill"], 8, size=1.0, collection=ctx.col)
    look.link(look.area("rim_m", (-0.45, 0.35, 0.75), (0, 0, 0.6 * H), look.PAL["rim_m"], 220, size=0.12,
                        collection=ctx.col), him)
    look.link(look.area("rim_c", (0.45, 0.35, 0.75), (0, 0, 0.6 * H), look.PAL["rim_c"], 220, size=0.12,
                        collection=ctx.col), him)
    look.link(look.spot("top", (0.0, 0.05, 1.5), (0, 0, 0.3), "#F3EEFF", 250, angle_deg=22, collection=ctx.col), him)
    look.area("set_flood", (0.0, 2.5, 3.5), (0, yw, 1.5), P["set_flood"], 110, size=3.0, collection=ctx.col, glossy=False)
    if o["kicker"]:
        look.link(look.area("kicker_deb", (0.5, -0.5, 0.45), (0, 0, 0.62 * H), P["kicker"], 40, size=0.3,
                            collection=ctx.col), him)
    eye = look.area("eye_light", tuple(cam.location + Vector((0, 0.02, 0.03))), (0, 0, 0.59 * H), "#FFFFFF", 3,
                    size=0.05, collection=ctx.col)
    eye.visible_diffuse = False                     # catchlights only: it adds no fill
    look.link(eye, him)
    _godray(ctx, cam, (1.1, 1.8, 2.4), (-0.15, 0.1, 0.0), "#E3D9FF", 450, 14, o["haze"])
    _haze(ctx, cam, (D + 0.5, D + 1.8, D + 3.6), o["haze"], o["slowmo"],
          box=((-3, -0.45, -0.01), (3, yw - 0.1, 3.2)), hexc=P["haze"], density=0.016, drift=3.0)
    ctx.mover(g)
    ctx.track("subject", g.meshes)
    ctx.keep_clear = ["subject"] + [k for k in ctx.tracks if k.startswith("beam:")]
    ctx.exposure = 1.0          # measured on the final (volume haze): subject ~140, backdrop 60-80, mid-frame ~95


# ---------------------------------------------------------------- action
@template("action", version=2, subject="lorraine", props=(), camera="hero_low", beats=("move", "land"),
          optional_beats=("tip",), multi_move=True,
          options={"steps_down": 1, "rocks": "auto", "roll_deg": 10.0, "pitch_deg": 12.0, "step_len": 0.025,
                   "tip_s": 0.20, "rock_max_s": 0.5, "slowmo": 0.29, "land_depth": 0.06, "sparks": 60,
                   "embers": 24, "dust": 40, "chime": True, "outfit": None, "fill": 0.50, "fstop": 2.8,
                   "haze": 0.5, "facing_deg": 50.0, "allow_facing": None, "start_cx": 0.59, "start_cy": 0.55,
                   "fire_at": [0.82, 0.31], "fire_r": [0.10, 0.20], "fire_burst": 1.25})
def action(ctx):
    """Lorraine still on the porch's top step, a stage fireball swelling behind the roofline (an action poster:
    she faces left, walking away from the explosion). She rock-waddles on the rock words (rigid rolls about her
    feet), tips on the tip word, dives one step in slow motion and lands after the word with a thud, a low dust
    puff and a second boom. Yaw constant: three-quarter, beak to frame left."""
    from mathutils import Matrix, Vector
    from . import geo, look, proxies
    o, rng, fps = ctx.opts, ctx.rng, ctx.fps
    P = look.palette("action")
    look.world(ctx.scene, P["sky_lo"], P["sky_hi"], 1.0)
    rise, run, n_steps, width = 0.18, 0.28, 3, 1.6
    top_z = rise * n_steps
    drop = rise * o["steps_down"]
    sub = ctx.subject(outfit=o["outfit"])
    H = sub.height
    foot = sub.foot
    th = math.radians(o["facing_deg"])
    front = Vector((-math.cos(th), -math.sin(th), 0.0))       # beak to frame left, three-quarter to camera
    yaw = math.atan2(-math.cos(th), math.sin(th))
    ctx.fact("yaw_deg", round(math.degrees(yaw), 3))

    # --- timing. Rocks start on the rock words (move, move2 ...); the tip starts on `tip` (or is derived from the
    # slow-motion fall); the dive runs from the end of the tip to `land`.
    t_land = ctx.beat_t("land")
    rock_starts = [ctx.beat_t(n) for n in ("move", "move2", "move3") if ctx.has_beat(n)]
    slow_g = 9.81 * o["slowmo"] ** 2
    T_tip = float(o["tip_s"])
    if ctx.has_beat("tip"):
        t_tip = ctx.beat_t("tip")
        t_fall = t_tip + T_tip
        T_fall = t_land - t_fall
    else:
        T_fall = math.sqrt(2 * drop / slow_g)
        t_fall = t_land - T_fall
        t_tip = t_fall - T_tip
        if t_tip < rock_starts[0] + 0.05:              # compress: squeeze tip and fall into the window
            k_ = (t_land - rock_starts[0] - 0.05) / (T_fall + T_tip)
            T_fall, T_tip = T_fall * k_, T_tip * k_
            t_fall, t_tip = t_land - T_fall, t_land - T_fall - T_tip
    if T_fall < 0.15:
        raise RuntimeError(f"action: the fall is {T_fall:.2f} s (tip at {t_tip:.2f} s, land at {t_land:.2f} s); give "
                           f"it 0.15 s or more")
    rocks = []                                          # (start, duration)
    if len(rock_starts) > 1 or o["rocks"] == "words":
        ends = rock_starts[1:] + [t_tip]
        for s0, e0 in zip(rock_starts, ends):
            d = min(e0 - s0, o["rock_max_s"])
            if d >= 0.15:
                rocks.append((s0, d))
    else:
        w = t_tip - rock_starts[0]
        n = (0 if w < 0.3 else max(1, min(3, int(round(w / 0.6))))) if o["rocks"] in ("auto", "words") \
            else (int(o["rocks"]) if w >= 0.15 * int(o["rocks"]) else 0)
        rocks = [(rock_starts[0] + i * w / n, w / n) for i in range(n)] if n else []
    n_rocks = len(rocks)
    ctx.fact("phases", {"rocks": [[round(a_, 3), round(b_, 3)] for a_, b_ in rocks], "t_tip": round(t_tip, 3),
                        "tip_s": round(T_tip, 3), "t_fall": round(t_fall, 3), "fall_s": round(T_fall, 3),
                        "t_land": round(t_land, 3), "slowmo_implied": round(math.sqrt(2 * drop / 9.81) / T_fall, 3)})

    hw, fr = foot["half_width"] * 0.85, foot["front"]
    step = o["step_len"]
    adv = n_rocks * step
    pitch = math.radians(o["pitch_deg"])
    settle_f = 4                                        # frames to come back level before the landing

    def make_local(B0, d_fall, ease):
        def local(t):
            """(location, rotation_euler) of subj_ in the place frame (front = -Y) at clip time t."""
            q = Vector((0, 0, 0))
            d = Vector((0, 0, 0))
            rx = ry = 0.0
            if t <= rock_starts[0] or (n_rocks and t <= rocks[0][0]):
                pass
            elif t < t_tip:                                            # rock-waddle, holds between rocks
                done = 0
                for i, (s0, dur_) in enumerate(rocks):
                    if t < s0:
                        break
                    u = (t - s0) / dur_
                    if u >= 1.0:
                        done = i + 1
                        continue
                    sg = 1 if i % 2 == 0 else -1
                    q = Vector((sg * hw, 0, 0))
                    ry = sg * math.radians(o["roll_deg"]) * math.sin(math.pi * u)
                    done = i + smoothstep(u)
                    break
                d = Vector((0, -step * done, 0))
            elif t < t_fall:                                            # tip about the front edge of the feet
                u = (t - t_tip) / T_tip
                q = Vector((0, -fr, 0))
                rx = pitch * smoothstep(u)
                d = Vector((0, -adv, 0))
            elif t < t_land:                                            # the dive: z on a parabola from rest
                u = (t - t_fall) / T_fall
                q = Vector((0, -fr, 0))
                rx = pitch * smoothstep((t_land - t) * fps / settle_f)  # held, level again over the last 4 frames
                d = Vector((0, -(adv + d_fall * (1 - (1 - u) ** ease)), -drop * u * u))
            else:                                                       # landed: 2-frame 5 mm settle, no bounce
                f = (t - t_land) * fps
                d = Vector((0, -(adv + d_fall), -drop + 0.005 * max(0.0, 1 - f / 2)))
            R = (Matrix.Rotation(ry, 4, "Y") if ry else Matrix()) @ (Matrix.Rotation(rx, 4, "X") if rx else Matrix())
            loc = d + q - (R @ q.to_4d()).to_3d()
            return loc, (rx, ry, 0.0)
        return local

    corners = [Vector((sx * hw / 0.85, sy, 0)) for sx in (-1, 1) for sy in (-fr, foot["back"])]

    def surface(y):
        if y >= 0:
            return top_z
        i = int(math.ceil(-y / run))
        return max(0.0, top_z - rise * i)

    # after the rocks, the front corner of her feet that is farthest from the camera sits on the lip (y = 0): with
    # a three-quarter yaw only one front corner can touch the lip
    def _wy(x, y):
        return math.sin(yaw) * x + math.cos(yaw) * y
    lip_off = -max(_wy(sx * hw / 0.85, -fr) for sx in (-1, 1))

    def layout(depth, ease):
        """Place her (see lip_off) and land with the base centre `depth` past the lip. The dive's horizontal motion
        is 1 - (1 - u) ** ease: 1.0 is constant speed; more front-loads it so the back of her feet clears the top
        tread while z follows the parabola."""
        B0 = Vector((0.12, lip_off - adv * front.y, top_z))
        y_land = -run * (o["steps_down"] - 1) - depth
        B_tip = B0 + adv * front
        d_fall = (B_tip.y - y_land) / math.sin(th)
        local = make_local(B0, d_fall, ease)
        samples = [local(k / fps) for k in range(ctx.nframes)]
        place_m = Matrix.Translation(B0) @ Matrix.Rotation(yaw, 4, "Z")
        worst = 1.0
        for loc, rot in samples:
            M = place_m @ Matrix.Translation(loc) @ Matrix.Rotation(rot[1], 4, "Y") @ Matrix.Rotation(rot[0], 4, "X")
            for cpt in corners:
                w_ = M @ cpt
                worst = min(worst, w_.z - surface(w_.y))
        return B0, B_tip + d_fall * front, samples, worst, y_land

    # The dive must clear the top tread. A constant forward speed with z on a parabola from rest sinks the back of
    # a wide three-quarter footprint 3-6 cm into the tread at a 12 deg pitch, so: the gentlest horizontal ease that
    # clears, then a deeper landing (never past the lower tread's nosing).
    best = None
    for depth in [o["land_depth"] + 0.01 * i for i in range(8)]:
        toe = -run * (o["steps_down"] - 1) - depth - fr * math.sin(th)
        if toe - 0.01 < -run * o["steps_down"] + 0.02 and best is not None:
            break
        for ease in (1.0, 1.15, 1.3, 1.45, 1.6, 1.8, 2.0, 2.3):
            B0, B_land, samples, worst, y_land = layout(depth, ease)
            if best is None or worst > best[3] + 1e-9:
                best = (B0, B_land, samples, worst, y_land, depth, ease)
            if worst >= -0.001:
                break
        if best[3] >= -0.001:
            break
    B0, B_land, samples, worst, y_land, depth, ease = best
    ctx.fact("land_depth_m", round(depth, 3))
    ctx.fact("dive_ease", ease)
    ctx.fact("min_step_clearance_m", round(worst, 4))
    sub.place.location = B0
    sub.place.rotation_euler = (0, 0, yaw)
    for k, (loc, rot) in enumerate(samples):
        ctx.key_rigid(sub.root, k, loc, rot)

    # --- camera: solve the start pose's size, then anchor the start where the cut-back still shows her
    c = ctx.cam_spec
    yt = B0.y
    top_a = (B0.y + 0.15 * H * front.y - yt, top_z + H)
    bot_a = ((B0 + fr * front).y - yt, top_z)
    bot_b = ((B_land + fr * front).y - yt, top_z - drop)
    if c.get("dist") and c.get("tilt") is not None:
        D, tilt = float(c["dist"]), math.radians(float(c["tilt"]))
    else:
        D, tilt = solve_union(c["lens"], c["height"], top_a, bot_a, bot_b, c["fill"])
    cx = (B0.x + B_land.x) / 2
    focus = geo.empty("focus", parent=sub.root, loc=(0, -0.1 * H, 0.6 * H), collection=ctx.col)
    cam = ctx.make_camera((cx, yt - D, c["height"]), tilt, c.get("pan", 0.0), focus)
    ctx.fact("camera_solved", {"dist": round(D, 4), "tilt_deg": round(math.degrees(tilt), 3)})
    if not (c.get("dist") and c.get("tilt") is not None):
        anchored = c.get("anchor") == "start" and c.get("start_cx") is not None
        cy = c.get("start_cy")
        ctx.fact("camera_fit", ctx.fit_camera(
            cam, sub.meshes, range(0, ctx.nframes, 3), max_w=0.84, max_h=0.80,
            center_y=(1 - 2 * cy) if cy is not None else -0.15, anchor_cx=c["start_cx"] if anchored else None,
            x_bounds=(0.04, 0.96) if anchored else None))
        if cy is not None:   # fit_camera centred the union vertically; put frame 0's centre at start_cy instead
            _tilt_to(ctx, cam, sub.meshes, cy)
    cx, D = cam.location.x, B0.y - cam.location.y
    tilt = cam.rotation_euler[0] - math.pi / 2

    # --- set: steps and porch floor, front walk, lawn, the house flat behind the porch
    _lawn(ctx, P)
    step_m = look.plastic("steps", look.PAL["step"], rough=0.38, coat=0.3)
    walk_m = look.matte("walk", "#A9A6A0", 0.55)
    yw = 4.8                     # deep enough that a full-height door fits under a roofline 38% down the frame
    b = geo.Builder()
    sx0 = cx - 0.1
    b.box(step_m, (sx0, yw / 2, top_z / 2), (width + 1.6, yw, top_z))                       # porch floor
    for i in range(1, n_steps):
        z = top_z - rise * i
        y0, y1 = -run * i, -run * (i - 1)
        b.box(step_m, (sx0, (y0 + y1) / 2, z / 2), (width, y1 - y0, z))
    b.box(walk_m, (sx0, -run * (n_steps - 1) - 2.0, 0.003), (1.0, 4.0, 0.006))
    b.to_object("steps", ctx.col)
    nose_m = look.plastic("step_nosing", "#D8D6D0", rough=0.3, coat=0.5)
    shade_m = look.matte("step_riser", "#77767A", 0.5)
    nb = geo.Builder()
    for i in range(n_steps):
        z = top_z - rise * i
        y = -run * i
        nb.box(nose_m, (sx0, y - 0.012, z - 0.015), (width + (1.6 if i == 0 else 0), 0.026, 0.03))
        nb.box(shade_m, (sx0, y - 0.004, z - rise / 2 - 0.012), (width + (1.6 if i == 0 else 0), 0.006, rise - 0.03))
    nb.to_object("step_trim", ctx.col)
    v_roof = 1 - 2 * 0.38                                            # the roofline 38% down the frame
    t_lens = (SENSOR_H / 2) / c["lens"]
    z_roof = cam.location.z + (yw - cam.location.y) * math.tan(tilt + math.atan(v_roof * t_lens))
    lant = _on_plane_y(ctx, cam, 0.13, 0.47, yw - 0.02)
    door_h = min(2.05, z_roof - top_z - 0.22)
    _house(ctx, P, cx - 7, cx + 7, yw, z_roof, door=(cx + 0.30, top_z, 0.95, door_h),
           windows=((cx + 1.55, top_z + 1.15, 0.8, min(1.0, z_roof - top_z - 1.55)),
                    (cx - 1.6, top_z + 1.15, 0.8, min(1.0, z_roof - top_z - 1.55))),
           lantern=(lant.x, lant.z))
    ctx.fact("roofline_z_m", round(z_roof, 3))
    ctx.fact("door_h_m", round(door_h, 3))

    # --- the fireball: one billowing shape on a plane 4 m behind the wall, upper right, below the tag band; its
    # lower part hidden by the roof. Grows from fire_r[0] to fire_r[1] of the frame width by the land beat, never
    # into the tag zone (+20 px); ignites with a flash on frame 0 and booms again on the landing.
    T = ctx.nframes / fps
    fx_, fy_ = o["fire_at"]
    fire_y = yw + 4.0
    fc = _on_plane_y(ctx, cam, fx_, fy_, fire_y)
    fw = _frame_width(ctx, fc.y - cam.location.y)              # frame width (m) at its depth
    zone = ctx.zones.get("tag")
    r_cap = 1e9
    disp = 0.15                                                # the Displace's reach, as a fraction of the radius
    if zone:
        dpx = rect_dist(fx_ * 1080, fy_ * 1920, zone)
        r_cap = 0.94 * dpx / (1 + disp) / 1080                 # radius cap (frame widths) so the silhouette never reaches it
    ctx.fact("fire_r_cap", round(r_cap, 4) if r_cap < 1e8 else None)
    fire_m = look.fire("fireball")
    fb = geo.Builder()
    fb.ico(fire_m, (0, 0, 0), 1.0, subdiv=5)
    fob = fb.to_object("fireball", ctx.col)
    fob.location = fc
    fob.visible_shadow = False
    ctx.fx_tag(fob, "fire")
    tex = bpy_texture_clouds("fire_clouds")
    drv = geo.empty("fire_noise_space", collection=ctx.col)
    md = fob.modifiers.new("billow", "DISPLACE")
    md.texture = tex
    md.texture_coords = "OBJECT"
    md.texture_coords_object = drv
    md.strength = 2 * disp
    md.mid_level = 0.5
    nz = fire_m.node_tree.nodes["noise"]
    sn = fire_m.node_tree.nodes["strength"]
    fl = flicker(rng, 3)
    burst = o["fire_burst"]

    def fire_r(t):
        r0, r1 = o["fire_r"]
        r = r0 + (r1 - r0) * min(1.0, t / max(t_land, 1e-3)) ** 0.8
        if t >= t_land:
            r *= 1 + (burst - 1) * smoothstep((t - t_land) * fps / 6)
        return min(r, r_cap)

    def flash(t):                                               # ignition on frame 0, decaying over 0.3 s
        return 1.0 + 2.0 * max(0.0, 1 - t / 0.3) ** 2

    def boom(t):                                                # the second burst on the landing
        return 1.0 + 0.6 * math.exp(-(t - t_land) / 0.35) if t >= t_land else 1.0
    r_max = 0.0
    for k in range(ctx.nframes):
        t = k / fps
        u = k / max(1, ctx.nframes - 1)
        r_m = fire_r(t) * fw
        r_max = max(r_max, fire_r(t))
        fob.scale = (r_m, r_m, r_m)
        fob.rotation_euler = (0.3 + 1.2 * u, 0.25 * u, 0.15 * u)       # rolls 0.3 -> 1.5 rad over the clip
        fob.keyframe_insert("scale", frame=k + 1)
        fob.keyframe_insert("rotation_euler", frame=k + 1)
        drv.location = (0.0, 0.0, -0.9 * t)                              # the billow keeps boiling upward
        drv.rotation_euler = (0.0, 0.0, 0.4 * t)
        drv.keyframe_insert("location", frame=k + 1)
        drv.keyframe_insert("rotation_euler", frame=k + 1)
        nz.inputs["W"].default_value = 5.6 * o["slowmo"] * t
        nz.inputs["W"].keyframe_insert("default_value", frame=k + 1)
        sn.outputs[0].default_value = (1 + 0.8 * (flash(t) - 1) / 2) * (1 + 0.15 * fl(t)) * boom(t)
        sn.outputs[0].keyframe_insert("default_value", frame=k + 1)
    ctx.fact("fire_r_frac", [o["fire_r"][0], round(r_max, 4)])
    ctx.track("fireball", [fob])
    glow = look.point("fire_glow", fc + Vector((0, -1.2, -0.25 * fw)), look.PAL["spark"], 1500, radius=0.5,
                      collection=ctx.col)

    # sparks: seeded ballistic arcs under slow-motion gravity, keyed per frame; they shrink out (strength 5: AgX
    # keeps them orange)
    if o["sparks"]:
        spark_m = look.emissive("spark", look.PAL["spark"], 5.0)
        sb = geo.Builder()
        sb.ico(spark_m, (0, 0, 0), 0.006 * fw * 16 / 9, subdiv=1)
        proto = sb.to_object("spark_proto", ctx.col)
        proto.hide_render = True
        for i in range(int(o["sparks"])):
            sp = proto.copy()
            sp.name = f"spark{i:02d}"
            sp.hide_render = False
            ctx.col.objects.link(sp)
            sp.visible_shadow = False
            ctx.fx_tag(sp, "spark")
            t0 = rng.uniform(-0.5, T * 0.8)
            life = rng.uniform(1.2, 2.6)
            v = Vector((rng.uniform(-0.05, 0.45), rng.uniform(-0.15, 0.15), rng.uniform(0.25, 0.85))) * fw * 1.07
            p0 = fc + Vector((rng.uniform(-0.03, 0.08) * fw, 0, rng.uniform(0.0, 0.05) * fw))
            g_s = slow_g * 4 * fw * 1.78 / 10
            for k in range(ctx.nframes):
                t = k / fps - t0
                if 0 <= t <= life:
                    sp.location = p0 + v * t + Vector((0, 0, -0.5 * g_s * t * t))
                    s = max(0.0, 1 - t / life)
                else:
                    sp.location = p0
                    s = 0.0
                sp.scale = (s, s, s)
                sp.keyframe_insert("location", frame=k + 1)
                sp.keyframe_insert("scale", frame=k + 1)

    # embers: the visible slow motion. They drift slowly upward across the porch (in front of her and between her
    # and the wall), never near her.
    if o["embers"]:
        em_m = look.emissive("ember", look.PAL["ember"], 3.0)
        path_pts = [B0, B_land, (B0 + B_land) / 2]
        n_done, tries = 0, 0
        while n_done < int(o["embers"]) and tries < 400:
            tries += 1
            layer = rng.random()
            if layer < 0.35:      # foreground: between the lens and her, soft through the DOF
                y = rng.uniform(cam.location.y + 0.35, B_land.y - 0.3)
            else:                 # behind her, in front of the wall
                y = rng.uniform(B0.y + 0.35, yw - 0.3)
            dep = y - cam.location.y
            half_w = 0.5 * _frame_width(ctx, dep)
            x = cam.location.x + rng.uniform(-1.0, 1.0) * half_w
            z0 = rng.uniform(0.15, 1.6)
            p = Vector((x, y, z0))
            if any((p - (q + Vector((0, 0, 0.5 * H)))).length < 0.35 for q in path_pts):
                continue
            r = rng.uniform(0.004, 0.006)
            eb = geo.Builder()
            eb.ico(em_m, (0, 0, 0), r, subdiv=1)
            ob = eb.to_object(f"ember{n_done:02d}", ctx.col)
            ob.visible_shadow = False
            ctx.fx_tag(ob, "ember")
            vz = rng.uniform(0.05, 0.10)
            vx = rng.uniform(-0.03, 0.03)
            ph = rng.uniform(0, 2 * math.pi)
            for k in range(ctx.nframes):
                t = k / fps
                ob.location = (x + vx * t + 0.01 * math.sin(1.3 * t + ph), y, z0 + vz * t)
                ob.keyframe_insert("location", frame=k + 1)
            n_done += 1
        ctx.fact("embers", n_done)

    # --- the chime under the soffit, over the black door, always swaying hard (it was very windy)
    if o["chime"]:
        hook = _on_plane_y(ctx, cam, 0.70, 0.40, yw - 0.45)
        root, tubes = proxies.build_chime(ctx.col, tuple(hook), None, rng)
        period = 3.2 / o["slowmo"] * 0.5
        ph0 = rng.uniform(0, 2 * math.pi)
        for k in range(ctx.nframes):
            t = k / fps
            root.rotation_euler = (0.3 * math.radians(15) * math.sin(2 * math.pi * t / period + ph0 + 1.0),
                                   math.radians(15) * math.sin(2 * math.pi * t / period + ph0), 0)
            root.keyframe_insert("rotation_euler", frame=k + 1)
            for i, tb in enumerate(tubes):
                tb.rotation_euler = (0, math.radians(8) * math.sin(2 * math.pi * t / (period * 0.8) + ph0 + 0.9 * i), 0)
                tb.keyframe_insert("rotation_euler", frame=k + 1)
        ctx.fx(root, "chime")
        look.spot("chime_spot", tuple(Vector(hook) + Vector((0.35, -1.1, 0.25))), tuple(Vector(hook) + Vector((0, 0, -0.45))),
                  "#DDEBFF", 60, angle_deg=14, blend=0.5, collection=ctx.col)   # the tubes glint against the dark door

    # --- concrete dust at the landing: low, soft, grey-brown puffs that run along the tread, spawned 3 cm behind her
    # toe line so her orange feet stay visible on the frame the cut leaves in memory
    if o["dust"]:
        dm = look.dust("dust", look.PAL["dust"])
        z_tread = top_z - drop
        toe = B_land + fr * front
        spawn = toe - 0.03 * front
        along = Vector((1.0, 0.0, 0.0))                 # the tread's long axis
        for i in range(int(o["dust"])):
            side = -1 if i % 2 == 0 else 1
            sp_ = rng.uniform(0.12, 0.30)
            vel = along * side * sp_ + Vector((0, rng.uniform(-0.04, 0.02), 0))
            rise_ = rng.uniform(0.0, 0.03)
            r0 = rng.uniform(0.012, 0.02)
            off = Vector((rng.uniform(-0.6, 0.6) * hw, rng.uniform(-0.02, 0.02), 0))
            db = geo.Builder()
            db.ico(dm, (0, 0, 0), r0, subdiv=2)
            ob = db.to_object(f"dust{i:02d}", ctx.col)
            ob.visible_shadow = False
            ctx.fx_tag(ob, "dust")
            delay = rng.uniform(0.0, 0.08)
            for k in range(ctx.nframes):
                t = k / fps - t_land - delay
                if t < 0:
                    loc, s, al = spawn, 0.0, 0.0
                else:
                    u = min(t / 1.0, 1.0)
                    e = 1 - (1 - u) ** 2
                    loc = Vector((spawn.x, spawn.y, z_tread + r0 * 0.6)) + off + vel * e + Vector((0, 0, rise_ * e))
                    s = 0.6 + 1.4 * e
                    al = 0.25 * min(1.0, t * fps / 2) * (1 - u)
                ob.location = loc
                ob.scale = (s, s, s)
                ob.color = (1, 1, 1, al)
                ob.keyframe_insert("location", frame=k + 1)
                ob.keyframe_insert("scale", frame=k + 1)
                ob.keyframe_insert("color", frame=k + 1)

    # --- lights: the teal/orange action grade. A soft warm key from her beak side (its reflection stays off the
    # door), a spot where she lands, the fire's orange backlight (flickering with the fireball, doubling on the
    # boom), a cool cyan fill-rim from front left, a low teal set flood, the god-ray.
    mid = (B0 + B_land) / 2 + Vector((0, 0, 0.55 * H))
    ctr = B0 + Vector((0, 0, 0.55 * H))
    look.area("key", tuple(B0 + Vector((-0.7, -0.9, 1.0))), tuple(mid), look.PAL["key"], 70, size=1.0, collection=ctx.col)
    look.spot("land_spot", tuple(B_land + Vector((0.15, -0.25, 1.4))), tuple(B_land + Vector((0, 0, 0.3 * H))), "#FFF4E6",
              150, angle_deg=25, blend=0.5, collection=ctx.col)
    look.area("fill", tuple(Vector((cx, cam.location.y - 0.2, 0.5))), tuple(ctr), P["fill"], 25, size=1.2,
              collection=ctx.col)
    look.area("rim_fill", tuple(B0 + Vector((-0.9, -0.25, 0.65))), tuple(ctr), P["rim_fill"], 150, size=0.3,
              collection=ctx.col)
    fb_ = look.area("fire_back", tuple(B0 + Vector((0.45, 0.9, 1.0))), tuple(ctr), P["fire_back"], 700, size=0.4,
                    collection=ctx.col)
    look.spot("top", tuple(B0 + Vector((0, 0.1, 1.6))), tuple(B0), "#F3EEFF", 60, angle_deg=30, collection=ctx.col)
    look.area("set_flood", (cx, 0.9, 1.3), (cx, yw, 2.0), P["set_flood"], 70, size=2.5, collection=ctx.col, glossy=False)
    for k in range(ctx.nframes):
        t = k / fps
        f = flash(t) * (1 + 0.15 * fl(t))
        look.key_energy(fb_, k, 700 * f * (1 + (boom(t) - 1) / 0.6))       # x2 on the landing, decaying
        look.key_energy(glow, k, 1500 * f * boom(t))
    _godray(ctx, cam, tuple(Vector((cx + 1.0, yw - 0.6, z_roof - 0.2))), tuple(B0 + Vector((-0.3, 0, 0))), "#FFC890",
            260, 16, o["haze"])
    _haze(ctx, cam, (D + 0.6, D + 1.6, D + 2.2), o["haze"], o["slowmo"],
          box=((cx - 3, B0.y - 0.6, -0.01), (cx + 3, yw - 0.05, z_roof + 0.2)), hexc=P["haze"], density=0.008, drift=3.0)
    for name in ("key", "land_spot", "fire_back", "rim_fill", "fill", "chime_spot", "top"):
        _no_volume(ctx.col.objects.get(name))     # only the god-ray shafts through the haze; the rest would fog it orange
    ctx.mover(sub)
    ctx.track("subject", sub.meshes)
    ctx.keep_clear = ["subject", "fireball"]
    ctx.coverage = {"fireball": {"min_frac": 0.06, "by_frame": ctx.beat_frame("land")}}
    ctx.facing = {"min_deg": 15.0, "max_deg": 60.0, "allow": o["allow_facing"]}
    ctx.exposure = 0.4


def _no_volume(light_ob):
    """A light that shades surfaces but doesn't scatter in the haze volume (Cycles ray visibility; Eevee factor)."""
    if light_ob is None:
        return
    light_ob.visible_volume_scatter = False
    if hasattr(light_ob.data, "volume_factor"):
        light_ob.data.volume_factor = 0.0


def _tilt_to(ctx, cam, meshes, cy):
    """Tilt the locked camera so the subject's frame-0 box is centred at cy (0..1 from the top)."""
    import numpy as np
    tv = (SENSOR_H / 2) / cam.data.lens
    for _ in range(4):
        P = ctx._points_per_frame(meshes, [0])[0]
        R = np.array(cam.rotation_euler.to_matrix())
        q = (P - np.array(cam.location)) @ R
        y = q[:, 1] / -q[:, 2] / tv
        c = (y.max() + y.min()) / 2
        rx = cam.rotation_euler[0] + math.atan(c * tv) - math.atan((1 - 2 * cy) * tv)
        cam.rotation_euler = (rx, cam.rotation_euler[1], cam.rotation_euler[2])
    ctx.scene.frame_set(1)


def bpy_texture_clouds(name):
    import bpy
    t = bpy.data.textures.new(name, "CLOUDS")
    t.noise_scale = 0.45
    t.noise_depth = 3
    t.noise_basis = "BLENDER_ORIGINAL"
    return t


# ---------------------------------------------------------------- showcase (CLI only) and test templates
@template("showcase", version=1, subject="garrison", props=(), camera="sheet", beats=(), cli_only=True,
          locked_camera=False, yaw_locked=False,
          options={"mode": "sheet", "views": [0, 35, 90, 180], "fill": 0.80, "fstop": 8.0})
def showcase(ctx):
    """The model alone on the SHEET_3D grey ground, lit with the plastic look. `sheet`: frame k shows view k
    (front, three-quarter, side, back); `turntable`: one orbit over the clip; `pushin`: a 1.0 -> 1.3 dolly."""
    from . import geo, look
    o = ctx.opts
    look.world(ctx.scene, "#7A7A7A", "#9A9A9A", 0.8)
    sub = ctx.subject()
    H = sub.height
    grey = look.matte("sheet_ground", "#8E8E8E", 0.7)
    b = geo.Builder()
    b.quad(grey, (0, 0, 0), (30, 30))
    b.to_object("ground", ctx.col)
    c = ctx.cam_spec
    v_top = 1 - 2 * c["top_at"]
    D, tilt = solve_camera(c["lens"], H * 0.5, (0.0, H), (0.0, 0.0), v_top, v_top - 2 * c["fill"])
    focus = geo.empty("focus", parent=sub.root, loc=(0, 0, 0.5 * H), collection=ctx.col)
    pivot = geo.empty("orbit", loc=(0, 0, 0), collection=ctx.col)
    cam = ctx.make_camera((0.0, -D, 0.5 * H), tilt, 0.0, focus, parent=pivot)
    n = ctx.nframes
    for k in range(n):
        if o["mode"] == "sheet":   # view k: front, three-quarter (beak left), side, back
            pivot.rotation_euler = (0, 0, -math.radians(o["views"][k % len(o["views"])]))
        elif o["mode"] == "turntable":
            pivot.rotation_euler = (0, 0, 2 * math.pi * k / n)
        else:                      # pushin: a 1.0 -> 1.3 dolly
            cam.location = (0.0, -D / (1.0 + 0.3 * k / max(1, n - 1)), 0.5 * H)
            cam.keyframe_insert("location", frame=k + 1)
        pivot.keyframe_insert("rotation_euler", frame=k + 1)
    tgt = (0, 0, 0.5 * H)
    look.area("key", (0.8 * D, -0.9 * D, 1.2 * H + 0.3), tgt, "#FFFFFF", 60 * D * D, size=1.0, collection=ctx.col)
    look.area("rim", (-0.6 * D, 0.8 * D, 1.4 * H + 0.2), tgt, "#FFFFFF", 50 * D * D, size=0.5, collection=ctx.col)
    look.area("fill", (-0.9 * D, -0.6 * D, 0.6 * H), tgt, "#FFFFFF", 25 * D * D, size=1.2, collection=ctx.col)
    ctx.fact("height_m", round(H, 5))
    ctx.fact("foot", {k: round(v, 4) for k, v in sub.foot.items()})
    ctx.track("subject", sub.meshes)
    ctx.exposure = 0.0


@template("_test_yaw", version=1, subject="garrison", props=(), camera="beside_deb", beats=("move",),
          cli_only=True, options={})
def _test_yaw(ctx):
    """Test only: keys the subject's yaw, which the worker must refuse (the rigidity tripwire)."""
    from . import look
    g = ctx.subject()
    c = ctx.cam_spec
    D, tilt = solve_camera(c["lens"], c["height"], (0.0, g.height), (0.0, 0.0), 0.5, -0.82)
    ctx.make_camera((0.0, -D, c["height"]), tilt, 0.0, None)
    _lawn(ctx, look.palette("heist"))
    look.area("key", (0.5, -0.8, 0.8), (0, 0, 0.2), "#FFFFFF", 40, collection=ctx.col)
    for k in range(ctx.nframes):
        g.root.rotation_euler = (0, 0, 0.02 * max(0, k - ctx.beat_frame("move")))
        g.root.keyframe_insert("rotation_euler", frame=k + 1)
    ctx.mover(g)
    ctx.track("subject", g.meshes)


@template("_test_touch", version=1, subject="garrison", props=(), camera="beside_deb", beats=("move",),
          cli_only=True, options={})
def _test_touch(ctx):
    """Test only: a beam through the cap, which the worker must refuse (the never-touch rule)."""
    from . import look
    g = ctx.subject()
    c = ctx.cam_spec
    D, tilt = solve_camera(c["lens"], c["height"], (0.0, g.height), (0.0, 0.0), 0.5, -0.82)
    ctx.make_camera((0.0, -D, c["height"]), tilt, 0.0, None)
    _lawn(ctx, look.palette("heist"))
    look.area("key", (0.5, -0.8, 0.8), (0, 0, 0.2), "#FFFFFF", 40, collection=ctx.col)
    ctx.beam("laser_test", (0, 0, 0.9 * g.height), (1, 0, 0), 1.0, 0.0025)
    for k in range(ctx.nframes):
        ctx.key_rigid(g.root, k, (0.0, 0.0, 0.0))
    ctx.mover(g)
    ctx.track("subject", g.meshes)


@template("_test_blended", version=1, subject="garrison", props=(), camera="beside_deb", beats=("move",),
          cli_only=True, options={})
def _test_blended(ctx):
    """Test only: a BLENDED emitter (it would vanish from Eevee's passes), which the worker must refuse."""
    from . import geo, look
    g = ctx.subject()
    c = ctx.cam_spec
    D, tilt = solve_camera(c["lens"], c["height"], (0.0, g.height), (0.0, 0.0), 0.5, -0.82)
    ctx.make_camera((0.0, -D, c["height"]), tilt, 0.0, None)
    m = look.emissive("bad_glow", "#FF0000", 2.0)
    m.surface_render_method = "BLENDED"
    b = geo.Builder()
    b.sphere(m, (0.2, 0.2, 0.2), 0.02)
    b.to_object("bad_glow", ctx.col)
    for k in range(ctx.nframes):
        ctx.key_rigid(g.root, k, (0.0, 0.0, 0.0))
    ctx.mover(g)
    ctx.track("subject", g.meshes)
