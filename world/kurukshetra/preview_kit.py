import bpy, sys, os, json, math
from mathutils import Vector
kit, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
man = json.load(open(os.path.join(kit,"manifest.json")))
for a in man["assets"]:
    if a["name"]=="KRK_Terrain": continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.join(kit,a["file"]))
    o=[x for x in bpy.context.scene.objects if x.type=="MESH"][0]
    s=bpy.context.scene; s.render.engine="CYCLES"; s.cycles.samples=24; s.cycles.device="CPU"
    s.cycles.use_denoising=False
    sun=bpy.data.objects.new("sun",bpy.data.lights.new("sun","SUN")); s.collection.objects.link(sun)
    sun.rotation_euler=(math.radians(50),math.radians(15),math.radians(30)); sun.data.energy=3
    s.render.resolution_x=s.render.resolution_y=400
    w=bpy.data.worlds.new("w"); s.world=w; w.use_nodes=True; w.node_tree.nodes["Background"].inputs[0].default_value=(0.45,0.45,0.45,1); w.node_tree.nodes["Background"].inputs[1].default_value=0.8
    d=max(o.dimensions); c=Vector((0,0,o.dimensions.z/2))
    cam=bpy.data.objects.new("c",bpy.data.cameras.new("c")); s.collection.objects.link(cam); s.camera=cam
    cam.location=c+Vector((1.3*d, -1.9*d, 1.0*d))
    cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.lens=50
    s.render.filepath=os.path.join(out,a["name"]+".png")
    bpy.ops.render.render(write_still=True)
