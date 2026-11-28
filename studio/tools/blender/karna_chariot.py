"""Karna's chariot as used in the teaser: kit rank chariot (kit driver and kit archer cut out), Shalya at the
reins, Karna (karna_hero_v4, Vijaya bow in his left fist) standing behind him, the elephant's-rope standard,
and a dun team of Hastinapur horses.

    import karna_chariot
    ch, shalya, team, karna, bow = karna_chariot.build(rigged=True, reins_on=True)   # team["rigs"]: the horse rigs
"""
import pathlib
import bpy, bmesh
from mathutils import Vector

from anim_lib import Hero
import banners, horse_gaits, horse_team, moves, moves_ep01, reins
from bows import Bow

HERE = pathlib.Path(__file__).resolve().parent
STUDIO = HERE.parent.parent
KIT = pathlib.Path("/mnt/project-files/kurukshetra/hero/blend")
KARNA = STUDIO / "cast/karna/model/rig/karna_hero_v4.blend"
VIJAYA = STUDIO / "cast/karna/model/trellis_out/karna_bow_1536.glb"
KARNA_AT = (0, 0.35, 1.07)            # the kit archer's place on the raised rear floor


def append_kit(name):
    with bpy.data.libraries.load(str(KIT / f"SM_{name}.blend"), link=False) as (src, dst):
        dst.objects = list(src.objects)
    for o in dst.objects:
        bpy.context.scene.collection.objects.link(o)
    return dst.objects[0]


def _front(c, size):   # kit driver: body, bow, reins and the two lion figureheads
    return abs(c.x) < 1.2 and -2.2 < c.y < -0.3 and 0.9 < c.z < 3.0 and size < 2.2


def _archer(c, size):  # kit archer on the rear floor: legs, body, arms, head and bow (canopy ribs sit above z 2.95)
    return abs(c.x) < 0.5 and -0.3 < c.y < 0.65 and 1.0 < c.z < 2.95 and size < 1.7


def cut_kit_driver(ch, tests=(_front, _archer)):
    """cut every loose part that one of `tests` picks (by centre and size)"""
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
        if any(t(c, size) for t in tests):
            cut.extend(part)
    bmesh.ops.delete(bm, geom=cut, context="VERTS"); bm.to_mesh(ch.data); bm.free()
    return len(cut)


def build(rigged=True, reins_on=True, coat="dun", karna=True, bow_ratio=0.15, with_bow=True, subsurf=False):
    """bow_ratio decimates the 451k-vertex Vijaya after its string hooks (it is a thin prop at mid distance).
    subsurf=False turns off the heroes' render subdivision: with it on, Karna + Shalya + team pass the 16 GB cloud
    box. Turn it on for close-ups (one hero in frame) or on a bigger machine."""
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
    k = bow = None
    if karna:
        k = Hero.load(KARNA, "KARNA", loc=KARNA_AT, face=0); k.rig.parent = ch
        if with_bow:
            bow = Bow.vijaya(VIJAYA)
            k.reset(); moves.bow_draw(k, 1.6); bow.attach(k)
        if bow and bow_ratio < 1:                                   # apply it once: a live decimate re-runs on
            d = bow.obj.modifiers.new("lod", "DECIMATE"); d.ratio = bow_ratio   # every pose update and stalls keying
            with bpy.context.temp_override(object=bow.obj, active_object=bow.obj):
                bpy.ops.object.modifier_move_to_index(modifier="lod", index=0)
                bpy.ops.object.modifier_apply(modifier="lod")
        k.reset(); moves_ep01.stand_tall(k, 0.0); k.key_all(1)
    for hero in (h, k):
        if hero and not subsurf:                                    # the hero bodies' render subsurf costs ~5.5 GB each
            for m in hero.body.modifiers:                           # in the CPU renderers; mid-ground shots don't need it
                if m.type == "SUBSURF":
                    m.show_render = False
    bpy.context.view_layer.update()
    if rigged:
        rigs = [bpy.data.objects[n] for n in team["rigs"]]
        for r in rigs:
            horse_gaits.pose(r, "stand", 0)
        bpy.context.view_layer.update()
        if reins_on:
            reins.add(ch, h.rig, rigs)
    return ch, h, team, k, bow


def cpu_render_settings(scene, samples=24):
    """Cycles on the CPU for cloud checks: with Karna, Shalya and four horses, CPU EEVEE (llvmpipe) climbs past the
    16 GB box limit while it compiles shaders; Cycles stays near 3 GB. Finals still go to EEVEE on a GPU (pipeline step 10)."""
    scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"
    scene.cycles.samples = samples; scene.cycles.use_denoising = True; scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.cycles.max_bounces = 4; scene.cycles.use_adaptive_sampling = True
    scene.render.use_persistent_data = True                                 # keep the BVH between frames of a clip
