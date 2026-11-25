"""Small animation helpers for the rigged series heroes (cast/<hero>/model/rig/<hero>_hero_v*.blend). Free, cloud Blender.

Poses are set by direction, not by Rigify's local axes, so a sequence reads like a director's note:
  h = Hero.load(path, "KARNA", loc=(0, 0, 0), face=0)     # face: degrees to turn the hero about Z (0 = facing -Y)
  h.aim("upper_arm_fk.R", (0.2, -1, -0.3))                 # point the bone along a direction in the hero's own frame
  h.turn("head", "Z", 15)                                  # rotate a control about the hero's own axes (Z up, X his left, -Y front)
  h.fingers("R", curl=60, spread=0, point=False)           # +curl closes the hand (Rigify fingers, Z toward the palm)
  h.keys({"jaw_open": 0.4, "smile_L": 0.5})                # face shape keys; h.say(track, t) mixes Rhubarb visemes
  h.key_all(frame)                                         # keyframe every touched bone and shape key at this frame
Hero front is -Y, his left is +X, up is +Z. Arms and fingers are FK (IK_FK = 1); legs stay IK so planted feet stay planted.
"""
import json, math, pathlib
import bpy
from mathutils import Vector, Matrix, Quaternion


def ease(t, t0, t1):
    """0 before t0, 1 after t1, smooth in between"""
    if t1 <= t0:
        return float(t >= t1)
    u = min(max((t - t0) / (t1 - t0), 0.0), 1.0)
    return u * u * (3 - 2 * u)


def mix(a, b, u):
    if isinstance(a, (int, float)):
        return a + (b - a) * u
    return tuple(x + (y - x) * u for x, y in zip(a, b))


def track(t, keys):
    """keys: [(time, value), ...]; eased hold-to-hold interpolation (values can be numbers or tuples)"""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            return mix(v0, v1, ease(t, t0, t1))
    return keys[-1][1]


class Hero:
    def __init__(self, rig, body, head, visemes):
        self.rig, self.body, self.head, self.visemes = rig, body, head, visemes
        self.pb = rig.pose.bones
        self.touched, self.shapes = set(), set()

    @classmethod
    def load(cls, path, tag, loc=(0, 0, 0), face=0.0):
        path = str(pathlib.Path(path).resolve())
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            dst.objects = [n for n in src.objects if n.startswith((tag + "_", "FACE_"))]
        sc = bpy.context.scene
        for o in dst.objects:
            sc.collection.objects.link(o)
        rig = next(o for o in dst.objects if o.name.startswith(tag + "_rig"))
        body = next(o for o in dst.objects if o.name.startswith(tag + "_body"))
        head = next(o for o in dst.objects if o.name.startswith(tag + "_head"))
        rig.location = loc
        rig.rotation_euler = (0, 0, math.radians(face))
        for o in dst.objects:
            o.hide_viewport = False
        vis = {}
        vj = pathlib.Path(path).with_name(pathlib.Path(path).name.split("_hero_")[0] + "_hero_v1.visemes.json")
        if vj.exists():
            vis = json.loads(vj.read_text())
        h = cls(rig, body, head, vis)
        for side in "LR":
            h.pb[f"upper_arm_parent.{side}"]["IK_FK"] = 1.0      # arms in FK
        bpy.context.view_layer.update()
        return h

    # ---- bones -------------------------------------------------------------------------------------------------------------
    def _rest(self, name):
        pb = self.pb[name]
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
        bpy.context.view_layer.update()
        self.touched.add(name)
        return pb, self.rig.matrix_world @ pb.matrix

    def _set(self, pb, M):
        pb.matrix = self.rig.matrix_world.inverted() @ M
        bpy.context.view_layer.update()

    def W(self, v):
        """a direction in the hero's own frame, in world space"""
        return (self.rig.matrix_world.to_3x3() @ Vector(v)).normalized()

    def aim(self, name, d, roll=0.0):
        """point the bone (its Y axis) along direction d in the hero's frame; roll turns it about that direction"""
        pb, M0 = self._rest(name)
        d = self.W(d)
        q = M0.to_3x3().col[1].normalized().rotation_difference(d)
        if roll:
            q = Quaternion(d, math.radians(roll)) @ q
        R = q.to_matrix() @ M0.to_3x3()
        M = R.to_4x4(); M.translation = M0.translation
        self._set(pb, M)

    def turn(self, name, axis, deg, keep=False):
        """rotate a control about the hero's own X, Y or Z axis (through its head); keep=True adds to its current pose"""
        pb = self.pb[name]
        if keep:
            bpy.context.view_layer.update(); M0 = self.rig.matrix_world @ pb.matrix; self.touched.add(name)
            pb.rotation_mode = "QUATERNION"
        else:
            pb, M0 = self._rest(name)
        ax = self.W({"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}[axis])
        R = Quaternion(ax, math.radians(deg)).to_matrix() @ M0.to_3x3()
        M = R.to_4x4(); M.translation = M0.translation
        self._set(pb, M)

    def move(self, name, offset):
        """move a control (IK feet, torso) by an offset in the hero's frame, from its rest place"""
        pb = self.pb[name]
        self.touched.add(name)
        pb.location = (0, 0, 0)
        bpy.context.view_layer.update()
        M0 = self.rig.matrix_world @ pb.matrix
        M = M0.copy(); M.translation = M0.translation + self.rig.matrix_world.to_3x3() @ Vector(offset)
        self._set(pb, M)

    def fingers(self, side, curl=0.0, spread=0.0, point=False, thumb=None):
        """+curl closes the hand (degrees per joint); point keeps the index straight; spread fans the fingers"""
        th = curl * 0.55 if thumb is None else thumb
        for i, f in enumerate(["f_index", "f_middle", "f_ring", "f_pinky", "thumb"]):
            c = 0.0 if (point and f == "f_index") else (th if f == "thumb" else curl)
            for k in ("01", "02", "03"):
                n = f"{f}.{k}.{side}"
                if n in self.pb:
                    pb = self.pb[n]; pb.rotation_mode = "QUATERNION"
                    pb.rotation_quaternion = Quaternion((1, 0, 0), math.radians(c))
                    self.touched.add(n)
            m = f"{f}.01_master.{side}"
            if m in self.pb and f != "thumb":
                pb = self.pb[m]; pb.rotation_mode = "QUATERNION"
                pb.rotation_quaternion = Quaternion((0, 0, 1), math.radians(spread * (i - 1.5)))
                self.touched.add(m)
        bpy.context.view_layer.update()

    # ---- face ----------------------------------------------------------------------------------------------------------------
    def keys(self, values):
        kb = self.head.data.shape_keys.key_blocks
        for k, v in values.items():
            if k in kb:
                kb[k].value = float(v); self.shapes.add(k)

    def say(self, line, t, blend=0.06):
        """line: [(start_s, viseme), ...] in Rhubarb letters (A-H, X); returns mouth shape weights at time t"""
        out = {k: 0.0 for k in ("jaw_open", "mouth_wide", "mouth_round", "mouth_press")}
        for i, (t0, v) in enumerate(line):
            t1 = line[i + 1][0] if i + 1 < len(line) else t0 + 10
            w = ease(t, t0 - blend, t0 + blend) * (1 - ease(t, t1 - blend, t1 + blend))
            for k, x in self.visemes.get(v, {}).items():
                out[k] = out.get(k, 0.0) + w * x
        return out

    def key_all(self, frame):
        for n in self.touched:
            pb = self.pb[n]
            if pb.rotation_mode == "QUATERNION":
                pb.keyframe_insert("rotation_quaternion", frame=frame)
            else:
                pb.keyframe_insert("rotation_euler", frame=frame)
            pb.keyframe_insert("location", frame=frame)
        kb = self.head.data.shape_keys.key_blocks
        for k in self.shapes:
            kb[k].keyframe_insert("value", frame=frame)

    def reset(self):
        for n in self.touched:
            pb = self.pb[n]; pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.location = (0, 0, 0)
        for k in self.shapes:
            self.head.data.shape_keys.key_blocks[k].value = 0.0
        bpy.context.view_layer.update()
