"""War standards for the heroes' chariots. Free, cloud Blender.

  b = banners.make("elephant_rope", height=7.0)       Karna's standard: the gold elephant's rope (hastikakshya) on maroon
  b.parent = chariot; b.location = (0, 1.2, 0)         the pole's foot; the cloth flies toward +X and ripples
  banners.animate(b, 1, 168)                           the cloth flutters over those frames

The emblem is drawn here with PIL (a coiled rope with a hanging loop and tassels, a gold border), so the standard reads
at a distance without a model. The bible (passport.md, line 12062 of the source) gives Karna's standard as the gold
elephant's rope; Arjuna's ape banner already exists as krk_ape_banner in the battle kit.
"""
import math, pathlib, tempfile
import bpy
import numpy as np
from PIL import Image, ImageDraw

EMBLEMS = {"elephant_rope": dict(field=(92, 18, 22), gold=(226, 170, 60), dark=(120, 70, 16))}


def _emblem_png(kind, w=512, h=768):
    E = EMBLEMS[kind]
    im = Image.new("RGB", (w, h), E["field"]); d = ImageDraw.Draw(im)
    b = 26
    d.rectangle((b // 2, b // 2, w - b // 2, h - b // 2), outline=E["gold"], width=b)
    for k in range(0, h, 48):                                          # small border studs
        d.ellipse((4, k + 18, 22, k + 36), fill=E["dark"]); d.ellipse((w - 22, k + 18, w - 4, k + 36), fill=E["dark"])
    cx, cy = w / 2, h * 0.40
    pts = []
    for i in range(700):                                               # the rope coiled in a loose spiral
        a = i / 700 * 2 * math.pi * 3.2
        r = 40 + 115 * i / 700
        pts.append((cx + r * math.cos(a), cy + r * 0.82 * math.sin(a)))
    for wdt, col in ((34, E["dark"]), (24, E["gold"])):
        d.line(pts, fill=col, width=wdt, joint="curve")
    for i in range(0, 700, 9):                                         # twist marks along the rope
        x, y = pts[i]; d.line((x - 7, y - 7, x + 7, y + 7), fill=E["dark"], width=4)
    end = pts[-1]                                                      # the hanging loop and two tassels
    loop = [(end[0] + 60 * math.sin(t / 30 * math.pi), end[1] + 140 * t / 30) for t in range(31)]
    for wdt, col in ((30, E["dark"]), (20, E["gold"])):
        d.line(loop, fill=col, width=wdt, joint="curve")
    for dx in (-36, 36):
        x0, y0 = cx + dx, h * 0.80
        d.polygon([(x0 - 22, y0 + 90), (x0 + 22, y0 + 90), (x0 + 6, y0), (x0 - 6, y0)], fill=E["gold"])
        d.ellipse((x0 - 16, y0 - 20, x0 + 16, y0 + 12), fill=E["gold"], outline=E["dark"], width=4)
    p = pathlib.Path(tempfile.gettempdir()) / f"banner_{kind}.png"; im.save(p)
    return p


def make(kind="elephant_rope", height=7.0, cloth=(1.6, 2.4)):
    root = bpy.data.objects.new(f"standard_{kind}", None); bpy.context.scene.collection.objects.link(root)
    gold = bpy.data.materials.new("standard_gold"); gold.use_nodes = True
    bs = gold.node_tree.nodes["Principled BSDF"]; bs.inputs["Base Color"].default_value = (0.75, 0.52, 0.14, 1)
    bs.inputs["Metallic"].default_value = 0.8; bs.inputs["Roughness"].default_value = 0.3
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=height, vertices=12, location=(0, 0, height / 2))
    pole = bpy.context.object; pole.name = f"{kind}_pole"; pole.data.materials.append(gold); pole.parent = root
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.11, location=(0, 0, height + 0.08))
    fin = bpy.context.object; fin.name = f"{kind}_finial"; fin.data.materials.append(gold); fin.parent = root
    cw, ch = cloth
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=24, y_subdivisions=32, size=1)
    c = bpy.context.object; c.name = f"{kind}_cloth"; c.parent = root
    for v in c.data.vertices:                                           # hangs from the top of the pole, flying toward +X
        u, w = v.co.x + 0.5, v.co.y + 0.5
        v.co = (u * cw + 0.05, 0.0, height - 0.15 - (1 - w) * ch)
    m = bpy.data.materials.new(f"{kind}_cloth"); m.use_nodes = True; nt = m.node_tree
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(str(_emblem_png(kind))); tex.image.pack()
    b2 = nt.nodes["Principled BSDF"]; b2.inputs["Roughness"].default_value = 0.75
    b2.inputs["Sheen Weight"].default_value = 0.4
    nt.links.new(tex.outputs["Color"], b2.inputs["Base Color"])
    c.data.materials.append(m)
    for p in c.data.polygons:
        p.use_smooth = True
    # flutter: a sine-band texture moved along the cloth by a "wind" empty, weighted toward the free edge
    g = c.vertex_groups.new(name="free")
    for v in c.data.vertices:
        a = max(v.co.x - 0.05, 0) / cw
        g.add([v.index], a ** 1.4, "REPLACE")
    wind = bpy.data.objects.new(f"{kind}_wind", None); bpy.context.scene.collection.objects.link(wind); wind.parent = root
    tx = bpy.data.textures.new(f"{kind}_flutter", "WOOD"); tx.wood_type = "BANDS"; tx.noise_basis_2 = "SIN"
    dm = c.modifiers.new("flutter", "DISPLACE"); dm.texture = tx; dm.direction = "Y"; dm.vertex_group = "free"
    dm.texture_coords = "OBJECT"; dm.texture_coords_object = wind; dm.strength = 0.32; dm.mid_level = 0.5
    sk = c.modifiers.new("solid", "SOLIDIFY"); sk.thickness = 0.008
    root["cloth"] = c.name; root["wind"] = wind.name
    return root


def animate(root, f0, f1, fps=24, speed=1.6):
    """the flutter travels along the cloth from frame f0 to f1 (linear, so it never eases to a stop)"""
    w = bpy.data.objects[root["wind"]]
    prefs = bpy.context.preferences.edit; old = prefs.keyframe_new_interpolation_type
    prefs.keyframe_new_interpolation_type = "LINEAR"
    for f in (f0, f1):
        w.location = (-speed * (f - f0) / fps, 0, 0); w.keyframe_insert("location", frame=f)
    prefs.keyframe_new_interpolation_type = old
