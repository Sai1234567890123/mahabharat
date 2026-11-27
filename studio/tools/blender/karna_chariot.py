"""Karna's chariot as used in the teaser: kit rank chariot (kit driver cut out), Shalya at the reins,
the elephant's-rope standard, and a dun team of Hastinapur horses.

    import karna_chariot
    ch, shalya, team = karna_chariot.build(rigged=True, reins_on=True)   # team["rigs"] holds the horse rigs
"""
import pathlib
import bpy, bmesh
from mathutils import Vector

from anim_lib import Hero
import banners, horse_gaits, horse_team, moves_ep01, reins

HERE = pathlib.Path(__file__).resolve().parent
STUDIO = HERE.parent.parent
KIT = pathlib.Path("/mnt/project-files/kurukshetra/hero/blend")


def append_kit(name):
    with bpy.data.libraries.load(str(KIT / f"SM_{name}.blend"), link=False) as (src, dst):
        dst.objects = list(src.objects)
    for o in dst.objects:
        bpy.context.scene.collection.objects.link(o)
    return dst.objects[0]


def cut_kit_driver(ch):
    """every loose part on the front of the car: the kit driver's body, bow, reins and the two lion figureheads"""
    bm = bmesh.new(); bm.from_mesh(ch.data); bm.verts.ensure_lookup_table()
    seen, cut = set(), []
    for v0 in bm.verts:
        if v0 in seen:
            continue
        part, stack = [], [v0]
        while stack:
            v = stack.pop()
            if v in seen:
                continue
            seen.add(v); part.append(v); stack.extend(e.other_vert(v) for e in v.link_edges)
        xs = [v.co.x for v in part]; ys = [v.co.y for v in part]; zs = [v.co.z for v in part]
        c = Vector((sum(xs), sum(ys), sum(zs))) / len(part)
        size = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
        if abs(c.x) < 1.2 and -2.2 < c.y < -0.3 and 0.9 < c.z < 3.0 and size < 2.2:
            cut.extend(part)
    bmesh.ops.delete(bm, geom=cut, context="VERTS"); bm.to_mesh(ch.data); bm.free()
    return len(cut)


def build(rigged=True, reins_on=True, coat="dun"):
    ch = append_kit("krk_rank_chariot")
    for m in ch.data.materials:
        if m and m.name.startswith("MAT_Saffron"):
            m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.36, 0.05, 0.06, 1)
    team = horse_team.make(ch, coat=coat, name="karna_team", rigged=rigged)
    std = banners.make("elephant_rope", height=7.0); std.parent = ch; std.location = (1.25, 2.9, 0.6)
    print("cut kit driver verts", cut_kit_driver(ch))
    h = Hero.load(STUDIO / "cast/shalya/model/rig/shalya_hero_v1.blend", "SHALYA", loc=(0, -1.0, 0.84), face=0)
    h.rig.parent = ch
    h.reset(); moves_ep01.charioteer(h, 0.4); h.key_all(1)
    bpy.context.view_layer.update()
    if rigged:
        rigs = [bpy.data.objects[n] for n in team["rigs"]]
        for r in rigs:
            horse_gaits.pose(r, "stand", 0)
        bpy.context.view_layer.update()
        if reins_on:
            reins.add(ch, h.rig, rigs)
    return ch, h, team
