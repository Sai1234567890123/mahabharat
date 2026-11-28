"""Reins from a charioteer's fists to each horse's bit, re-strung every frame.

    import reins
    reins.add(chariot, hero_rig, [horse_rig, ...])      # horses 0-1 to the left fist, 2-3 to the right

Each rein is a bevelled curve parented to the chariot. A frame_change_post handler moves its ends to the
fist (middle of DEF-hand) and to the bit (a point fixed in the horse's head bone) and lets the middle sag,
so the reins follow Shalya's hands and the galloping heads. Call reins.update() after posing a still.
"""
import bpy
from mathutils import Vector

BIT = Vector((0.0, -1.07, 1.60))       # horse rest space: the bit ring at the corner of the mouth
SAG = 0.18                             # metres the middle drops on a 3 m rein
_REINS = []


def _mat():
    m = bpy.data.materials.get("MAT_rein_leather")
    if not m:
        m = bpy.data.materials.new("MAT_rein_leather")
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (0.16, 0.07, 0.03, 1); b.inputs["Roughness"].default_value = 0.6
    return m


def add(chariot, hero_rig, horse_rigs, bevel=0.009):
    for i, hr in enumerate(horse_rigs):
        side = "L" if i < len(horse_rigs) / 2 else "R"
        cu = bpy.data.curves.new(f"rein_{hr.name}", "CURVE"); cu.dimensions = "3D"
        cu.bevel_depth = bevel; cu.bevel_resolution = 2; cu.use_fill_caps = True
        sp = cu.splines.new("NURBS"); sp.points.add(4); sp.order_u = 4; sp.use_endpoint_u = True
        ob = bpy.data.objects.new(cu.name, cu); bpy.context.scene.collection.objects.link(ob)
        ob.parent = chariot; ob.data.materials.append(_mat())
        hb = hr.pose.bones["head"]
        bit = hb.bone.matrix_local.inverted() @ BIT          # bit in the head bone's rest space
        _REINS.append((ob, hero_rig, f"DEF-hand.{side}", hr, bit))
    if _handler not in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.append(_handler)
    update()


def update():
    for ob, hero, hand, hr, bit in _REINS:
        hb = hero.pose.bones[hand]
        a = hero.matrix_world @ ((hb.head + hb.tail) * 0.5)
        hd = hr.pose.bones["head"]
        b = hr.matrix_world @ (hd.matrix @ bit)
        inv = ob.matrix_world.inverted()
        L = (b - a).length
        for k, p in enumerate(ob.data.splines[0].points):
            u = k / 4
            q = a.lerp(b, u) - Vector((0, 0, 4 * SAG * (L / 3) * u * (1 - u)))
            p.co = (*(inv @ q), 1)


def _handler(scene, depsgraph=None):
    update()
