import bpy, sys, os, json, math
from mathutils import Vector
kit, layout, out, cam_label = sys.argv[1:5]
L = json.load(open(layout))
bpy.ops.wm.read_factory_settings(use_empty=True)
s = bpy.context.scene
def imp(name):
    p = os.path.join(kit, f"SM_{name}.fbx")
    if not os.path.exists(p): return None
    bpy.ops.import_scene.fbx(filepath=p)
    o = bpy.context.selected_objects[0]; o.hide_render = True; o.hide_viewport = True
    return o.data
proxy = {}
def proxy_mesh(name):
    if name in proxy: return proxy[name]
    base = name.split("@")[0]
    me = imp(base)
    if me is None:  # stand-in box sized like the real thing
        size = {"hst_white_horse": (0.6, 2.4, 1.7), "hst_war_elephant": (2.0, 4.5, 3.3), "krk_ape_banner": (0.4, 0.4, 12.0), "krk_war_tent": (10, 8, 6)}.get(base, (2.2, 3.5, 3.0))
        bpy.ops.mesh.primitive_cube_add(size=1); o = bpy.context.object
        o.scale = size; o.location.z = size[2] / 2
        bpy.ops.object.transform_apply(location=True, scale=True)
        m = bpy.data.materials.new(base); m.diffuse_color = (0.85, 0.65, 0.2, 1) if "chariot" in base else (0.35, 0.33, 0.32, 1)
        if "horse" in base: m.diffuse_color = (0.92, 0.92, 0.9, 1)
        o.data.materials.append(m); me = o.data; o.hide_render = True
    proxy[name] = me; return me
ter = imp(L["terrain"]); t = bpy.data.objects.new("terrain", ter); s.collection.objects.link(t)
def place(me, tr):
    o = bpy.data.objects.new("i", me); s.collection.objects.link(o)
    o.location = (tr[0] / 100, -tr[1] / 100, tr[2] / 100)
    o.rotation_euler = (0, 0, -math.radians(tr[3])); o.scale = (tr[4],) * 3
for name, g in L["groups"].items():
    me = proxy_mesh(name)
    for tr in g["instances"]: place(me, tr)
for h in L["heroes"]: place(proxy_mesh(h["mesh"]), h["t"])
for m in bpy.data.materials:
    if m.use_nodes:
        b = m.node_tree.nodes.get("Principled BSDF")
        if b: b.inputs["Base Color"].default_value = m.diffuse_color
    else:
        m.use_nodes = True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = m.diffuse_color
c = [c for c in L["cameras"] if c["label"] == cam_label][0]
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); s.collection.objects.link(cam); s.camera = cam
cam.location = (c["loc"][0] / 100, -c["loc"][1] / 100, c["loc"][2] / 100)
p, y = math.radians(c["rot"][0]), math.radians(c["rot"][1])
d = Vector((math.cos(p) * math.cos(y), -math.cos(p) * math.sin(y), math.sin(p)))
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
cam.data.angle = math.radians(c["fov"]); cam.data.clip_end = 10000
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); s.collection.objects.link(sun)
sp, sy_ = math.radians(L["sun"]["pitch"]), math.radians(L["sun"]["yaw"])
sd = Vector((math.cos(sp) * math.cos(sy_), -math.cos(sp) * math.sin(sy_), math.sin(sp)))
sun.rotation_euler = sd.to_track_quat('-Z', 'Y').to_euler(); sun.data.energy = 4; sun.data.color = (1, 0.8, 0.55)
w = bpy.data.worlds.new("w"); s.world = w; w.use_nodes = True
bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.75, 0.62, 0.48, 1); bg.inputs[1].default_value = 1.0
vol = w.node_tree.nodes.new("ShaderNodeVolumePrincipled"); vol.inputs["Density"].default_value = 0.0012
vol.inputs["Color"].default_value = (0.8, 0.62, 0.42, 1)

s.render.engine = "CYCLES"; s.cycles.samples = 32; s.cycles.use_denoising = False
s.render.resolution_x, s.render.resolution_y = 1280, 720
s.render.filepath = out
bpy.ops.render.render(write_still=True)
