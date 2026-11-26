"""Kurukshetra backdrop for the 3D episode shots, built from the battle kit (/mnt/project-files/kurukshetra/hero/blend).

  import battlefield
  bf = battlefield.build(seed=3, density=1.0, haze=True)      # call after the scene and world exist
  bf.sun(elev=32, azim=20)                                    # a key sun for the battle day (optional)

Layout (metres; the battle line runs along X):
  the centre (|y| < 38) is left clear for the heroes; Pandava host to the south (y < 0) facing +Y, Kaurava host to the
  north (y > 0) facing -Y; each host has a front line of chariots, infantry ranks, elephants among the rear ranks,
  cavalry on both wings, drum carts behind, and the camp tents far back; the field between holds a few wrecks and
  spent arrows (no bodies, no gore). The ground is flat near the centre and rolls gently further out.
Soldiers, horses and tents are geometry-node instances of the kit meshes (one copy each in memory), so tens of
thousands render in Cycles on CPU. Kit fronts are -Y.
"""
import math, random
import bpy
from mathutils import Vector

KIT = "/mnt/project-files/kurukshetra/hero/blend/SM_{}.blend"


def _load(name, coll):
    with bpy.data.libraries.load(KIT.format(name), link=False) as (src, dst):
        dst.objects = [n for n in src.objects]
    o = next(x for x in dst.objects if x.type == "MESH")
    coll.objects.link(o)
    o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0)
    return o


def _points_object(name, pts, coll):
    """a vertex cloud carrying the instance index, yaw and scale per point"""
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(pts)); me.vertices.foreach_set("co", [c for p in pts for c in p[0]])
    for attr, typ, k in (("inst", "INT", 1), ("yaw", "FLOAT", 2), ("scl", "FLOAT", 3)):
        a = me.attributes.new(attr, typ, "POINT"); a.data.foreach_set("value", [p[k] for p in pts])
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    ng = bpy.data.node_groups.new(name + "_gn", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
    ci = N.new("GeometryNodeCollectionInfo"); ci.inputs["Collection"].default_value = coll
    ci.inputs["Separate Children"].default_value = True; ci.inputs["Reset Children"].default_value = True
    ip = N.new("GeometryNodeInstanceOnPoints"); ip.inputs["Pick Instance"].default_value = True
    na_i = N.new("GeometryNodeInputNamedAttribute"); na_i.data_type = "INT"; na_i.inputs["Name"].default_value = "inst"
    na_y = N.new("GeometryNodeInputNamedAttribute"); na_y.data_type = "FLOAT"; na_y.inputs["Name"].default_value = "yaw"
    na_s = N.new("GeometryNodeInputNamedAttribute"); na_s.data_type = "FLOAT"; na_s.inputs["Name"].default_value = "scl"
    cx = N.new("ShaderNodeCombineXYZ"); e2r = N.new("FunctionNodeEulerToRotation")
    L.new(gi.outputs[0], ip.inputs["Points"]); L.new(ci.outputs[0], ip.inputs["Instance"])
    L.new(na_i.outputs["Attribute"], ip.inputs["Instance Index"])
    L.new(na_y.outputs["Attribute"], cx.inputs["Z"]); L.new(cx.outputs[0], e2r.inputs[0]); L.new(e2r.outputs[0], ip.inputs["Rotation"])
    L.new(na_s.outputs["Attribute"], ip.inputs["Scale"])
    L.new(ip.outputs["Instances"], go.inputs[0])
    md = o.modifiers.new("instances", "NODES"); md.node_group = ng
    return o


class Battlefield:
    def __init__(self):
        self.objects = []

    def sun(self, elev=32, azim=20, energy=4.0):
        l = bpy.data.lights.new("battle_sun", "SUN"); l.energy = energy; l.angle = math.radians(1.5); l.color = (1.0, 0.9, 0.76)
        o = bpy.data.objects.new("battle_sun", l); bpy.context.scene.collection.objects.link(o)
        o.rotation_euler = (math.radians(90 - elev), 0, math.radians(azim))
        return o


def build(seed=3, density=1.0, haze=True, ground=True):
    rnd = random.Random(seed)
    bf = Battlefield()
    lib = bpy.data.collections.new("krk_kit")                         # sources for the instances; not in the scene
    names = ["pandava_archer", "pandava_archer_b", "kaurava_soldier", "kaurava_soldier_b", "pandava_cavalry",
             "kaurava_cavalry", "war_elephant", "war_elephant_red", "rank_chariot", "rank_chariot_red",
             "war_drum_cart", "war_tent", "war_tent_red", "chariot_wreck", "arrow_cluster", "horse_white"]
    for i, n in enumerate(names):
        o = _load("krk_" + n, lib); o.name = f"{i:02d}_{n}"
    I = {n: i for i, n in enumerate(names)}
    pts = []

    def put(kind, x, y, yaw, s=1.0, jitter=0.0):
        pts.append(((x + rnd.uniform(-jitter, jitter), y + rnd.uniform(-jitter, jitter), 0.0), I[kind],
                    yaw + rnd.uniform(-0.06, 0.06), s * rnd.uniform(0.96, 1.04)))

    for side in (-1, 1):                                               # -1 Pandavas (south), +1 Kauravas (north)
        yaw = math.pi if side < 0 else 0.0                             # kit front -Y; Pandavas turn to face +Y
        inf = ("pandava_archer", "pandava_archer_b") if side < 0 else ("kaurava_soldier", "kaurava_soldier_b")
        cav = "pandava_cavalry" if side < 0 else "kaurava_cavalry"
        cha = "rank_chariot" if side < 0 else "rank_chariot_red"
        ele = "war_elephant" if side < 0 else "war_elephant_red"
        tent = "war_tent" if side < 0 else "war_tent_red"
        for x in range(-260, 261, 24):                                 # front line of chariots
            put(cha, x + rnd.uniform(-5, 5), side * rnd.uniform(40, 47), yaw)
        step = 1.9 / math.sqrt(max(density, 0.05))
        y0 = 55
        rows = int(26 * min(density, 1.5))
        for r in range(rows):                                          # infantry ranks, in blocks with lanes between
            y = side * (y0 + r * 2.3)
            x = -250.0
            while x < 250:
                if (x + 250) % 50 > 3.5:                               # a lane every 50 m
                    put(inf[rnd.random() < 0.3], x, y, yaw, jitter=0.35)
                x += step
        for k in range(14):                                            # elephants among the rear ranks
            put(ele, rnd.uniform(-230, 230), side * rnd.uniform(y0 + rows * 2.3 + 6, y0 + rows * 2.3 + 30), yaw)
        for wing in (-1, 1):                                           # cavalry on both wings
            for r in range(10):
                for c in range(26):
                    put(cav, wing * (275 + c * 2.4), side * (48 + r * 4.0), yaw, jitter=0.5)
        for k in range(5):
            put("war_drum_cart", rnd.uniform(-200, 200), side * rnd.uniform(130, 150), yaw)
        for k in range(36):                                            # the camp, far back
            put(tent, rnd.uniform(-420, 420), side * rnd.uniform(330, 520), yaw + rnd.uniform(-0.5, 0.5), s=1.0)
    for k in range(7):                                                 # the field between: wrecks and spent arrows
        x, y = rnd.uniform(-150, 150), rnd.uniform(-30, 30)
        if abs(x) > 18 or abs(y) > 12:
            put("chariot_wreck", x, y, rnd.uniform(0, 6.28))
    for k in range(90):
        x, y = rnd.uniform(-160, 160), rnd.uniform(-34, 34)
        if abs(x) > 6 or abs(y) > 6:
            put("arrow_cluster", x, y, rnd.uniform(0, 6.28), s=rnd.uniform(0.6, 1.0))
    bf.instances = _points_object("krk_hosts", pts, lib)
    print("battlefield instances:", len(pts), flush=True)
    if ground:
        bf.ground = _ground(rnd)
    if haze:
        bf.haze = _haze()
    return bf


def _ground(rnd):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=220, y_subdivisions=220, size=1600)
    g = bpy.context.object; g.name = "krk_ground"
    for v in g.data.vertices:                                          # flat at the centre, gentle rolls outside 120 m
        r = math.hypot(v.co.x, v.co.y)
        k = min(max((r - 120) / 200, 0), 1)
        v.co.z = k * (1.4 * math.sin(v.co.x * 0.011 + 1.3) * math.cos(v.co.y * 0.009) + 0.8 * math.sin(v.co.x * 0.023 - v.co.y * 0.017))
    for p in g.data.polygons:
        p.use_smooth = True
    m = bpy.data.materials.new("krk_ground"); m.use_nodes = True; nt = m.node_tree
    b = nt.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.95
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    n1 = nt.nodes.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = 0.06; n1.inputs["Detail"].default_value = 6
    n2 = nt.nodes.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 1.2; n2.inputs["Detail"].default_value = 10
    nt.links.new(geo.outputs["Position"], n1.inputs["Vector"]); nt.links.new(geo.outputs["Position"], n2.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "FLOAT"; mx.inputs[0].default_value = 0.4
    nt.links.new(n1.outputs["Fac"], mx.inputs[2]); nt.links.new(n2.outputs["Fac"], mx.inputs[3])
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position = 0.35; cr.color_ramp.elements[0].color = (0.2, 0.13, 0.07, 1)
    cr.color_ramp.elements[1].position = 0.7; cr.color_ramp.elements[1].color = (0.46, 0.32, 0.18, 1)
    nt.links.new(mx.outputs[0], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], b.inputs["Base Color"])
    bm = nt.nodes.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = 0.3
    nt.links.new(n2.outputs["Fac"], bm.inputs["Height"]); nt.links.new(bm.outputs["Normal"], b.inputs["Normal"])
    g.data.materials.append(m)
    return g


def _haze():
    """low dust haze over the field: a thin volume, densest near the ground"""
    bpy.ops.mesh.primitive_cube_add(size=1); v = bpy.context.object; v.name = "krk_haze"
    v.scale = (1500, 1500, 40); v.location = (0, 0, 20)
    m = bpy.data.materials.new("krk_haze"); m.use_nodes = True; nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    pv = nt.nodes.new("ShaderNodeVolumePrincipled"); pv.inputs["Color"].default_value = (0.86, 0.72, 0.55, 1)
    geo = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0; mr.inputs["From Max"].default_value = 30
    mr.inputs["To Min"].default_value = 0.0005; mr.inputs["To Max"].default_value = 0.0
    nt.links.new(geo.outputs["Position"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], pv.inputs["Density"])
    nt.links.new(pv.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    v.data.materials.append(m); v.visible_shadow = False
    sc = bpy.context.scene; sc.cycles.volume_step_rate = 8; sc.cycles.volume_max_steps = 64
    return v
