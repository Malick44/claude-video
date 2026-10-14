"""Mesh building inside Blender: one bmesh per figure, parts tagged with their material.

Runs only inside Blender (imports bpy/bmesh). Every proxy and set piece is built from these parts, so a
figure is one object with several material slots (cheap to render, cheap to hash for the rigidity check).
All sizes are metres; `rot` is an XYZ Euler in radians; parts are placed with an explicit matrix, so
nothing depends on the 3D cursor, selection or operator context.
"""
import math

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector


def xform(loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    return Matrix.Translation(Vector(loc)) @ Euler(rot, "XYZ").to_matrix().to_4x4() @ Matrix.Diagonal((*scale, 1.0))


class Builder:
    """Accumulates parts into one bmesh. `to_object()` makes the mesh object with one slot per material."""

    def __init__(self):
        self.bm = bmesh.new()
        self.mats = []

    def _slot(self, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def _tag(self, verts, mat, smooth=True):
        idx = self._slot(mat)
        faces = {f for v in verts for f in v.link_faces}
        for f in faces:
            f.material_index = idx
            f.smooth = smooth and len(f.verts) <= 4   # ngon caps stay flat
        return verts

    # ---- primitives (centred, then moved by the matrix)
    def sphere(self, mat, loc, radius, scale=(1, 1, 1), rot=(0, 0, 0), seg=(32, 16), smooth=True):
        r = bmesh.ops.create_uvsphere(self.bm, u_segments=seg[0], v_segments=seg[1], radius=radius,
                                      matrix=xform(loc, rot, scale))
        return self._tag(r["verts"], mat, smooth)

    def ico(self, mat, loc, radius, subdiv=2, scale=(1, 1, 1), rot=(0, 0, 0), smooth=True):
        r = bmesh.ops.create_icosphere(self.bm, subdivisions=subdiv, radius=radius, matrix=xform(loc, rot, scale))
        return self._tag(r["verts"], mat, smooth)

    def cone(self, mat, base, r1, r2, depth, rot=(0, 0, 0), seg=32, scale=(1, 1, 1), smooth=True, cap=True):
        """A (truncated) cone standing on `base` along its local +Z."""
        m = xform(base, rot, scale) @ Matrix.Translation((0, 0, depth / 2))
        r = bmesh.ops.create_cone(self.bm, cap_ends=cap, cap_tris=False, segments=seg, radius1=r1, radius2=r2,
                                  depth=depth, matrix=m)
        return self._tag(r["verts"], mat, smooth)

    def cyl(self, mat, base, radius, depth, rot=(0, 0, 0), seg=32, scale=(1, 1, 1), smooth=True):
        return self.cone(mat, base, radius, radius, depth, rot, seg, scale, smooth)

    def box(self, mat, loc, size, rot=(0, 0, 0)):
        r = bmesh.ops.create_cube(self.bm, size=1.0, matrix=xform(loc, rot, size))
        return self._tag(r["verts"], mat, False)

    def disc(self, mat, loc, radius, rot=(0, 0, 0), seg=48, scale=(1, 1, 1)):
        r = bmesh.ops.create_circle(self.bm, cap_ends=True, segments=seg, radius=radius, matrix=xform(loc, rot, scale))
        return self._tag(r["verts"], mat, False)

    def quad(self, mat, loc, size_xy, rot=(0, 0, 0)):
        r = bmesh.ops.create_grid(self.bm, x_segments=1, y_segments=1, size=0.5,
                                  matrix=xform(loc, rot, (size_xy[0], size_xy[1], 1)))
        return self._tag(r["verts"], mat, False)

    def torus(self, mat, loc, R, r, rot=(0, 0, 0), seg=(48, 12), scale=(1, 1, 1)):
        m = xform(loc, rot, scale)
        rings = []
        for i in range(seg[0]):
            a = 2 * math.pi * i / seg[0]
            ring = []
            for j in range(seg[1]):
                b = 2 * math.pi * j / seg[1]
                p = Vector(((R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a), r * math.sin(b)))
                ring.append(self.bm.verts.new(m @ p))
            rings.append(ring)
        verts = [v for ring in rings for v in ring]
        for i in range(seg[0]):
            a, b = rings[i], rings[(i + 1) % seg[0]]
            for j in range(seg[1]):
                self.bm.faces.new((a[j], b[j], b[(j + 1) % seg[1]], a[(j + 1) % seg[1]]))
        return self._tag(verts, mat, True)

    def tube(self, mat, points, radii, seg=20, cap=True):
        """Sweep a circle along a polyline (parallel-transport frames). `radii` is one radius per point."""
        pts = [Vector(p) for p in points]
        n = len(pts)
        tangents = []
        for i in range(n):
            a = pts[max(i - 1, 0)]
            b = pts[min(i + 1, n - 1)]
            tangents.append((b - a).normalized())
        up = Vector((0, 0, 1)) if abs(tangents[0].z) < 0.9 else Vector((1, 0, 0))
        normal = tangents[0].cross(up).normalized()
        rings = []
        for i in range(n):
            t = tangents[i]
            if i:   # parallel transport the normal
                prev = tangents[i - 1]
                axis = prev.cross(t)
                if axis.length > 1e-9:
                    ang = prev.angle(t)
                    normal = (Matrix.Rotation(ang, 3, axis.normalized()) @ normal).normalized()
            bino = t.cross(normal).normalized()
            ring = []
            for j in range(seg):
                a = 2 * math.pi * j / seg
                ring.append(self.bm.verts.new(pts[i] + radii[i] * (math.cos(a) * normal + math.sin(a) * bino)))
            rings.append(ring)
        for i in range(n - 1):
            a, b = rings[i], rings[i + 1]
            for j in range(seg):
                self.bm.faces.new((a[j], a[(j + 1) % seg], b[(j + 1) % seg], b[j]))
        if cap:
            self.bm.faces.new(list(reversed(rings[0])))
            self.bm.faces.new(rings[-1])
        verts = [v for ring in rings for v in ring]
        return self._tag(verts, mat, True)

    def to_object(self, name, collection=None, parent=None):
        me = bpy.data.meshes.new(name)
        self.bm.normal_update()
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(name, me)
        (collection or bpy.context.scene.collection).objects.link(ob)
        if parent is not None:
            ob.parent = parent
        return ob


def bezier(p0, p1, p2, p3, n=24):
    """Points on a cubic Bezier."""
    p0, p1, p2, p3 = (Vector(p) for p in (p0, p1, p2, p3))
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append(u * u * u * p0 + 3 * u * u * t * p1 + 3 * u * t * t * p2 + t * t * t * p3)
    return out


def empty(name, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), collection=None):
    ob = bpy.data.objects.new(name, None)
    (collection or bpy.context.scene.collection).objects.link(ob)
    ob.parent = parent
    ob.location = loc
    ob.rotation_euler = rot
    return ob
