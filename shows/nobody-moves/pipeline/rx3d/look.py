"""The shared reenactment look: glossy, saturated, cheesy true-crime TV (docs/BLENDER_REENACTMENTS.md §5.2).

Runs only inside Blender. Materials (plastic with a clear coat, metals, laser beams, fire, dust, the dark
door and window surfaces, the final-quality haze volume), lights, the painted world, the compositor (glare fed
from the Emission pass and the `glint` AOV only, so clear-coat highlights never streak), colour management
(AgX, "AgX - Punchy") and the engine/quality settings.

Colour calibration (measured in Blender 5.0.1, review_tests/agx_grid.png): AgX - Punchy desaturates bright
emitters toward white. #FF1A1A emission reads (212,54,34) at strength 1.5, (239,102,85) at 3, (254,145,133) at 6
and salmon-pink (255,166,157) at 9. So a "saturated" emitter (laser, fire) keeps its body at strength 0.8-2.0
and only a thin core goes hot: beam() and fire() drive strength through a facing term, not a flat value.
Standard keeps the red but clips the white glaze and the beard, so the view transform stays AgX.
"""
import math
import warnings

import bpy
from mathutils import Vector

# ---------------------------------------------------------------- palette (sRGB hex; converted to linear)
PAL = {
    "key": "#FFE2C0", "rim_m": "#FF2D9B", "rim_c": "#2DE2FF", "trim": "#F4F4F0",
    "door": "#0B0B0E", "window": "#07070C", "brass": "#C9A227", "lantern": "#FFC56B",
    "laser": "#FF1A1A", "step": "#9A9A98", "hosta": "#2E8B57", "petal": "#D3559B", "cone": "#B5541B",
    "stem": "#3E9B3A", "soil": "#2A1A10", "spark": "#FFB347", "ember": "#FFB347", "dust": "#8E877D",
    # defaults a template palette overrides
    "sky_lo": "#3A2C8C", "sky_hi": "#7B4FD1", "siding": "#8C93A3", "siding_band": "#6E7586", "lawn": "#2FB34A",
    "lawn_noise": "#279C3F", "moon": "#FFF1CF", "haze": "#D6D2E6", "fill": "#B9A8FF", "set_flood": "#9C88FF",
}
# Per-template grades, so later episodes inherit them. Heist: red/violet. Action (the Director's Cut): teal/orange,
# the fire the only warm thing in the frame.
PALETTES = {
    "heist": {"sky_lo": "#3A2C8C", "sky_hi": "#241A5E", "siding": "#5A6074", "siding_band": "#4A4F62",
              "lawn": "#3BD45A", "lawn_noise": "#2FB34A", "moon": "#E8ECFF", "haze": "#D6D2E6", "fill": "#B9A8FF",
              "set_flood": "#6E5BD6", "kicker": "#FF6F9A"},
    "action": {"sky_lo": "#1F5A7A", "sky_hi": "#0E2A47", "siding": "#4E5868", "siding_band": "#3F4857",
               "lawn": "#2FB34A", "lawn_noise": "#279C3F", "haze": "#9DB8C8", "fill": "#A9C8DC",
               "set_flood": "#7FB8D8", "fire_back": "#FF6A00", "rim_fill": "#2DE2FF", "fascia": "#262B36"},
}
# Fire: emission colour and strength by heat (noise), multiplied by a core term so the rim stays dark smoke.
# AgX keeps 0.8-2.0 saturated: #C22A00 at 1.0 and #FF6A00 at 1.8 read (172,64,0) to (212,64,22).
FIRE_STOPS = ((0.00, "#2A0A00", 0.0), (0.30, "#C22A00", 1.0), (0.50, "#FF6A00", 1.8), (0.72, "#FFB000", 3.5),
              (1.00, "#FFF1C0", 8.0))
FIRE_MAX = 8.0
# Dark surfaces (doors, windows): rough and uncoated, so no light's specular highlight reads as a light inside the
# house (docs/BLENDER_REENACTMENTS.md §5.2). check_rules enforces it on every material tagged rx_kind "dark_surface".
DARK_MIN_ROUGH = 0.45


def palette(name):
    return {**PAL, **PALETTES.get(name, {})}


def lin(hexc):
    h = hexc.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def rgba(hexc):
    return (*lin(hexc), 1.0)


def _new(name):
    m = bpy.data.materials.new(name)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m.use_nodes = True
    nt = m.node_tree
    return m, nt, nt.nodes, nt.links


def _value_node(nodes, name, value):
    v = nodes.new("ShaderNodeValue")
    v.name = v.label = name
    v.outputs[0].default_value = value
    return v


def _math(N, L, op, a, b=None, name=None):
    n = N.new("ShaderNodeMath")
    n.operation = op
    if name:
        n.name = name
    for i, x in enumerate((a, b)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            n.inputs[i].default_value = x
        else:
            L.new(x, n.inputs[i])
    return n.outputs[0]


def _core(N, L, power, blend=0.5):
    """(1 - Layer Weight Facing) ** power: 1 where the surface faces the camera (a beam's or a ball's core),
    0 at grazing angles (the sheath, the rim)."""
    lw = N.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = blend
    inv = _math(N, L, "SUBTRACT", 1.0, lw.outputs["Facing"])
    return _math(N, L, "POWER", inv, float(power))


def key_value(mat, node_name, frame, value):
    """Keyframe a Value node (laser hum, glint spike, fireball heat): one key per frame, no curves."""
    n = mat.node_tree.nodes[node_name]
    n.outputs[0].default_value = value
    n.outputs[0].keyframe_insert("default_value", frame=frame)


# ---------------------------------------------------------------- materials
def plastic(name, hexc, rough=0.3, coat=1.0, metal=0.0, coat_rough=0.03, ior_level=0.6, stripe=False):
    """The plastic look: saturated base, clear coat. `stripe` adds the faint 45-degree proxy stripe (12%)."""
    m, nt, N, L = _new(name)
    b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = rgba(hexc)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = coat_rough
    b.inputs["Specular IOR Level"].default_value = ior_level
    if stripe:
        tc = N.new("ShaderNodeTexCoord")
        wave = N.new("ShaderNodeTexWave")
        wave.wave_type = "BANDS"
        wave.bands_direction = "DIAGONAL"
        wave.inputs["Scale"].default_value = 18.0
        L.new(tc.outputs["Object"], wave.inputs["Vector"])
        mr = N.new("ShaderNodeMapRange")
        mr.inputs["To Min"].default_value = 0.0
        mr.inputs["To Max"].default_value = 0.12
        L.new(wave.outputs["Factor"], mr.inputs["Value"])
        mix = N.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.inputs[6].default_value = rgba(hexc)
        c = lin(hexc)
        mix.inputs[7].default_value = (c[0] * 0.55, c[1] * 0.55, c[2] * 0.55, 1)
        L.new(mr.outputs["Result"], mix.inputs[0])
        L.new(mix.outputs[2], b.inputs["Base Color"])
    m["rx_kind"] = "plastic"
    return m


def dark(name, hexc, rough=0.5):
    """A dark door or window: rough and uncoated (rough >= 0.45, coat 0). A glossy black door mirrored the key
    light as 'a light under the door' once the subject stopped hiding it (review: door_compare.png)."""
    m = plastic(name, hexc, rough=max(rough, DARK_MIN_ROUGH), coat=0.0)
    m["rx_kind"] = "dark_surface"
    return m


def matte(name, hexc, rough=0.6, noise_hex=None, noise_scale=40.0, spec=0.4):
    """No coat (a coated lawn turns into a mirror). Optional noise mix for lichen or soil. Ground seen from grass
    height takes spec ~0.05: at a grazing angle even a rough dielectric mirrors the sky and reads grey, not green."""
    m, nt, N, L = _new(name)
    b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = rgba(hexc)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = 0.0
    b.inputs["Specular IOR Level"].default_value = spec
    if noise_hex:
        tc = N.new("ShaderNodeTexCoord")
        nz = N.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = noise_scale
        L.new(tc.outputs["Object"], nz.inputs["Vector"])
        mix = N.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.inputs[6].default_value = rgba(hexc)
        mix.inputs[7].default_value = rgba(noise_hex)
        mr = N.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.5
        mr.inputs["From Max"].default_value = 0.75
        L.new(nz.outputs["Factor"], mr.inputs["Value"])
        L.new(mr.outputs["Result"], mix.inputs[0])
        L.new(mix.outputs[2], b.inputs["Base Color"])
    m["rx_kind"] = "matte"
    return m


def glass(name, hexc="#FFFFFF", ior=1.33):
    m, nt, N, L = _new(name)
    b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = rgba(hexc)
    b.inputs["Roughness"].default_value = 0.02
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = ior
    return m


def emissive(name, hexc, strength, aov=None):
    """Pure, opaque emission (moon, lantern, sparks, embers, glints). The strength comes from a Value node named
    'strength' so it can be keyed per frame. `aov` also writes colour x strength into that AOV (glints).
    Always opaque (DITHERED): a BLENDED material writes no render passes on Eevee, so its glare would vanish
    there. A sprite that must disappear is keyed to scale 0 instead (check_rules enforces this)."""
    m, nt, N, L = _new(name)
    N.remove(N["Principled BSDF"])
    out = N["Material Output"]
    e = N.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = rgba(hexc)
    s = _value_node(N, "strength", strength)
    L.new(s.outputs[0], e.inputs["Strength"])
    L.new(e.outputs[0], out.inputs["Surface"])
    if aov:
        a = N.new("ShaderNodeOutputAOV")
        a.aov_name = aov
        vm = N.new("ShaderNodeVectorMath")
        vm.operation = "SCALE"
        vm.inputs[0].default_value = lin(hexc)
        L.new(s.outputs[0], vm.inputs["Scale"])
        L.new(vm.outputs[0], a.inputs["Color"])
    m["rx_kind"] = "emissive"
    return m


def beam(name, hexc, lo=1.4, hi=6.0, power=4.0):
    """A laser: strength = mix(lo, hi, core ** power) x 'strength' (the hum, 1.0 nominal). The sheath stays in
    AgX's saturated range, about (212,50,30) for #FF1A1A at 1.4, and only a thin core goes hot and blooms."""
    m, nt, N, L = _new(name)
    N.remove(N["Principled BSDF"])
    out = N["Material Output"]
    e = N.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = rgba(hexc)
    core = _core(N, L, power, blend=0.5)
    mr = N.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = lo
    mr.inputs["To Max"].default_value = hi
    L.new(core, mr.inputs["Value"])
    s = _value_node(N, "strength", 1.0)
    L.new(_math(N, L, "MULTIPLY", mr.outputs["Result"], s.outputs[0]), e.inputs["Strength"])
    L.new(e.outputs[0], out.inputs["Surface"])
    m["rx_kind"] = "emissive"
    m["rx_saturated"] = True
    return m


def fire(name, noise_scale=2.4, core_power=1.5, smoke="#2A0A00"):
    """A fireball surface. Heat = 4D noise (node 'noise', W keyed per frame) through FIRE_STOPS: colour and
    strength both follow the heat, x core ** 1.5 so the rim stays dark smoke and only the core goes white-hot,
    x 'strength' (keyed: the ignition flash, the flicker, the land burst). A dark diffuse smoke layer is added
    underneath, so cold patches read as smoke rather than holes."""
    m, nt, N, L = _new(name)
    N.remove(N["Principled BSDF"])
    out = N["Material Output"]
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise")
    nz.name = "noise"
    nz.noise_dimensions = "4D"
    nz.inputs["Scale"].default_value = noise_scale
    nz.inputs["Detail"].default_value = 6.0
    nz.inputs["Roughness"].default_value = 0.6
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    heat = N.new("ShaderNodeMapRange")
    heat.name = "heat"
    heat.inputs["From Min"].default_value = 0.30
    heat.inputs["From Max"].default_value = 0.72
    L.new(nz.outputs["Factor"], heat.inputs["Value"])
    core = _core(N, L, core_power, blend=0.45)
    # hotter toward the core: heat x (0.55 + 0.45 core) keeps the rim in the red/smoke stops
    hc = _math(N, L, "MULTIPLY", heat.outputs["Result"], _math(N, L, "ADD", _math(N, L, "MULTIPLY", core, 0.45), 0.55))
    cr = N.new("ShaderNodeValToRGB")
    sr = N.new("ShaderNodeValToRGB")
    for ramp in (cr, sr):
        while len(ramp.color_ramp.elements) < len(FIRE_STOPS):
            ramp.color_ramp.elements.new(0.5)
    for i, (pos, hexc, st) in enumerate(FIRE_STOPS):
        cr.color_ramp.elements[i].position = pos
        cr.color_ramp.elements[i].color = rgba(hexc)
        sr.color_ramp.elements[i].position = pos
        g = st / FIRE_MAX
        sr.color_ramp.elements[i].color = (g, g, g, 1.0)
    L.new(hc, cr.inputs["Fac"])
    L.new(hc, sr.inputs["Fac"])
    s = _value_node(N, "strength", 1.0)
    st = _math(N, L, "MULTIPLY", _math(N, L, "MULTIPLY", sr.outputs["Color"], FIRE_MAX), core)
    st = _math(N, L, "MULTIPLY", st, s.outputs[0])
    e = N.new("ShaderNodeEmission")
    L.new(cr.outputs["Color"], e.inputs["Color"])
    L.new(st, e.inputs["Strength"])
    sm = N.new("ShaderNodeBsdfDiffuse")
    sm.inputs["Color"].default_value = rgba(smoke)
    add = N.new("ShaderNodeAddShader")
    L.new(sm.outputs[0], add.inputs[0])
    L.new(e.outputs[0], add.inputs[1])
    L.new(add.outputs[0], out.inputs["Surface"])
    m["rx_kind"] = "emissive"
    m["rx_saturated"] = True
    return m


def additive(name, hexc, strength, noise=True, facing=False, noise_scale=1.6):
    """Additive haze: Transparent + Emission x mask (the god-ray cone card in preview/draft). The mask is 4D
    noise (W keyed per frame for the drift, node 'noise') and/or a facing falloff (soft edges). BLENDED on
    Eevee to sort the card; it writes no passes there, which is fine: it feeds no glare."""
    m, nt, N, L = _new(name)
    N.remove(N["Principled BSDF"])
    out = N["Material Output"]
    tr = N.new("ShaderNodeBsdfTransparent")
    e = N.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = rgba(hexc)
    add = N.new("ShaderNodeAddShader")
    s = _value_node(N, "strength", strength)
    mask = s.outputs[0]
    if noise:
        tc = N.new("ShaderNodeTexCoord")
        nz = N.new("ShaderNodeTexNoise")
        nz.name = "noise"
        nz.noise_dimensions = "4D"
        nz.inputs["Scale"].default_value = noise_scale
        nz.inputs["Detail"].default_value = 1.0
        L.new(tc.outputs["Object"], nz.inputs["Vector"])
        mr = N.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.35
        mr.inputs["From Max"].default_value = 0.75
        L.new(nz.outputs["Factor"], mr.inputs["Value"])
        mask = _math(N, L, "MULTIPLY", mask, mr.outputs["Result"])
    if facing:
        mask = _math(N, L, "MULTIPLY", mask, _core(N, L, 1.0, blend=0.6))
    L.new(mask, e.inputs["Strength"])
    L.new(tr.outputs[0], add.inputs[0])
    L.new(e.outputs[0], add.inputs[1])
    L.new(add.outputs[0], out.inputs["Surface"])
    if hasattr(m, "surface_render_method"):
        m.surface_render_method = "BLENDED"
    m["rx_kind"] = "card"
    return m


def dust(name, hexc, rough=0.9, edge_power=2.0):
    """A concrete-dust puff: Mix(Transparent, Principled) by alpha = the object's colour alpha (keyed per frame:
    peak about 0.25) x core ** 2, so each puff has soft edges instead of reading as a white egg."""
    m, nt, N, L = _new(name)
    b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = rgba(hexc)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = 0.0
    b.inputs["Specular IOR Level"].default_value = 0.2
    out = N["Material Output"]
    tr = N.new("ShaderNodeBsdfTransparent")
    oi = N.new("ShaderNodeObjectInfo")
    alpha = _math(N, L, "MULTIPLY", oi.outputs["Alpha"], _core(N, L, edge_power, blend=0.5))
    mix = N.new("ShaderNodeMixShader")
    L.new(alpha, mix.inputs[0])
    L.new(tr.outputs[0], mix.inputs[1])
    L.new(b.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs["Surface"])
    if hasattr(m, "surface_render_method"):
        m.surface_render_method = "BLENDED"
    m["rx_kind"] = "dust"
    return m


def haze_volume(name, density, hexc=PAL["haze"], noise_scale=None):
    """Final quality: a Principled Volume. `noise_scale` modulates the density with 4D noise (node 'noise', W keyed
    per frame for the drift), so the haze reads as drifting smoke rather than an even veil. Costlier on a CPU
    (ray marching); finals render on a GPU."""
    m, nt, N, L = _new(name)
    N.remove(N["Principled BSDF"])
    out = N["Material Output"]
    v = N.new("ShaderNodeVolumePrincipled")
    v.inputs["Color"].default_value = rgba(hexc)
    v.inputs["Anisotropy"].default_value = 0.35
    v.inputs["Density"].default_value = density
    if noise_scale:
        tc = N.new("ShaderNodeTexCoord")
        nz = N.new("ShaderNodeTexNoise")
        nz.name = "noise"
        nz.noise_dimensions = "4D"
        nz.inputs["Scale"].default_value = noise_scale
        nz.inputs["Detail"].default_value = 2.0
        L.new(tc.outputs["Generated"], nz.inputs["Vector"])
        mr = N.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 0.3, 0.7
        mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 0.25, 1.75
        L.new(nz.outputs["Factor"], mr.inputs["Value"])
        L.new(_math(N, L, "MULTIPLY", mr.outputs["Result"], density), v.inputs["Density"])
    L.new(v.outputs[0], out.inputs["Volume"])
    m["rx_kind"] = "volume"
    return m


def restyle(mat):
    """Plastic look on an imported (GLB) Principled material: keep the base colour texture, coat it,
    clamp roughness, drop baked emission (docs/BLENDER_REENACTMENTS.md §4.1)."""
    if not mat or not mat.node_tree:
        return
    for n in mat.node_tree.nodes:
        if n.bl_idname != "ShaderNodeBsdfPrincipled":
            continue
        n.inputs["Coat Weight"].default_value = 1.0
        n.inputs["Coat Roughness"].default_value = 0.03
        r = n.inputs["Roughness"]
        if not r.is_linked:
            r.default_value = min(r.default_value, 0.35)
        n.inputs["Emission Strength"].default_value = 0.0


# ---------------------------------------------------------------- world, lights
def world(scene, lo=PAL["sky_lo"], hi=PAL["sky_hi"], strength=1.0):
    w = bpy.data.worlds.new("rx_sky")
    scene.world = w
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        w.use_nodes = True
    N, L = w.node_tree.nodes, w.node_tree.links
    bg = N["Background"]
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Generated"], sep.inputs[0])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = rgba(lo)
    ramp.color_ramp.elements[1].position = 0.55
    ramp.color_ramp.elements[1].color = rgba(hi)
    mr = N.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -0.05
    mr.inputs["From Max"].default_value = 0.6
    L.new(sep.outputs["Z"], mr.inputs["Value"])
    L.new(mr.outputs["Result"], ramp.inputs[0])
    L.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    return w


def _aim(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def area(name, loc, target, hexc, energy, size=0.5, collection=None, shape="DISK", glossy=True):
    """An area light, invisible to the camera. glossy=False for set floods: a big disc mirrored in the black
    door or a dark window reads as a second moon."""
    L = bpy.data.lights.new(name, "AREA")
    L.energy = energy
    L.size = size
    L.shape = shape
    L.color = lin(hexc)
    ob = bpy.data.objects.new(name, L)
    (collection or bpy.context.scene.collection).objects.link(ob)
    ob.location = loc
    _aim(ob, target)
    ob.visible_camera = False
    ob.visible_glossy = glossy
    return ob


def spot(name, loc, target, hexc, energy, angle_deg=35, blend=0.4, radius=0.05, collection=None):
    L = bpy.data.lights.new(name, "SPOT")
    L.energy = energy
    L.spot_size = math.radians(angle_deg)
    L.spot_blend = blend
    L.shadow_soft_size = radius
    L.color = lin(hexc)
    ob = bpy.data.objects.new(name, L)
    (collection or bpy.context.scene.collection).objects.link(ob)
    ob.location = loc
    _aim(ob, target)
    ob.visible_camera = False
    return ob


def point(name, loc, hexc, energy, radius=0.03, collection=None):
    L = bpy.data.lights.new(name, "POINT")
    L.energy = energy
    L.shadow_soft_size = radius
    L.color = lin(hexc)
    ob = bpy.data.objects.new(name, L)
    (collection or bpy.context.scene.collection).objects.link(ob)
    ob.location = loc
    ob.visible_camera = False
    return ob


def link(light_ob, objects):
    """Light linking (Cycles and Eevee, Blender 4.x/5.0): the light shades only `objects`. The subject's key, rims
    and kicker then never flood the set: the subject stays the brightest thing in the frame and the lawn at the
    lens doesn't wash out."""
    c = bpy.data.collections.new(f"{light_ob.name}_receivers")
    for o in objects:
        if o.name not in c.objects:
            c.objects.link(o)
    light_ob.light_linking.receiver_collection = c
    return light_ob


def key_energy(light_ob, k, energy):
    light_ob.data.energy = energy
    light_ob.data.keyframe_insert("energy", frame=k + 1)


# ---------------------------------------------------------------- compositor and colour
def compositor(scene, quality, streaks=0.55, bloom=0.7, ghosts=0.9, glint_streaks=1.0, mist=None, nframes=1):
    """Glare from the Emission pass (Streaks: 2 anamorphic streaks at 0 deg; Bloom over threshold 1.0, so only
    the hot cores bloom) and from the `glint` AOV (Ghosts, plus a long anamorphic Streaks: the lens flare reads
    at least 40% of the frame wide), each added onto the beauty image. Beauty highlights never feed the glare.
    `mist` (preview/draft haze): the Mist pass x a drifting 4D noise blends the image toward the haze colour,
    before the glare."""
    vl = scene.view_layers[0]
    vl.use_pass_emit = True
    if "glint" not in [a.name for a in vl.aovs]:
        a = vl.aovs.add()
        a.name = "glint"
        a.type = "COLOR"
    ng = bpy.data.node_groups.new("rx_comp", "CompositorNodeTree")
    ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    N, L = ng.nodes, ng.links
    rl = N.new("CompositorNodeRLayers")
    q = {"preview": "Low", "draft": "Medium", "final": "High", "selftest": "Low"}.get(quality, "Medium")

    def glare(kind, src, threshold, strength, **kw):
        g = N.new("CompositorNodeGlare")
        g.inputs["Type"].default_value = kind
        g.inputs["Quality"].default_value = q
        g.inputs["Threshold"].default_value = threshold
        g.inputs["Strength"].default_value = strength
        for k, v in kw.items():
            g.inputs[k].default_value = v
        L.new(src, g.inputs["Image"])
        return g.outputs["Glare"]

    img = rl.outputs["Image"]
    if mist:
        vl.use_pass_mist = True
        ms = scene.world.mist_settings
        ms.start, ms.depth, ms.falloff = mist["start"], mist["depth"], "QUADRATIC"
        ic = N.new("CompositorNodeImageCoordinates")
        L.new(rl.outputs["Image"], ic.inputs["Image"])
        nz = N.new("ShaderNodeTexNoise")
        nz.noise_dimensions = "4D"
        nz.inputs["Scale"].default_value = 2.2
        nz.inputs["Detail"].default_value = 2.0
        L.new(ic.outputs["Normalized"], nz.inputs["Vector"])
        mr = N.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 0.3, 0.75
        mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 0.35, 1.25
        L.new(nz.outputs["Factor"], mr.inputs["Value"])
        m1 = N.new("ShaderNodeMath")
        m1.operation = "MULTIPLY"
        L.new(rl.outputs["Mist"], m1.inputs[0])
        L.new(mr.outputs["Result"], m1.inputs[1])
        m2 = N.new("ShaderNodeMath")
        m2.operation = "MULTIPLY"
        m2.inputs[1].default_value = mist["strength"]
        L.new(m1.outputs[0], m2.inputs[0])
        mix = N.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "SCREEN"
        L.new(m2.outputs[0], mix.inputs[0])
        L.new(img, mix.inputs[6])
        c = lin(mist.get("hex", PAL["haze"]))
        mix.inputs[7].default_value = (c[0] * 0.6, c[1] * 0.6, c[2] * 0.6, 1)
        img = mix.outputs[2]
        for k in range(nframes):
            nz.inputs["W"].default_value = mist["w0"] + mist["speed"] * k / 30.0
            nz.inputs["W"].keyframe_insert("default_value", frame=k + 1)
    em = rl.outputs["Emission"]
    layers = []
    if streaks:
        layers.append(glare("Streaks", em, 1.2, streaks, Streaks=2, **{"Streaks Angle": 0.0, "Fade": 0.92}))
    if bloom:
        layers.append(glare("Bloom", em, 1.0, bloom, Size=0.6))
    if ghosts:
        layers.append(glare("Ghosts", rl.outputs["glint"], 0.05, ghosts))
    if glint_streaks:
        layers.append(glare("Streaks", rl.outputs["glint"], 0.05, glint_streaks, Streaks=2,
                            **{"Streaks Angle": 0.0, "Fade": 0.985}))
    for g in layers:
        mix = N.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "ADD"
        mix.inputs[0].default_value = 1.0
        L.new(img, mix.inputs[6])
        L.new(g, mix.inputs[7])
        img = mix.outputs[2]
    out = N.new("NodeGroupOutput")
    L.new(img, out.inputs[0])
    scene.compositing_node_group = ng
    return ng


def colour(scene, exposure=0.0):
    vs = scene.view_settings
    vs.view_transform = "AgX"
    vs.look = "AgX - Punchy"
    vs.exposure = exposure
    vs.gamma = 1.0
    scene.display_settings.display_device = "sRGB"


# ---------------------------------------------------------------- engine and quality
GPU_TYPES = ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI")


def use_gpu(gpu_type):
    """Turn on the Cycles devices of `gpu_type` and prove one is active. Without this check Cycles quietly
    renders on the CPU when the worker finds no device of that type (an old driver for OptiX,
    CUDA_VISIBLE_DEVICES, a container without /dev/nvidia*), while the sidecar says 'gpu'.
    Returns {'type', 'devices'} for result.json and the sidecar."""
    prefs = bpy.context.preferences.addons["cycles"].preferences
    t = gpu_type or "OPTIX"
    prefs.compute_device_type = t
    try:
        prefs.refresh_devices()
    except Exception:
        prefs.get_devices()
    names = sorted({f"{d.type}:{d.name}" for d in prefs.devices})
    devs = [d for d in prefs.devices if d.type == t]
    if not devs:
        raise RuntimeError(f"--device gpu: the worker found no {t} device (devices seen: {', '.join(names) or 'none'})")
    for d in prefs.devices:
        d.use = d.type == t
    if not prefs.has_active_device():
        raise RuntimeError(f"--device gpu: no {t} device became active ({', '.join(d.name for d in devs)})")
    return {"type": t, "devices": [d.name for d in devs]}


def apply_render(scene, R, seed):
    """R: job['render'] = {engine, device, samples, scale, denoise, bounces, threads, ...}. Returns the device
    actually used: {'engine', 'device', 'type', 'devices'}."""
    r = scene.render
    r.resolution_x, r.resolution_y = 1080, 1920
    r.resolution_percentage = int(R["scale"])
    r.fps = 30
    r.use_motion_blur = False
    r.film_transparent = False
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGB"
    r.image_settings.color_depth = "8"
    r.use_compositing = True
    r.use_persistent_data = True          # keep the synced scene between the frames of one worker
    for attr in dir(r):                   # no date/time/render-time metadata in the PNGs: same pixels, same bytes
        if attr.startswith("use_stamp"):
            try:
                setattr(r, attr, False)
            except (AttributeError, TypeError):
                pass
    if R.get("threads"):
        r.threads_mode = "FIXED"
        r.threads = int(R["threads"])
    if R["engine"] == "eevee":
        r.engine = "BLENDER_EEVEE"
        e = scene.eevee
        e.taa_render_samples = int(R["samples"])
        if hasattr(e, "use_raytracing"):
            e.use_raytracing = R["quality"] == "final"
        if hasattr(e, "volumetric_end"):
            e.volumetric_end = 40.0
            e.volumetric_tile_size = "4" if R["quality"] == "final" else "8"
        return {"engine": "eevee", "device": "gpu", "type": None, "devices": []}
    r.engine = "CYCLES"
    c = scene.cycles
    c.samples = int(R["samples"])
    c.seed = int(seed) % 2147483647
    c.use_animated_seed = False
    c.use_adaptive_sampling = True
    c.use_denoising = bool(R["denoise"])
    if R["denoise"]:
        try:
            c.denoiser = "OPTIX" if R.get("denoiser") == "optix" else "OPENIMAGEDENOISE"
        except TypeError:
            pass
    b = R["bounces"]
    c.max_bounces, c.diffuse_bounces, c.glossy_bounces = b, min(b, 3), min(b, 4)
    c.transmission_bounces, c.transparent_max_bounces = min(b + 2, 8), 16
    c.volume_bounces = 1 if R["haze"] == "volume" else 0
    if hasattr(c, "volume_step_rate"):
        c.volume_step_rate = 2.0
    c.caustics_reflective = c.caustics_refractive = False
    c.sample_clamp_indirect = 10.0
    if R["device"] == "gpu":
        dev = use_gpu(R.get("gpu_type"))
        c.device = "GPU"
        return {"engine": "cycles", "device": "gpu", **dev}
    c.device = "CPU"
    return {"engine": "cycles", "device": "cpu", "type": None, "devices": []}
