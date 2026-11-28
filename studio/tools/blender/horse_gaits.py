"""Gaits for the rigged Hastinapur horse (horse_rig.py): stand, trot, gallop.

    import horse_gaits
    horse_gaits.key(rig, "gallop", f0=1, f1=48, fps=24, phase=0.0, speed=1.0)

Every bone swings about its local X (= world X, see horse_rig.align_roll); +angle moves a leg back (+Y),
-angle reaches forward. Angles are degrees. The horse gallops in place: the chariot carries the team forward.
"""
import math
from mathutils import Euler

GAITS = {
    # stride seconds, leg phase offsets (hind L, hind R, fore L, fore R), stance share, reach, push, bob (m)
    "gallop": dict(period=0.48, ph=dict(hL=0.00, hR=0.12, fL=0.45, fR=0.57), stance=0.36, reach=-42, push=34, bob=0.10),
    "trot":   dict(period=0.70, ph=dict(hL=0.00, hR=0.50, fL=0.50, fR=0.00), stance=0.48, reach=-20, push=18, bob=0.03),
    "stand":  None,
}


def _leg(s, stance, reach, push):
    """returns (upper swing, fold) for a leg at cycle position s; fold 0..1 peaks mid swing"""
    if s < stance:                                   # hoof on the ground: sweep from reach to push, leg straight
        u = s / stance
        return reach + (push - reach) * u, 0.0
    u = (s - stance) / (1 - stance)                  # in the air: fold, carry forward, unfold to reach
    swing = push + (reach - push) * (0.5 - 0.5 * math.cos(math.pi * u))
    return swing, math.sin(math.pi * min(1.0, u * 1.15)) ** 1.5


def pose(rig, gait, t, phase=0.0, speed=1.0):
    if "base_z" not in rig:
        rig["base_z"] = rig.location.z
    pb = rig.pose.bones
    for b in pb:
        b.rotation_mode = "XYZ"; b.rotation_euler = Euler((0, 0, 0)); b.location = (0, 0, 0)
    g = GAITS[gait]
    if g is None:
        pb["neck.1"].rotation_euler.x = math.radians(4); return
    p = (t / g["period"] * speed + phase) % 1.0
    for leg, off in g["ph"].items():
        s = (p + off) % 1.0
        swing, fold = _leg(s, g["stance"], g["reach"], g["push"])
        side = leg[1]
        if leg[0] == "f":
            pb[f"fore_upper.{side}"].rotation_euler.x = math.radians(swing * 0.75)
            pb[f"fore_arm.{side}"].rotation_euler.x = math.radians(swing * 0.25 - 25 * fold)      # forearm lifts forward
            pb[f"fore_cannon.{side}"].rotation_euler.x = math.radians(95 * fold)                  # knee folds the cannon back
        else:
            pb[f"hind_thigh.{side}"].rotation_euler.x = math.radians(swing * 0.7 - 10 * fold)
            pb[f"hind_gaskin.{side}"].rotation_euler.x = math.radians(swing * 0.3 + 30 * fold)    # hock folds up
            pb[f"hind_cannon.{side}"].rotation_euler.x = math.radians(-55 * fold)
    w = math.sin(2 * math.pi * p)
    rig.pose.bones["root"].rotation_euler.x = math.radians(3.0 * w)                            # rocking: chest up, hips down
    pb["neck.1"].rotation_euler.x = math.radians(-5 * w + 8)
    pb["neck.2"].rotation_euler.x = math.radians(-3 * w)
    pb["head"].rotation_euler.x = math.radians(4 * w - 6)
    pb["tail.1"].rotation_euler.x = math.radians(38 + 4 * w)
    pb["tail.2"].rotation_euler.x = math.radians(22 + 10 * math.sin(2 * math.pi * p - 1.2))
    ground(rig, g["bob"] * max(0.0, math.sin(2 * math.pi * (p - 0.62))))   # a short float in the suspension phase


def ground(rig, lift=0.0):
    """drop or raise the rig so the lowest hoof rests on the ground (hooves sit at z 0.03 at rest)"""
    import bpy
    base = rig.get("base_z", rig.location.z)
    rig.location.z = base; bpy.context.view_layer.update()
    low = min((rig.matrix_world @ rig.pose.bones[n].tail).z for n in
              ("fore_cannon.L", "fore_cannon.R", "hind_cannon.L", "hind_cannon.R"))
    rig.location.z = base + (base + 0.03 - low) + lift


def key(rig, gait, f0, f1, fps=24, phase=0.0, speed=1.0):
    for f in range(f0, f1 + 1):
        pose(rig, gait, (f - f0) / fps, phase, speed)
        for b in rig.pose.bones:
            b.keyframe_insert("rotation_euler", frame=f)
        rig.keyframe_insert("location", index=2, frame=f)
