"""Rig the Hastinapur TRELLIS horse for animation (A05 gallop, A02/A16 trot and stand).

    EGL_PLATFORM=surfaceless python3 horse_rig.py [<out.blend>]
       default out: studio/assets/hastinapur/hst_white_horse_rig.blend

1. Decimates the 590k-triangle GLB to about 90k triangles (UVs and texture kept), for animation and crowds.
2. Builds a 21-bone skeleton from measured landmarks (horse faces -Y, hooves at z 0):
   root, hips, chest, neck.1, neck.2, head, tail.1, tail.2 and three bones per leg (upper, fore/gaskin, cannon).
3. Skins with Blender's bone-heat weights; if heat fails on this mesh it falls back to distance weights
   limited by side and region, so a leg never drags the saddle-cloth or the other leg.
Names: HORSE_rig and HORSE_body. Gaits live in horse_gaits.py.
"""
import pathlib, sys
import bpy, bmesh
import numpy as np
from mathutils import Vector

HERE = pathlib.Path(__file__).resolve().parent
ASSETS = HERE.parents[1] / "assets/hastinapur"
GLB = ASSETS / "hst_white_horse.glb"
OUT = pathlib.Path(sys.argv[-1]).resolve() if sys.argv[-1].endswith(".blend") else ASSETS / "hst_white_horse_rig.blend"
TARGET_TRIS = 90_000

# head, tail, parent, (region for the fallback weights)
FX, HX = 0.17, 0.17
BONES = {
    "root":     ((0, 0.05, 1.20), (0, -0.25, 1.20), None),
    "hips":     ((0, 0.10, 1.38), (0, 0.75, 1.36), "root"),
    "chest":    ((0, 0.10, 1.38), (0, -0.48, 1.52), "root"),
    "neck.1":   ((0, -0.48, 1.52), (0, -0.66, 1.86), "chest"),
    "neck.2":   ((0, -0.66, 1.86), (0, -0.80, 2.12), "neck.1"),
    "head":     ((0, -0.80, 2.12), (0, -1.12, 1.58), "neck.2"),
    "tail.1":   ((0, 1.08, 1.36), (0, 1.16, 1.00), "hips"),
    "tail.2":   ((0, 1.16, 1.00), (0, 1.10, 0.58), "tail.1"),
}
for s, x in (("L", FX), ("R", -FX)):
    BONES[f"fore_upper.{s}"] = ((x, -0.36, 1.26), (x, -0.43, 0.86), "chest")
    BONES[f"fore_arm.{s}"] = ((x, -0.43, 0.86), (x, -0.39, 0.44), f"fore_upper.{s}")
    BONES[f"fore_cannon.{s}"] = ((x, -0.39, 0.44), (x, -0.42, 0.03), f"fore_arm.{s}")
for s, x in (("L", HX), ("R", -HX)):
    BONES[f"hind_thigh.{s}"] = ((x, 0.52, 1.30), (x, 0.60, 0.92), "hips")
    BONES[f"hind_gaskin.{s}"] = ((x, 0.60, 0.92), (x, 0.88, 0.56), f"hind_thigh.{s}")
    BONES[f"hind_cannon.{s}"] = ((x, 0.88, 0.56), (x, 0.74, 0.03), f"hind_gaskin.{s}")


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(GLB))
    body = next(o for o in bpy.data.objects if o.type == "MESH")
    body.name = body.data.name = "HORSE_body"
    body.rotation_mode = "XYZ"
    for o in list(bpy.data.objects):
        if o is not body:
            bpy.data.objects.remove(o)
    n0 = len(body.data.polygons)
    dec = body.modifiers.new("dec", "DECIMATE"); dec.ratio = TARGET_TRIS / n0
    bpy.context.view_layer.objects.active = body; body.select_set(True)
    bpy.ops.object.modifier_apply(modifier="dec")
    print("decimated", n0, "->", len(body.data.polygons))

    arm = bpy.data.armatures.new("HORSE_rig"); rig = bpy.data.objects.new("HORSE_rig", arm)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    eb = {}
    for name, (h, t, p) in BONES.items():
        b = arm.edit_bones.new(name); b.head, b.tail = Vector(h), Vector(t)
        b.align_roll(Vector((1, 0, 0)))          # local X = world X, so every gait swing is a turn about X
        eb[name] = b
    for name, (h, t, p) in BONES.items():
        if p:
            eb[name].parent = eb[p]; eb[name].use_connect = (Vector(h) - eb[p].tail).length < 1e-4
    bpy.ops.object.mode_set(mode="OBJECT")
    for b in arm.bones:
        b.use_deform = b.name != "root"
    body.parent = rig

    ok = heat_weights(body, rig)
    if not ok:
        distance_weights(body)
    mod = body.modifiers.new("rig", "ARMATURE"); mod.object = rig
    print("weights", "bone heat" if ok else "distance fallback")
    return rig, body


def heat_weights(body, rig):
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True); rig.select_set(True); bpy.context.view_layer.objects.active = rig
    try:
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    except RuntimeError as e:
        print("heat failed:", e); return False
    for m in list(body.modifiers):
        if m.type == "ARMATURE":
            body.modifiers.remove(m)
    # heat leaves unweighted islands silently: count them
    groups = {g.index for g in body.vertex_groups}
    bad = sum(1 for v in body.data.vertices if not any(g.group in groups and g.weight > 0.01 for g in v.groups))
    print("unweighted verts after heat", bad, "of", len(body.data.vertices))
    if bad > 0.01 * len(body.data.vertices):
        for g in list(body.vertex_groups):
            body.vertex_groups.remove(g)
        return False
    return True


def _seg_dist(P, a, b):
    ab = b - a; t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


def distance_weights(body):
    co = np.empty(len(body.data.vertices) * 3); body.data.vertices.foreach_get("co", co); P = co.reshape(-1, 3)
    names = [n for n in BONES if n != "root"]
    radius = {n: (0.30 if n in ("hips", "chest") else 0.16 if n.startswith(("neck", "head")) else 0.06) for n in names}
    D = np.stack([_seg_dist(P, np.array(BONES[n][0]), np.array(BONES[n][1])) - radius[n] for n in names], 1)
    D = np.maximum(D, 0.005)
    legzone = P[:, 2] < 0.95                                              # below the belly line only legs move
    for j, n in enumerate(names):
        side = n.endswith(".L") and 1 or n.endswith(".R") and -1 or 0
        if side:
            D[(np.sign(P[:, 0]) != side) & (np.abs(P[:, 0]) > 0.03), j] = 9
            if not n.startswith(("fore_upper", "hind_thigh")):
                D[~legzone, j] = 9                                       # lower leg bones never reach the barrel
        elif n in ("hips", "chest") or n.startswith(("neck", "head")):
            D[legzone & (np.abs(P[:, 0]) < 0.26) & ~((P[:, 1] > 0.95) | (P[:, 1] < -0.6)), j] *= 3
    W = D ** -4; W /= W.sum(1, keepdims=True)
    for j, n in enumerate(names):
        g = body.vertex_groups.new(name=n)
        for i in np.nonzero(W[:, j] > 0.02)[0]:
            g.add([int(i)], float(W[i, j]), "REPLACE")


if __name__ == "__main__":
    rig, body = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT), compress=True)
    print("saved", OUT, round(OUT.stat().st_size / 1e6, 1), "MB")
