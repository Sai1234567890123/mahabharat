"""Battle moves library for the rigged heroes (anim_lib.Hero). Free, cloud Blender.

Each move is a function of the hero and a time t (seconds from the start of the move); call it once per frame after
h.reset() and before h.key_all(frame). Directions follow anim_lib: hero front -Y, his left +X, up +Z.
arm() takes directions written for the LEFT arm with x pointing out to his side; the right arm is mirrored.

  bow_draw(h, t)       0.0-1.6 s  bow arm up toward the target (his left, +X), string hand draws to the jaw, holds
  bow_release(h, t)    0.0-0.8 s  from full draw: string hand flies back past the ear, fingers open, bow arm follows through
  block(h, t)          0.0-1.0 s  steps back, forearms cross up before the face, chin down, then recovers
  dodge(h, t, side)    0.0-1.0 s  ducks and slips to one side (+1 his left, -1 his right), weight on the outside foot
  run(h, t)            loops      run cycle in place (move the rig for travel): flight phase, pumping arms, forward lean
  RUN_SPEED            m/s the run cycle travels, so feet do not slide when the rig is moved by RUN_SPEED * t

Archer convention: the bow is in his LEFT hand, he draws with his RIGHT, the target is to his left (+X); the
string hand's palm point is bow_string_point(h) so a bow rig can follow it.
"""
import math
import bpy
from mathutils import Vector, Quaternion
from anim_lib import ease, track, mix


def arm(h, s, up, fo, ha, roll=0.0, palm=None):
    """aim the FK arm; directions for the left arm (x out to his side), mirrored for the right"""
    sx = 1 if s == "L" else -1
    h.aim(f"upper_arm_fk.{s}", (up[0] * sx, up[1], up[2]))
    h.aim(f"forearm_fk.{s}", (fo[0] * sx, fo[1], fo[2]))
    h.aim(f"hand_fk.{s}", (ha[0] * sx, ha[1], ha[2]), roll * sx)
    if palm:
        palm_to(h, s, (palm[0] * sx, palm[1], palm[2]))


def palm_to(h, s, want):
    """turn the hand about its own length so the palm (the fingers' +Z) faces direction want (hero frame)"""
    bpy.context.view_layer.update()
    pb = h.pb[f"hand_fk.{s}"]; M = h.rig.matrix_world @ pb.matrix
    y = M.to_3x3().col[1].normalized()
    n = (h.rig.matrix_world @ h.pb[f"f_middle.01.{s}"].matrix).to_3x3().col[2].normalized()
    w = h.W(want)
    n = (n - y * n.dot(y)).normalized(); w = (w - y * w.dot(y)).normalized()
    ang = math.atan2(y.dot(n.cross(w)), n.dot(w))
    R = Quaternion(y, ang).to_matrix() @ M.to_3x3()
    Mn = R.to_4x4(); Mn.translation = M.translation
    h._set(pb, Mn)


def lerp(a, b, u):
    return tuple(mix(x, y, u) for x, y in zip(a, b))


DOWN = ((0.15, 0.02, -1), (0.08, -0.15, -1), (0.05, -0.12, -1))
# archery, left arm (bow arm) -----------------------------------------------------------------------------------------------
BOW_LOW = ((0.45, -0.55, -0.7), (0.55, -0.75, -0.3), (0.5, -0.8, -0.2))          # bow held low and forward, ready
BOW_UP = ((1, -0.05, 0.08), (1, -0.02, 0.1), (1, 0, 0.12))                       # straight at the target
BOW_FOLLOW = ((1, 0.08, 0.02), (1, 0.12, 0.0), (1, 0.15, -0.05))                 # after the shot, drifts back a little
# right arm (string arm), written for his left side and mirrored, so x is out to his RIGHT, -x is toward the target
NOCK = ((0.0, -0.75, -0.65), (-0.8, -0.6, 0.0), (-0.9, -0.4, 0.05))            # string hand at the bow, low
SET = ((-0.25, -0.55, 0.8), (-1, -0.1, 0.1), (-1, 0, 0.1))                     # raised, both hands at the target line
ANCHOR = ((0.92, 0.25, 0.12), (-0.9, -0.38, 0.12), (-0.9, -0.3, 0.1))            # elbow back at shoulder height, hand at the jaw
LOOSE = ((0.75, 0.6, 0.25), (0.35, 0.9, 0.1), (0.2, 0.95, -0.1))                # hand flies back past the ear


def _stance(h, u):
    """archer's stance: feet apart, side on to the target (+X); u 0..1 blends it in"""
    h.move("foot_ik.L", (0.10 * u, 0.06 * u, 0)); h.move("foot_ik.R", (-0.12 * u, -0.04 * u, 0))
    h.move("torso", (0.01 * u, 0, -0.03 * u))
    h.turn("head", "Z", 78 * u)                                         # looks along the arrow, at the target
    h.turn("chest", "Z", 6 * u, keep=True)


def bow_draw(h, t):
    """0.0-0.35 nock low, 0.35-0.8 raise (set), 0.8-1.4 draw to anchor, then hold"""
    s = ease(t, 0.0, 0.5)
    _stance(h, s)
    up = ease(t, 0.3, 0.8)
    arm(h, "L", *lerp(BOW_LOW, BOW_UP, up))
    palm_to(h, "L", (0, -1, 0.0) if up > 0.5 else (-0.3, -0.2, 1))      # knuckles up while low, palm in at full height
    a = ease(t, 0.0, 0.35); b = ease(t, 0.35, 0.8); c = ease(t, 0.8, 1.4)
    r = lerp(lerp(lerp(DOWN, NOCK, a), SET, b), ANCHOR, c)
    arm(h, "R", *r)
    palm_to(h, "R", (0, 1, 0) if c > 0.3 else (0.2, 0, -1))           # hooked fingers on the string
    h.fingers("L", 80, thumb=50)                                       # bow grip
    h.fingers("R", track(t, [(0, 20), (0.35, 45), (1.4, 55)]), thumb=30)
    h.turn("chest", "X", -3 * c, keep=True)                            # chest opens as he draws
    h.keys(dict(brow_angry=track(t, [(0.4, 0.1), (1.4, 0.55)]), mouth_press=track(t, [(0.8, 0), (1.4, 0.5)])))


def bow_release(h, t):
    """starts at full draw (bow_draw at t >= 1.4)"""
    _stance(h, 1.0)
    f = ease(t, 0.0, 0.12)                                             # the snap is fast
    arm(h, "L", *lerp(BOW_UP, BOW_FOLLOW, ease(t, 0.0, 0.25))); palm_to(h, "L", (0, -1, 0))
    arm(h, "R", *lerp(ANCHOR, LOOSE, f))
    h.fingers("L", 80, thumb=50)
    h.fingers("R", mix(55, 0, ease(t, 0.0, 0.08)), spread=mix(0, 6, f), thumb=mix(30, 5, f))
    h.turn("chest", "X", -3 + 2 * f, keep=True)
    h.keys(dict(brow_angry=mix(0.55, 0.3, ease(t, 0.2, 0.8)), mouth_press=mix(0.5, 0.0, ease(t, 0.1, 0.5)),
                jaw_open=0.12 * f * (1 - ease(t, 0.3, 0.8))))


GUARD = ((0.35, -0.75, -0.25), (-0.45, -0.35, 0.85), (-0.3, -0.2, 0.95))         # forearm up across the face


def block(h, t):
    g = ease(t, 0.0, 0.18) * (1 - ease(t, 0.6, 1.0))
    h.move("foot_ik.R", (0, 0.28 * g, 0.05 * math.sin(math.pi * ease(t, 0.0, 0.18))))   # right foot steps back
    h.move("torso", (0, 0.13 * g, -0.06 * g))
    h.turn("chest", "X", -6 * g, keep=True)                            # leans away from the blow
    h.turn("head", "X", 10 * g)                                        # chin tucked
    arm(h, "L", *lerp(DOWN, GUARD, g)); arm(h, "R", *lerp(DOWN, ((0.3, -0.7, -0.4), (-0.5, -0.45, 0.75), (-0.35, -0.3, 0.9)), g))
    h.fingers("L", mix(25, 85, g)); h.fingers("R", mix(25, 85, g))
    h.keys(dict(brow_angry=0.6 * g, mouth_press=0.5 * g, blink_L=0.35 * g, blink_R=0.35 * g))


def dodge(h, t, side=1):
    d = ease(t, 0.0, 0.22) * (1 - ease(t, 0.65, 1.0))
    sx = side
    h.move("foot_ik.L" if sx > 0 else "foot_ik.R", (0.42 * sx * d, 0.0, 0.06 * math.sin(math.pi * ease(t, 0.0, 0.22))))
    h.move("torso", (0.30 * sx * d, 0.03 * d, -0.22 * d))           # ducks and slips sideways
    h.turn("chest", "Y", -14 * sx * d, keep=True)                      # torso tilts away from the line of the blow
    h.turn("chest", "X", 12 * d, keep=True)
    h.turn("head", "Y", 8 * sx * d)
    arm(h, "L" if sx > 0 else "R", *lerp(DOWN, ((0.7, -0.2, -0.65), (0.6, -0.5, -0.3), (0.5, -0.6, -0.2)), d))   # balance arm out
    arm(h, "R" if sx > 0 else "L", *lerp(DOWN, ((0.2, -0.75, -0.35), (-0.35, -0.6, 0.6), (-0.3, -0.5, 0.7)), d))  # guard up
    h.fingers("L", 40); h.fingers("R", 40)
    h.keys(dict(brow_angry=0.45 * d, mouth_press=0.4 * d))


RUN_T, RUN_STRIDE = 0.66, 1.15                                         # cycle seconds, one step (m)
RUN_SPEED = RUN_STRIDE / (RUN_T / 2)


def _run_foot(t, phase):
    """foot offset along -Y (forward) relative to the body, and lift, for a foot whose stance starts at the phase"""
    u = (t / RUN_T + phase) % 1.0
    stance = 0.42                                                      # under half the cycle on the ground: flight phase
    half = 0.5 * stance / 0.5 * RUN_STRIDE                             # the body travels 2*half while the foot is planted
    if u < stance:                                                     # planted: slides back under the moving body
        a = u / stance
        return mix(half, -half, a), 0.0, mix(10, -20, a)
    a = (u - stance) / (1 - stance)                                    # swing: lifts high behind, reaches forward
    y = mix(-half, half, ease(a, 0.15, 1.0))
    z = 0.32 * math.sin(math.pi * min(a / 0.7, 1.0)) * (1 - 0.6 * a)
    return y, z, mix(-35, 15, a)


def run(h, t):
    """run in place; move the rig forward by RUN_SPEED * t (hero -Y) for travel"""
    yl, zl, pl = _run_foot(t, 0.0)
    yr, zr, pr = _run_foot(t, 0.5)
    h.move("foot_ik.L", (0, -yl, zl)); h.move("foot_ik.R", (0, -yr, zr))
    h.turn("foot_ik.L", "X", pl); h.turn("foot_ik.R", "X", pr)
    ph = 2 * math.pi * t / RUN_T
    bounce = 0.035 * abs(math.cos(ph))                                 # highest in the flight phase
    h.move("torso", (0.015 * math.sin(ph), -0.05, -0.08 + bounce))
    h.turn("torso", "X", 9, keep=True)                                 # leans into the run
    h.turn("hips", "Z", 9 * math.sin(ph)); h.turn("chest", "Z", -11 * math.sin(ph), keep=True)
    sw = 0.75 * math.sin(ph)                                           # arms pump, bent near 90 degrees
    arm(h, "L", (0.2, sw * 0.8, -1), (0.12, -0.95 + 0.3 * sw, 0.25 - 0.4 * sw), (0.05, -0.9 + 0.3 * sw, 0.3 - 0.4 * sw))
    arm(h, "R", (0.2, -sw * 0.8, -1), (0.12, -0.95 - 0.3 * sw, 0.25 + 0.4 * sw), (0.05, -0.9 - 0.3 * sw, 0.3 + 0.4 * sw))
    h.fingers("L", 60); h.fingers("R", 60)
    h.turn("head", "X", -6)                                            # eyes ahead, against the lean


def bow_string_point(h):
    """world point between the right hand's index and middle finger tips: where the string sits at full draw"""
    bpy.context.view_layer.update()
    a = h.rig.matrix_world @ h.pb["f_index.02.R"].tail if "f_index.02.R" in h.pb else None
    b = h.rig.matrix_world @ h.pb["f_middle.02.R"].tail if "f_middle.02.R" in h.pb else None
    if a is None or b is None:
        return h.rig.matrix_world @ h.pb["DEF-hand.R"].tail
    return (a + b) / 2
