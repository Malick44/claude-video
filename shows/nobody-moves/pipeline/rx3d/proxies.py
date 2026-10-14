"""Subjects: procedural proxies and GLB import with normalization (docs/BLENDER_REENACTMENTS.md §4).

Runs only inside Blender. Every subject (or prop) ends up as

    place_<name>   static: its spot in the set and its yaw, set once, never keyed
      subj_<name>  the only thing a template animates (location, plus roll/pitch for a rock or a tip)
        <name>_norm   static: the GLB's normalization (scale to height_m, base at Z=0, front to -Y)
          meshes      `<name>_PROXY` for a proxy, the GLB's meshes otherwise

Front faces -Y (the camera side) before the yaw. Sizes are fractions of the bible's height H (metres).
Proxies carry the faint 45-degree stripe and the _PROXY name, so they are never mistaken for a model.
"""
import math
import os

import bpy
import numpy as np
from mathutils import Matrix, Vector

from . import geo, look

HEIGHTS = {"ray": 0.152, "garrison": 0.406, "lorraine": 0.508, "basin": 0.711, "deb": 0.864, "chime": 0.914,
           "dale": 2.438}   # SERIES.md: Ray 6 in, Garrison 16, Lorraine 20, Mr. Basin 28, Deb 34, chime 36; Dale 8 ft up
OUTFITS = (None, "bumblebee", "easter", "gingham")


class Subject:
    def __init__(self, name, kind, place, root, norm, meshes, anchors, file=None):
        self.name, self.kind, self.place, self.root, self.norm = name, kind, place, root, norm
        self.meshes, self.anchors, self.file = meshes, anchors, file
        self.height = measure_height(meshes)
        self.foot = footprint(meshes, self.height)

    def local_bbox(self):
        """(min, max) of the figure in root-local space (normalized metres)."""
        lo, hi = _verts_bounds(self.meshes, self.root)
        return lo, hi


# ---------------------------------------------------------------- measuring
def _verts_local(meshes, frame_obj):
    """All vertices of `meshes` in the space of `frame_obj` (evaluated, so modifiers count)."""
    dg = bpy.context.evaluated_depsgraph_get()
    inv = frame_obj.matrix_world.inverted() if frame_obj else Matrix()
    out = []
    for ob in meshes:
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        co = np.empty(len(me.vertices) * 3, dtype=np.float64)
        me.vertices.foreach_get("co", co)
        ev.to_mesh_clear()
        co = co.reshape(-1, 3)
        m = np.array(inv @ ob.matrix_world)
        out.append(co @ m[:3, :3].T + m[:3, 3])
    return np.concatenate(out) if out else np.zeros((0, 3))


def _verts_bounds(meshes, frame_obj):
    v = _verts_local(meshes, frame_obj)
    return v.min(axis=0), v.max(axis=0)


def measure_height(meshes):
    root = meshes[0].parent.parent if meshes and meshes[0].parent else None
    bpy.context.view_layer.update()
    v = _verts_local(meshes, root)
    return float(v[:, 2].max())


def footprint(meshes, H):
    """The contact patch: vertices within 4% of H of the base. Half width, front and back reach (root space)."""
    root = meshes[0].parent.parent if meshes and meshes[0].parent else None
    v = _verts_local(meshes, root)
    low = v[v[:, 2] < 0.04 * max(H, 1e-6)]
    if not len(low):
        low = v
    return {"half_width": float(max(-low[:, 0].min(), low[:, 0].max())),
            "front": float(-low[:, 1].min()), "back": float(low[:, 1].max())}


def mesh_hash(meshes):
    """sha1 of every subject vertex in its own object space (rounded): changes only if a mesh deforms."""
    import hashlib
    dg = bpy.context.evaluated_depsgraph_get()
    h = hashlib.sha1()
    for ob in sorted(meshes, key=lambda o: o.name):
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        co = np.empty(len(me.vertices) * 3, dtype=np.float32)
        me.vertices.foreach_get("co", co)
        ev.to_mesh_clear()
        h.update(np.round(co, 5).tobytes())
    return h.hexdigest()[:16]


# ---------------------------------------------------------------- proxy builders (front -Y, base at Z=0)
def _mats(prefix, spec, stripe=True):
    out = {}
    for k, v in spec.items():
        hexc, kw = (v, {}) if isinstance(v, str) else v
        out[k] = look.plastic(f"{prefix}_{k}", hexc, stripe=stripe, **kw)
    return out


def build_garrison(h, stripe=True):
    """Garrison as in stills/garrison.webp: a full white beard down to the belly with the fists at its lower
    corners (thumbs up), slate trousers and dark boots showing under a blue tunic, a tall red cap with a few
    brown paint chips, bead eyes under the brim (big enough to read on a phone: he stares into the lens)."""
    M = _mats("garrison", {
        "cap": ("#B0281F", {"rough": 0.28}), "beard": ("#F3F0EA", {"rough": 0.35}), "tunic": "#4F6D8F",
        "trousers": ("#2F3A4A", {"rough": 0.4}), "belt": "#151515",
        "buckle": ("#C9A227", {"metal": 1.0, "rough": 0.2, "coat": 0.5}),
        "skin": "#E9BFA6", "cheek": "#E57F72", "nose": "#E59A86", "boot": "#3B2416",
        "eye": ("#0A0A0A", {"rough": 0.08}), "chip": ("#6B4436", {"rough": 0.7, "coat": 0.0})}, stripe)
    b = geo.Builder()
    for sx in (-1, 1):
        b.sphere(M["boot"], (sx * 0.08 * h, -0.06 * h, 0.042 * h), 0.072 * h, scale=(1, 1.4, 0.6))     # toes forward
        b.cyl(M["trousers"], (sx * 0.07 * h, -0.01 * h, 0.06 * h), 0.05 * h, 0.11 * h, seg=24)          # legs
    b.cone(M["tunic"], (0, 0, 0.16 * h), 0.19 * h, 0.15 * h, 0.28 * h, seg=48)    # hem at 0.16 H: boots show
    b.sphere(M["tunic"], (0, 0, 0.44 * h), 0.152 * h, scale=(1, 1, 0.55))
    b.cyl(M["belt"], (0, 0, 0.275 * h), 0.176 * h, 0.045 * h, seg=48)
    b.box(M["buckle"], (0, -0.178 * h, 0.297 * h), (0.07 * h, 0.02 * h, 0.06 * h))
    b.sphere(M["skin"], (0, 0, 0.585 * h), 0.112 * h)
    # the beard: in front of the tunic (its front at -0.152 H), from under the moustache down to the belly, leaning
    # back as it rises so it never covers the nose; a rounded bottom between the fists
    b.cone(M["beard"], (0, -0.145 * h, 0.30 * h), 0.085 * h, 0.12 * h, 0.23 * h, seg=40, scale=(1, 0.6, 1),
           rot=(math.radians(-10), 0, 0))
    b.sphere(M["beard"], (0, -0.145 * h, 0.315 * h), 0.085 * h, scale=(1, 0.6, 0.7))
    b.sphere(M["beard"], (0, -0.075 * h, 0.515 * h), 0.122 * h, scale=(1.06, 0.72, 0.62))   # cheeks to chin
    for sx in (-1, 1):
        b.sphere(M["beard"], (sx * 0.05 * h, -0.142 * h, 0.535 * h), 0.042 * h, scale=(1.45, 0.65, 0.55),
                 rot=(0, sx * 0.35, 0))                                                          # moustache
        b.sphere(M["cheek"], (sx * 0.07 * h, -0.098 * h, 0.578 * h), 0.032 * h, scale=(1, 0.55, 0.8))
        b.sphere(M["eye"], (sx * 0.052 * h, -0.128 * h, 0.59 * h), 0.02 * h, seg=(16, 8))     # big enough to read
        # fists at the beard's lower corners; the thumb on the fist's inner top edge, tilted 15 deg outward;
        # three curled-finger ridges across the front, so a raised digit never reads as a middle finger
        hx, hy, hz = sx * 0.11 * h, -0.16 * h, 0.38 * h
        b.sphere(M["skin"], (hx, hy, hz), 0.046 * h, scale=(1, 0.85, 1))
        b.sphere(M["skin"], (sx * 0.080 * h, hy - 0.012 * h, hz + 0.052 * h), 0.016 * h, scale=(1, 1, 1.9),
                 rot=(0, sx * math.radians(15), 0))
        for j in range(3):
            b.sphere(M["skin"], (hx + sx * 0.006 * h, -0.19 * h, hz + (j - 1) * 0.022 * h), 0.012 * h,
                     scale=(2.4, 0.9, 0.9), seg=(16, 8))
    b.sphere(M["nose"], (0, -0.142 * h, 0.568 * h), 0.046 * h)
    b.cone(M["cap"], (0, 0, 0.62 * h), 0.136 * h, 0.003 * h, 0.38 * h, seg=64)
    b.torus(M["cap"], (0, 0, 0.627 * h), 0.13 * h, 0.017 * h)
    slope = 0.136 / 0.38
    # chipped paint: brown-grey, irregular, on the brim and the tip only (cream dots read as polka dots)
    # (#9C6B5A, the first try, still read as pale ovals under the key: worn resin is darker than the red)
    for a_deg, z, sc in ((-112, 0.672, (1.8, 0.6, 0.12)), (-62, 0.69, (1.3, 0.5, 0.12)), (-97, 0.90, (0.9, 0.45, 0.12))):
        a = math.radians(a_deg)
        r = 0.136 * h * (1 - (z * h - 0.62 * h) / (0.38 * h)) + 0.0015 * h
        n = Vector((math.cos(a), math.sin(a), slope)).normalized()
        rot = Vector((0, 0, 1)).rotation_difference(n).to_euler()
        b.sphere(M["chip"], (r * math.cos(a), r * math.sin(a), z * h), 0.02 * h, scale=sc, rot=tuple(rot), seg=(12, 6))
    anchors = {"nose": (0.0, -0.188 * h, 0.568 * h), "cap_tip": (0.0, 0.0, 1.0 * h), "head": (0.0, -0.11 * h, 0.59 * h),
               "eyes": (0.0, -0.148 * h, 0.59 * h)}
    return b, anchors


def _wing_ridges(b, mat, sx, h, centre, radii, rot_x, n=3):
    """Molded feather ridges on a wing ellipsoid: thin tubes following its outer surface."""
    cx, cy, cz = centre
    a, bb, c = radii
    R = Matrix.Rotation(rot_x, 3, "X")
    for j in range(n):
        zl = (-0.35 + 0.3 * j) * c
        pts = []
        for i in range(9):
            yl = (-0.15 + 0.85 * i / 8) * bb
            q = 1 - (yl / bb) ** 2 - (zl / c) ** 2
            if q <= 0.02:
                continue
            xl = a * math.sqrt(q) + 0.002 * h
            pts.append(Vector((cx, cy, cz)) + R @ Vector((sx * xl, yl, zl)))
        if len(pts) >= 3:
            b.tube(mat, pts, [0.006 * h] * len(pts), seg=8)


def build_lorraine(h, stripe=True, outfit=None):
    """Lorraine as in stills/lorraine.webp: white glaze, an S-curved neck on a plump egg body, a round head, a
    chunky yellow-orange beak and orange webbed feet (#F7A600), molded wing feathers, an upturned tail."""
    M = _mats("lorraine", {"glaze": ("#F5F2EA", {"rough": 0.22}), "wing": ("#E9E4DA", {"rough": 0.25}),
                           "beak": ("#F7A600", {"rough": 0.3}), "eye": ("#0A0A0A", {"rough": 0.1})}, stripe)
    b = geo.Builder()
    b.sphere(M["glaze"], (0, 0.02 * h, 0.30 * h), 1.0, scale=(0.20 * h, 0.31 * h, 0.20 * h), rot=(math.radians(-15), 0, 0),
             seg=(40, 20))
    for sx in (-1, 1):
        wc, wr, wrot = (sx * 0.168 * h, 0.06 * h, 0.335 * h), (0.05 * h, 0.22 * h, 0.12 * h), math.radians(-12)
        b.sphere(M["wing"], wc, 1.0, scale=wr, rot=(wrot, 0, 0))
        _wing_ridges(b, M["wing"], sx, h, wc, wr, wrot)
        b.cyl(M["beak"], (sx * 0.075 * h, -0.07 * h, 0.02 * h), 0.024 * h, 0.10 * h, seg=16)          # legs
        b.sphere(M["beak"], (sx * 0.08 * h, -0.13 * h, 0.02 * h), 1.0, scale=(0.072 * h, 0.12 * h, 0.02 * h),
                 seg=(24, 8))                                                                          # webbed feet
        b.sphere(M["eye"], (sx * 0.06 * h, -0.262 * h, 0.94 * h), 0.013 * h, seg=(12, 6))
    b.cone(M["glaze"], (0, 0.27 * h, 0.33 * h), 0.09 * h, 0.012 * h, 0.12 * h, rot=(math.radians(-40), 0, 0))  # tail
    neck = geo.bezier((0, -0.19 * h, 0.40 * h), (0, -0.30 * h, 0.62 * h), (0, -0.16 * h, 0.74 * h),
                      (0, -0.215 * h, 0.90 * h), n=24)
    b.tube(M["glaze"], neck, [0.085 * h + (0.058 - 0.085) * h * i / 24 for i in range(25)], seg=24)
    b.sphere(M["glaze"], (0, -0.22 * h, 0.92 * h), 0.086 * h, scale=(0.92, 1.12, 0.95))
    b.cone(M["beak"], (0, -0.29 * h, 0.905 * h), 0.040 * h, 0.012 * h, 0.13 * h, rot=(math.radians(90), 0, 0),
           scale=(1.15, 0.7, 1.0), seg=24)
    if outfit:
        hexc = {"bumblebee": "#F2C230", "easter": "#F4E79A", "gingham": "#2F5FB3"}[outfit]
        om = look.plastic(f"lorraine_outfit_{outfit}", hexc, stripe=stripe, rough=0.6, coat=0.2)
        b.cyl(om, (0, 0.02 * h, 0.20 * h), 0.212 * h, 0.17 * h, seg=48, scale=(1, 1.45, 1))
    anchors = {"beak_tip": (0.0, -0.42 * h, 0.905 * h), "head": (0.0, -0.22 * h, 0.92 * h),
               "foot_l": (-0.08 * h, -0.20 * h, 0.01 * h), "foot_r": (0.08 * h, -0.20 * h, 0.01 * h)}
    return b, anchors


def build_deb(h, stripe=True):
    M = _mats("deb", {"body": ("#EE7486", {"rough": 0.25}), "wing": ("#F59AA8", {"rough": 0.25}),
                      "beak": ("#EEE2C0", {"rough": 0.3}), "tip": ("#121212", {"rough": 0.2}),
                      "eye": ("#0A0A0A", {"rough": 0.1}),
                      "rod": ("#A7ADB3", {"metal": 1.0, "rough": 0.22, "coat": 0.0})}, stripe)
    b = geo.Builder()
    for sx in (-1, 1):   # two straight galvanized rods, 6 mm, from 5 cm below the lawn into the body
        b.cyl(M["rod"], (sx * 0.022, 0.0, -0.05), 0.006, 0.46 * h + 0.05, seg=12)
        b.sphere(M["wing"], (sx * 0.083 * h, 0.06 * h, 0.535 * h), 1.0, scale=(0.03 * h, 0.17 * h, 0.07 * h),
                 rot=(math.radians(10), 0, 0))
        b.sphere(M["eye"], (sx * 0.028 * h, -0.19 * h, 0.965 * h), 0.008 * h, seg=(10, 6))
    b.sphere(M["body"], (0, 0.03 * h, 0.52 * h), 1.0, scale=(0.10 * h, 0.225 * h, 0.095 * h), rot=(math.radians(12), 0, 0),
             seg=(40, 20))
    b.cone(M["body"], (0, 0.22 * h, 0.55 * h), 0.05 * h, 0.01 * h, 0.09 * h, rot=(math.radians(-70), 0, 0))
    neck = geo.bezier((0, -0.16 * h, 0.55 * h), (0, -0.31 * h, 0.66 * h), (0, -0.05 * h, 0.79 * h),
                      (0, -0.15 * h, 0.935 * h), n=28)
    b.tube(M["body"], neck, [0.034 * h + (0.021 - 0.034) * h * i / 28 for i in range(29)], seg=18)
    b.sphere(M["body"], (0, -0.175 * h, 0.955 * h), 0.038 * h, scale=(0.85, 1.25, 1.0))
    b.tube(M["beak"], [(0, -0.21 * h, 0.955 * h), (0, -0.25 * h, 0.948 * h), (0, -0.275 * h, 0.928 * h)],
           [0.017 * h, 0.014 * h, 0.011 * h], seg=14)
    b.tube(M["tip"], [(0, -0.275 * h, 0.928 * h), (0, -0.287 * h, 0.905 * h), (0, -0.289 * h, 0.885 * h)],
           [0.011 * h, 0.008 * h, 0.003 * h], seg=14)
    anchors = {"head": (0.0, -0.175 * h, 0.955 * h), "beak_tip": (0.0, -0.289 * h, 0.885 * h)}
    return b, anchors


def build_basin(h, stripe=True):
    M = _mats("basin", {"stone": ("#D3CCBC", {"rough": 0.35, "coat": 0.6}),
                        "water": ("#3E8FD0", {"rough": 0.02}), "case": ("#5B3519", {"rough": 0.4}),
                        "clasp": ("#C9A227", {"metal": 1.0, "rough": 0.2, "coat": 0.5})}, stripe)
    b = geo.Builder()
    b.cyl(M["stone"], (0, 0, 0), 0.21 * h, 0.05 * h, seg=48)
    b.cyl(M["stone"], (0, 0, 0.05 * h), 0.16 * h, 0.05 * h, seg=48)
    b.cyl(M["stone"], (0, 0, 0.10 * h), 0.065 * h, 0.70 * h, seg=32)
    for i in range(12):
        a = 2 * math.pi * i / 12
        b.cyl(M["stone"], (0.065 * h * math.cos(a), 0.065 * h * math.sin(a), 0.11 * h), 0.012 * h, 0.66 * h, seg=8)
    b.torus(M["stone"], (0, 0, 0.60 * h), 0.08 * h, 0.018 * h)
    b.cone(M["stone"], (0, 0, 0.80 * h), 0.08 * h, 0.42 * h, 0.15 * h, seg=48)
    b.disc(M["water"], (0, 0, 0.951 * h), 0.39 * h)
    for i in range(16):
        a = 2 * math.pi * i / 16
        b.sphere(M["stone"], (0.42 * h * math.cos(a), 0.42 * h * math.sin(a), 0.95 * h), 0.05 * h, seg=(16, 8))
    b.box(M["case"], (0.13 * h, -0.215 * h, 0.05 * h), (0.13 * h, 0.035 * h, 0.095 * h), rot=(math.radians(-12), 0, 0))
    b.box(M["clasp"], (0.13 * h, -0.236 * h, 0.085 * h), (0.025 * h, 0.006 * h, 0.012 * h), rot=(math.radians(-12), 0, 0))
    anchors = {"bowl": (0.0, 0.0, 0.951 * h)}
    return b, anchors


PROXY_BUILDERS = {"garrison": build_garrison, "lorraine": build_lorraine, "deb": build_deb, "basin": build_basin}


def build_chime(collection, hook, sway_parts, rng, stripe=False):
    """The wind chime, a set prop: wooden disc, 5 brushed tubes on cords, striker, teardrop sail. Returns the
    pendulum root (pivot at `hook`) and its tube objects (each pivots on its own cord), for the template to sway."""
    wood = look.plastic("chime_wood", "#4A2E1C", rough=0.45, coat=0.4, stripe=stripe)
    tube = look.plastic("chime_tube", "#C9CED6", metal=1.0, rough=0.15, coat=0.0, stripe=stripe)
    cord = look.plastic("chime_cord", "#111111", rough=0.6, coat=0.0, stripe=stripe)
    sail = look.plastic("chime_sail", "#8A8F96", rough=0.5, coat=0.2, stripe=stripe)
    root = geo.empty("chime_root", loc=hook, collection=collection)
    b = geo.Builder()
    b.cyl(cord, (0, 0, -0.10), 0.0015, 0.10, seg=6)
    b.cyl(wood, (0, 0, -0.13), 0.09, 0.03, seg=32)
    b.cyl(cord, (0, 0, -0.62), 0.0012, 0.49, seg=6)
    b.cyl(wood, (0, 0, -0.50), 0.045, 0.014, seg=24)          # striker
    b.sphere(sail, (0, 0, -0.75), 1.0, scale=(0.06, 0.006, 0.12), seg=(24, 10))
    b.to_object("chime_body", collection, parent=root)
    tubes = []
    lengths = (0.42, 0.36, 0.31, 0.27, 0.23)
    for i, ln in enumerate(lengths):
        a = 2 * math.pi * i / 5 + 0.3
        piv = geo.empty(f"chime_tube{i}", parent=root, loc=(0.068 * math.cos(a), 0.068 * math.sin(a), -0.14),
                        collection=collection)
        t = geo.Builder()
        t.cyl(cord, (0, 0, -0.05), 0.0012, 0.05, seg=6)
        t.cyl(tube, (0, 0, -0.05 - ln), 0.012, ln, seg=20)
        t.to_object(f"chime_tube{i}_mesh", collection, parent=piv)
        tubes.append(piv)
    root["cast"] = "chime"
    return root, tubes


# ---------------------------------------------------------------- subjects and props
def _fit_height(norm, meshes, H, root):
    bpy.context.view_layer.update()
    top = float(_verts_local(meshes, root)[:, 2].max())
    s = H / top
    norm.matrix_basis = Matrix.Diagonal((s, s, s, 1.0)) @ norm.matrix_basis
    bpy.context.view_layer.update()


def add_proxy(name, H, collection, role="subject", outfit=None):
    if name not in PROXY_BUILDERS:
        raise RuntimeError(f"no proxy for {name!r} (proxies: {', '.join(sorted(PROXY_BUILDERS))})")
    prefix = "subj" if role == "subject" else "prop"
    place = geo.empty(f"place_{name}", collection=collection)
    root = geo.empty(f"{prefix}_{name}", parent=place, collection=collection)
    norm = geo.empty(f"{name}_norm", parent=root, collection=collection)
    kw = {"outfit": outfit} if name == "lorraine" else {}
    b, anchors = PROXY_BUILDERS[name](H, **kw)
    ob = b.to_object(f"{name}_PROXY", collection, parent=norm)
    ob["proxy"] = True
    _fit_height(norm, [ob], H, root)
    s = norm.matrix_basis.to_scale()[0]
    anchors = {k: tuple(s * c for c in v) for k, v in anchors.items()}
    root["cast"] = name
    root["role"] = role
    return Subject(name, "proxy", place, root, norm, [ob], anchors)


def _forward_angle(forward, yaw_offset_deg):
    base = {"+z": 0.0, "-z": 180.0, "+x": -90.0, "-x": 90.0}[forward]
    return math.radians(base + (yaw_offset_deg or 0.0))


def add_glb(name, model, collection, role="subject"):
    """Import a GLB and normalize it: strip rigs/shape keys/animation (subjects stay rigid), turn its front
    to -Y, scale it uniformly to height_m, put the base centre at the origin, and restyle its materials."""
    path = model["path"]
    if not os.path.exists(path):
        raise RuntimeError(f"{name}: {path} missing; file it with: blender_reenact.py model add")
    before = set(bpy.data.objects.keys())
    try:
        res = bpy.ops.import_scene.gltf(filepath=path)
    except Exception as e:      # the importer folds a whole traceback into its message: keep its last line
        lines = [ln.strip() for ln in str(e).splitlines() if ln.strip() and not ln.startswith((" ", "Location"))
                 and "Traceback" not in ln]
        raise RuntimeError(f"{name}: the glTF importer rejected {os.path.basename(path)}: "
                           f"{lines[-1] if lines else type(e).__name__}") from None
    if "FINISHED" not in res:
        raise RuntimeError(f"{name}: glTF import failed for {path}; file it with: blender_reenact.py model add")
    new = [bpy.data.objects[n] for n in sorted(set(bpy.data.objects.keys()) - before)]
    bpy.context.view_layer.update()
    meshes = [o for o in new if o.type == "MESH"]
    if not meshes:
        raise RuntimeError(f"{name}: {os.path.basename(path)} has no mesh")
    stripped = []
    world = {o.name: o.matrix_world.copy() for o in meshes}
    prefix = "subj" if role == "subject" else "prop"
    place = geo.empty(f"place_{name}", collection=collection)
    root = geo.empty(f"{prefix}_{name}", parent=place, collection=collection)
    norm = geo.empty(f"{name}_norm", parent=root, collection=collection)
    for o in meshes:
        for mod in list(o.modifiers):
            if mod.type in ("ARMATURE", "SHAPEWRAP") or mod.type.startswith("MESH_DEFORM"):
                stripped.append(f"{o.name}:{mod.type}")
                o.modifiers.remove(mod)
        if o.data.shape_keys:
            stripped.append(f"{o.name}:shape_keys")
            o.shape_key_clear()
        if o.animation_data:
            o.animation_data_clear()
        for c in list(o.users_collection):
            c.objects.unlink(o)
        collection.objects.link(o)
        o.parent = norm
        o.matrix_parent_inverse = Matrix()
        o.matrix_basis = world[o.name]
        if model.get("restyle", True):
            for slot in o.material_slots:
                look.restyle(slot.material)
    for o in new:
        if o.type != "MESH":
            if o.type == "ARMATURE":
                stripped.append(f"{o.name}:armature")
            bpy.data.objects.remove(o, do_unlink=True)
    rz = Matrix.Rotation(_forward_angle(model.get("forward", "+z"), model.get("yaw_offset_deg", 0)), 4, "Z")
    norm.matrix_basis = rz
    bpy.context.view_layer.update()
    v = _verts_local(meshes, root)
    lo, hi = v.min(axis=0), v.max(axis=0)
    H = float(model["height_m"])
    s = H / max(hi[2] - lo[2], 1e-9)
    c = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]))
    norm.matrix_basis = Matrix.Diagonal((s, s, s, 1.0)) @ Matrix.Translation(-c) @ rz
    bpy.context.view_layer.update()
    tris = 0
    for o in meshes:
        o.data.calc_loop_triangles()
        tris += len(o.data.loop_triangles)
    root["cast"] = name
    root["role"] = role
    anchors = {k: tuple(v) for k, v in (model.get("anchors") or {}).items()}
    sub = Subject(name, "glb", place, root, norm, meshes, anchors, file=path)
    sub.stripped, sub.tris = stripped, tris
    return sub


def add_subject(name, model, collection, role="subject", outfit=None):
    """`model`: the job's resolved entry ({'kind': 'glb', 'path', 'height_m', ...} or {'kind': 'proxy'})."""
    H = float(model.get("height_m") or HEIGHTS[name.split("_")[0]])
    if model.get("kind") == "glb":
        return add_glb(name, dict(model, height_m=H), collection, role)
    return add_proxy(name.split("_")[0], H, collection, role, outfit=outfit)
