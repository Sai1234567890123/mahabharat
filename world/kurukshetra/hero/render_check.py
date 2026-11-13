"""Three-quarter check render of whatever meshes are in the current scene (Cycles CPU)."""
import math

import bpy
from mathutils import Vector


def render(path, res=(1024, 1024), samples=48, az=-40.0, el=14.0, dist_mul=1.0, target=None, lens=60,
           sun_el=22.0, sun_az=-120.0, ground=True):
    s = bpy.context.scene
    objs = [o for o in s.objects if o.type == "MESH"]
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for o in objs:
        for v in o.data.vertices:
            for k in range(3):
                lo[k] = min(lo[k], v.co[k])
                hi[k] = max(hi[k], v.co[k])
    c = (lo + hi) / 2 if target is None else Vector(target)
    size = (hi - lo).length
    if ground:
        bpy.ops.mesh.primitive_plane_add(size=400, location=(c.x, c.y, lo.z - 0.001))
        g = bpy.context.object
        m = bpy.data.materials.new("ground")
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (0.36, 0.24, 0.15, 1)
        b.inputs["Roughness"].default_value = 0.95
        g.data.materials.append(m)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    s.collection.objects.link(cam)
    s.camera = cam
    cam.data.lens = lens
    a, e = math.radians(az), math.radians(el)
    d = size * 1.25 * dist_mul * (lens / 50)
    cam.location = c + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * d
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.clip_end = 5000
    w = bpy.data.worlds.new("w")
    s.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    bg.inputs[0].default_value = (0.62, 0.70, 0.86, 1)     # soft warm-day sky fill
    bg.inputs[1].default_value = 0.55
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    s.collection.objects.link(sun)
    sa, se = math.radians(sun_az), math.radians(sun_el)
    sd = -Vector((math.sin(sa) * math.cos(se), -math.cos(sa) * math.cos(se), math.sin(se)))
    sun.rotation_euler = sd.to_track_quat("-Z", "Y").to_euler()
    sun.data.energy = 3.2
    sun.data.color = (1.0, 0.86, 0.68)
    sun.data.angle = math.radians(3)
    s.render.engine = "CYCLES"
    s.cycles.device = "CPU"
    s.cycles.samples = samples
    try:
        s.cycles.use_denoising = True
        s.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        s.cycles.use_denoising = False
    try:
        s.view_settings.view_transform = "Standard"
    except Exception:
        pass
    s.render.resolution_x, s.render.resolution_y = res
    s.render.filepath = path
    bpy.ops.render.render(write_still=True)
