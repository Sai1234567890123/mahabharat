"""Every hero motion EP01 "Arjuna vs Karna" needs (studio/episodes/ep01_arjuna_vs_karna/animation_plan.md). Free, cloud Blender.

Same rules as moves.py: a move is a function of the hero and t (seconds from the move's start); call it each frame after
h.reset() and before h.key_all(frame). Hero front -Y, his left +X, up +Z; the bow is in his LEFT hand, the target to his
left (+X). Moves that travel return a root offset (hero frame, metres) for the caller to add to the rig's location.

  Karna    bow_salute (A03)  fan_release (A06)  exhausted (A09)  quiver_draw (A10)  bow_draw_ear (A11)
           leap_down + heave (A16)  palm_wait (A17)  stand_tall (A20)
  Arjuna   bow_draw (A04, moves.py)  rapid_fire (A07)  exhausted (A09)  head_hit (A14)  rise_hair_push (A15)
           bow_draw_ear (A19, the Anjalika)  bow_lower (A22)
  Krishna  charioteer (A02, A04)  reins_flick (A05)  foot_press (A13)  calm_look (A17, A22)
MOVES lists them with their lengths for the demo.
"""
import math
import moves
from moves import arm, palm_to, lerp, DOWN, BOW_LOW, BOW_UP, BOW_FOLLOW, NOCK, SET, ANCHOR, LOOSE, _stance
from anim_lib import ease, track, mix


def blink(t, times, dur=0.18):
    """eyelid weight for blinks starting at the given times"""
    w = 0.0
    for b in times:
        if b <= t <= b + dur:
            w = max(w, math.sin(math.pi * (t - b) / dur))
    return w


def _bow_hand(h, pose, palm=None):
    """bow arm pose; palm (hero frame) turns the fist first, while the fingers are still open (palm_to needs that)"""
    arm(h, "L", *pose)
    if palm:
        palm_to(h, "L", palm)
    h.fingers("L", 80, thumb=50)


# ---- Karna -----------------------------------------------------------------------------------------------------------------
SALUTE_L = ((0.15, -0.25, -0.95), (-0.8, -0.55, 0.15), (-0.82, -0.55, 0.12))    # bow fist close before the chest, bow upright before his face
SALUTE_R = ((0.2, -0.35, -0.9), (-0.7, -0.55, 0.45), (-0.75, -0.45, 0.45))      # other hand flat over his heart


def bow_salute(h, t, look=-1):
    """A03, 4 s: lifts the bow to his forehead, eyes closed (0-2), then the eyes open and lift toward look (-1 his right)"""
    u = ease(t, 0.0, 1.0) * (1 - 0.35 * ease(t, 2.2, 3.2))             # the bow comes down a little as he looks up
    _bow_hand(h, lerp(BOW_LOW, SALUTE_L, u), palm=(0, 1, 0) if u > 0.5 else None)   # palm to the chest: the bow stands upright
    r = ease(t, 0.15, 1.0) * (1 - ease(t, 2.4, 3.4))
    arm(h, "R", *lerp(DOWN, SALUTE_R, r))
    if r > 0.3:
        palm_to(h, "R", (0, 1, 0))                                     # palm flat on his chest
    h.fingers("R", 5, thumb=10)
    bow = ease(t, 0.6, 1.2) * (1 - ease(t, 2.0, 2.6))
    h.turn("head", "X", 18 * bow - 9 * ease(t, 2.2, 3.4))             # bows his forehead to the bow, then the chin lifts
    h.turn("head", "Z", 22 * look * ease(t, 2.3, 3.6), keep=True)
    h.turn("chest", "X", 5 * bow, keep=True)
    shut = ease(t, 0.7, 1.0) * (1 - ease(t, 2.0, 2.25))
    h.keys(dict(blink_L=shut, blink_R=shut, brow_sad=0.3 * bow, brow_angry=0.35 * ease(t, 2.6, 3.6)))


def fan_release(h, t):
    """A06, from full draw: the release sweeps the bow across, so seven arrows leave in a fan"""
    moves.bow_release(h, t)
    sweep = math.sin(math.pi * ease(t, 0.0, 0.5))
    h.turn("chest", "Z", 10 * (ease(t, 0.0, 0.4) - 0.5) * 2, keep=True)
    h.turn("chest", "Y", -4 * sweep, keep=True)


def exhausted(h, t, bow=True):
    """A09, loops: heavy breathing, shoulders rise and fall, a slow blink, sweat-dull eyes, bow hanging low"""
    br = math.sin(2 * math.pi * t / 1.6)                               # a breath every 1.6 s
    h.move("torso", (0, 0.01, -0.035 + 0.01 * br))
    h.turn("chest", "X", 4 + 2.5 * br, keep=True)                      # chest heaves
    h.turn("head", "X", 6 - 3 * br)
    if bow:
        _bow_hand(h, lerp(BOW_LOW, DOWN, 0.45))
    else:
        arm(h, "L", *DOWN); h.fingers("L", 25)
    arm(h, "R", *lerp(DOWN, ((0.3, -0.2, -0.9), (0.2, -0.4, -0.85), (0.1, -0.35, -0.9)), 0.5)); h.fingers("R", 35)
    for s in "LR":
        h.turn(f"shoulder.{s}", "Z", (3 if s == "L" else -3) * br)
    lid = 0.25 + 0.75 * blink(t, (1.3,), dur=0.55)
    h.keys(dict(blink_L=lid, blink_R=lid, jaw_open=0.1 + 0.06 * br, brow_sad=0.35))


QUIVER = ((0.35, 0.45, -0.82), (0.15, 0.55, -0.82), (0.05, 0.5, -0.85))         # right hand back at the hip quiver
PRESENT = ((0.25, -0.75, -0.1), (-0.5, -0.62, 0.58), (-0.45, -0.5, 0.74))        # the arrow held up before his face


def quiver_draw(h, t):
    """A10, 4 s: right hand to the quiver at his right hip (nothing on Karna's back), pulls one arrow, holds it up to look"""
    _bow_hand(h, BOW_LOW)
    a, b = ease(t, 0.0, 0.6), ease(t, 0.8, 1.7)
    arm(h, "R", *lerp(lerp(DOWN, QUIVER, a), PRESENT, b))
    h.fingers("R", track(t, [(0, 15), (0.55, 10), (0.75, 70), (1.7, 65)]), thumb=45)
    h.turn("head", "Z", -30 * a * (1 - b) - 12 * b)                    # glances down to the quiver, then at the arrow
    h.turn("head", "X", 14 * a * (1 - b) + 6 * b, keep=True)
    h.turn("chest", "Z", -8 * a * (1 - b), keep=True)
    h.keys(dict(brow_angry=0.5 * ease(t, 1.7, 2.6), blink_L=blink(t, (2.2,)), blink_R=blink(t, (2.2,))))


ANCHOR_EAR = ((0.9, 0.33, 0.25), (-0.85, -0.28, 0.35), (-0.85, -0.2, 0.33))     # the string hand back to the ear


def bow_draw_ear(h, t):
    """A11, A19: a heavier draw, all the way to the ear (the snake arrow, the Anjalika); 0-1.8 then hold"""
    old = moves.ANCHOR
    moves.ANCHOR = ANCHOR_EAR
    try:
        moves.bow_draw(h, t * 1.4 / 1.8)
    finally:
        moves.ANCHOR = old
    h.turn("chest", "Z", 4 * ease(t, 1.0, 1.8), keep=True)
    h.keys(dict(brow_angry=track(t, [(0.4, 0.1), (1.8, 0.8)]), mouth_press=track(t, [(1.0, 0), (1.8, 0.7)])))


def leap_down(h, t, drop=1.0, reach=1.4):
    """A16, 1.6 s: crouch, jump off the chariot (drop m down, reach m forward), land in a deep crouch, rise to a squat.
    Returns the root offset (x, y, z) to add to the rig's location."""
    crouch = ease(t, 0.0, 0.25) * (1 - ease(t, 0.25, 0.38)) + ease(t, 0.8, 0.95) * (1 - 0.6 * ease(t, 1.05, 1.6))
    fl = ease(t, 0.3, 0.85)                                            # flight 0.3-0.85
    arc = 0.35 * math.sin(math.pi * fl)
    root = (0.0, -reach * fl, arc - drop * fl * fl)
    tuck = math.sin(math.pi * fl)
    h.move("torso", (0, 0.04 * crouch, -0.42 * crouch))
    for s, sx in (("L", 1), ("R", -1)):
        h.move(f"foot_ik.{s}", (0.06 * sx * crouch, -0.1 * tuck, 0.28 * tuck))
    h.turn("chest", "X", 18 * crouch + 8 * tuck, keep=True)
    up = ((0.75, -0.35, 0.3), (0.7, -0.5, 0.25), (0.6, -0.6, 0.2))
    _bow_hand(h, lerp(BOW_LOW, up, tuck))
    arm(h, "R", *lerp(DOWN, up, max(tuck, 0.5 * crouch))); h.fingers("R", 40)
    h.turn("head", "X", -10 * tuck + 12 * crouch, keep=True)
    h.keys(dict(brow_angry=0.6, mouth_press=0.4))
    return root


GRIP_L = ((0.2, -0.75, -0.65), (0.25, -0.75, -0.6), (0.15, -0.7, -0.7))          # both hands on the wheel rim, knee height
GRIP_R = ((0.2, -0.75, -0.65), (0.25, -0.75, -0.6), (0.15, -0.7, -0.7))


def heave(h, t):
    """A16, 5 s: squats, grips the sunk wheel and heaves it up; veins, strain and a tremble; no bow (it lies in the chariot)"""
    lift = ease(t, 0.8, 3.0)
    tremble = 0.6 * math.sin(2 * math.pi * 11 * t) * ease(t, 0.8, 1.2) * (1 - ease(t, 4.0, 4.6))
    h.move("foot_ik.L", (0.2, 0, 0)); h.move("foot_ik.R", (-0.2, 0.08, 0))
    h.move("torso", (0, 0.05, mix(-0.45, -0.22, lift)))
    h.turn("chest", "X", mix(28, -6, lift) + tremble, keep=True)       # from bent over to leaning back
    lifted = ((0.25, -0.8, -0.4), (0.2, -0.85, -0.25), (0.15, -0.85, -0.3))
    arm(h, "L", *lerp(GRIP_L, lifted, lift)); arm(h, "R", *lerp(GRIP_R, lifted, lift))
    h.fingers("L", 85, thumb=60); h.fingers("R", 85, thumb=60)
    h.turn("head", "X", mix(-12, -18, lift) + 0.5 * tremble)
    strain = ease(t, 0.6, 1.4)
    h.keys(dict(brow_angry=0.9 * strain, mouth_press=0.5 * strain * (1 - 0.6 * ease(t, 2.5, 3.0)),
                mouth_wide=0.5 * ease(t, 2.5, 3.0), jaw_open=0.2 * ease(t, 2.5, 3.0), blink_L=0.35 * strain, blink_R=0.35 * strain))


WAIT_R = ((0.3, -0.75, -0.45), (0.12, -0.6, 0.78), (0.1, -0.25, 0.96))


def palm_wait(h, t):
    """A17, 4 s: raises his open right palm toward Arjuna (front): "wait"; the other hand on the wheel at his side"""
    u = ease(t, 0.0, 1.2)
    arm(h, "R", *lerp(DOWN, WAIT_R, u)); h.fingers("R", mix(25, 0, u), spread=6 * u, thumb=0)
    palm_to(h, "R", (0, -1, 0.1))
    arm(h, "L", *DOWN); h.fingers("L", 30)
    h.turn("chest", "X", -3 * u, keep=True)
    h.turn("head", "Z", -6 * u); h.turn("head", "Y", 5 * u, keep=True)
    h.keys(dict(brow_sad=0.5 * u, brow_up=0.3 * u, blink_L=blink(t, (2.5,)), blink_R=blink(t, (2.5,))))


def stand_tall(h, t):
    """A20, loops: upright and still against the sun, chest open, chin up, bow upright at his side"""
    br = math.sin(2 * math.pi * t / 3.0)
    h.turn("chest", "X", -5 + 0.8 * br, keep=True)
    h.turn("head", "X", -8)
    _bow_hand(h, ((0.3, -0.1, -0.95), (0.25, -0.35, -0.9), (0.2, -0.45, -0.85)))
    arm(h, "R", *DOWN); h.fingers("R", 20)
    h.keys(dict(brow_angry=0.2))


# ---- Arjuna ----------------------------------------------------------------------------------------------------------------
def rapid_fire(h, t, period=0.7):
    """A07, loops: nock, draw and loose again and again, the aim stepping a little each shot to meet each arrow"""
    _stance(h, 1.0)
    k = int(t // period); p = (t % period) / period
    _bow_hand(h, BOW_UP, palm=(0, -1, 0))
    if p < 0.3:
        r = lerp(LOOSE, SET, ease(p, 0.0, 0.3))
    elif p < 0.78:
        r = lerp(SET, ANCHOR, ease(p, 0.3, 0.7))
    else:
        r = lerp(ANCHOR, LOOSE, ease(p, 0.78, 0.86))
    arm(h, "R", *r)
    palm_to(h, "R", (0, 1, 0))
    h.fingers("R", 0 if p >= 0.8 else 50, thumb=25)
    h.turn("chest", "Y", (-4, 3, -1, 5, -3)[k % 5] * ease(p, 0.0, 0.3), keep=True)
    h.keys(dict(brow_angry=0.6, mouth_press=0.4))


def head_hit(h, t):
    """A14, 3 s: the crown is struck off: the head snaps back and aside, he staggers and drops to one knee"""
    snap = ease(t, 0.0, 0.1) * (1 - 0.7 * ease(t, 0.3, 1.0))
    knee = ease(t, 0.5, 1.6)
    h.turn("head", "X", -24 * snap + 10 * knee); h.turn("head", "Z", 18 * snap, keep=True)
    h.turn("chest", "X", -10 * snap + 14 * knee, keep=True)
    kneel(h, knee)
    _bow_hand(h, lerp(BOW_LOW, ((0.6, -0.4, -0.6), (0.5, -0.6, -0.5), (0.4, -0.7, -0.5)), knee))
    arm(h, "R", *lerp(lerp(DOWN, ((0.6, 0.3, 0.2), (0.3, -0.2, 0.9), (0.2, -0.3, 0.9)), snap), ((0.3, -0.6, -0.7), (0.1, -0.85, -0.4), (0.05, -0.9, -0.3)), knee))
    h.fingers("R", 40)
    h.keys(dict(blink_L=snap, blink_R=snap, brow_angry=0.6 * snap + 0.4 * knee, jaw_open=0.25 * snap))


def kneel(h, u):
    """down on the right knee (u 0..1): right foot back with the heel up, left foot forward, hips low"""
    h.move("foot_ik.R", (-0.04 * u, 0.55 * u, 0.02 * u)); h.turn("foot_ik.R", "X", -60 * u)
    h.move("foot_ik.L", (0.04 * u, -0.3 * u, 0))
    h.move("torso", (0, 0.1 * u, -0.55 * u))


HAIR_A = ((0.55, -0.6, 0.45), (-0.5, -0.45, 0.75), (-0.55, -0.3, 0.75))          # right hand at the forehead
HAIR_B = ((0.75, -0.1, 0.65), (-0.3, 0.3, 0.9), (-0.2, 0.55, 0.8))               # swept back over the crown of his head


def rise_hair_push(h, t):
    """A15, 3 s: rises from the knee, pushes the loose hair back from his brow, lifts Gandiva and his eyes"""
    kneel(h, 1 - ease(t, 0.0, 1.3))
    a, b, c = ease(t, 0.4, 1.0), ease(t, 1.0, 1.7), ease(t, 1.7, 2.3)
    arm(h, "R", *lerp(lerp(lerp(DOWN, HAIR_A, a), HAIR_B, b), DOWN, c))
    h.fingers("R", mix(10, 30, b), spread=6 * a * (1 - b))
    lift = ease(t, 1.9, 2.8)
    _bow_hand(h, lerp(BOW_LOW, ((0.55, -0.7, 0.15), (0.45, -0.85, 0.1), (0.4, -0.9, 0.1)), lift))
    h.turn("head", "X", 10 * (1 - a) - 10 * b * (1 - c) - 8 * lift)   # head tips back under the hand, then eyes lift
    h.keys(dict(brow_angry=0.5 * lift, blink_L=blink(t, (0.3,)), blink_R=blink(t, (0.3,))))


def bow_lower(h, t):
    """A22, 4 s: from full draw the bow comes down slowly; no celebration: the shoulders drop, the head bows a little"""
    u = ease(t, 0.0, 2.0)
    _bow_hand(h, lerp(BOW_UP, ((0.3, -0.15, -0.95), (0.25, -0.35, -0.9), (0.2, -0.45, -0.85)), u))
    arm(h, "R", *lerp(ANCHOR, DOWN, ease(t, 0.0, 1.4))); h.fingers("R", mix(50, 15, u))
    _stance(h, 1 - u)
    h.turn("head", "X", 8 * ease(t, 1.5, 3.0), keep=True)
    h.turn("chest", "X", 4 * ease(t, 1.0, 3.0), keep=True)
    h.keys(dict(brow_sad=0.4 * ease(t, 1.5, 3.0), blink_L=blink(t, (2.6,), 0.3), blink_R=blink(t, (2.6,), 0.3)))


# ---- Krishna ---------------------------------------------------------------------------------------------------------------
REINS = ((0.18, -0.55, -0.8), (0.08, -0.95, -0.15), (0.03, -1.0, -0.12))          # both hands forward at the waist


def charioteer(h, t, sway=1.0):
    """A02, A04, loops: standing at the chariot's front, knees soft, reins in both hands, riding the chariot's sway"""
    s = math.sin(2 * math.pi * t * 1.3) * sway
    h.move("foot_ik.L", (0.06, -0.08, 0)); h.move("foot_ik.R", (-0.06, 0.08, 0))
    h.move("torso", (0.012 * s, 0, -0.05))
    h.turn("chest", "Y", 1.5 * s, keep=True)
    for sd in "LR":
        arm(h, sd, *REINS); h.fingers(sd, 78, thumb=45)
    h.keys(dict(smile_L=0.15, smile_R=0.15))


def reins_flick(h, t):
    """A05, 1.2 s: the hands draw up and back, then snap forward and down: the horses surge"""
    charioteer(h, t, sway=0.3)
    up = ease(t, 0.0, 0.18) * (1 - ease(t, 0.18, 0.3))
    snap = ease(t, 0.18, 0.3) * (1 - ease(t, 0.5, 1.2))
    pose = lerp(lerp(REINS, ((0.2, -0.3, -0.75), (0.1, -0.7, 0.55), (0.05, -0.6, 0.6)), up),
                ((0.2, -0.8, -0.45), (0.1, -0.95, -0.35), (0.05, -0.9, -0.45)), snap)
    for sd in "LR":
        arm(h, sd, *pose); h.fingers(sd, 82, thumb=50)
    h.turn("chest", "X", 6 * snap, keep=True); h.turn("head", "X", 4 * snap)
    h.keys(dict(brow_angry=0.25 * (up + snap), smile_L=0.1, smile_R=0.1))


def foot_press(h, t):
    """A13, 2 s: lifts the right foot and presses it down on the chariot floor: the chariot sinks a cubit (do that in the shot)"""
    charioteer(h, t, sway=0.0)
    lift = ease(t, 0.1, 0.8) * (1 - ease(t, 0.8, 1.0))
    press = ease(t, 0.8, 1.0)
    h.move("foot_ik.R", (-0.06, 0.08 - 0.12 * lift, 0.3 * lift))
    h.move("torso", (0, 0, -0.05 - 0.07 * press + 0.03 * ease(t, 1.2, 2.0)))
    h.turn("chest", "X", 4 * press, keep=True)
    h.keys(dict(brow_angry=0.2 * press, smile_L=0.12, smile_R=0.12))


def calm_look(h, t, side=1, deg=45):
    """A17, A22, 4 s: turns his head slowly to look (side +1 his left), a faint smile, one slow blink; reins held"""
    charioteer(h, t, sway=0.2)
    u = ease(t, 0.3, 1.8)
    h.turn("head", "Z", deg * side * u); h.turn("head", "X", -3 * u, keep=True)
    h.turn("chest", "Z", 6 * side * u, keep=True)
    b = blink(t, (2.4,), 0.35)
    h.keys(dict(smile_L=0.15 + 0.15 * u, smile_R=0.15 + 0.15 * u, blink_L=b, blink_R=b))


# name: (function, seconds, heroes, needs a bow in the left hand)
MOVES = {
    "bow_salute": (bow_salute, 4.0, ("karna",), True),
    "fan_release": (lambda h, t: moves.bow_draw(h, t) if t < 1.8 else fan_release(h, t - 1.8), 3.0, ("karna",), True),
    "exhausted": (exhausted, 3.2, ("karna", "arjuna"), True),
    "quiver_draw": (quiver_draw, 3.0, ("karna",), True),
    "bow_draw_ear": (bow_draw_ear, 3.0, ("karna", "arjuna"), True),
    "leap_down": (leap_down, 1.6, ("karna",), True),
    "heave": (heave, 5.0, ("karna",), False),
    "palm_wait": (palm_wait, 3.5, ("karna",), False),
    "stand_tall": (stand_tall, 3.0, ("karna",), True),
    "bow_draw": (moves.bow_draw, 2.5, ("arjuna",), True),
    "rapid_fire": (rapid_fire, 3.5, ("arjuna",), True),
    "head_hit": (head_hit, 3.0, ("arjuna",), True),
    "rise_hair_push": (rise_hair_push, 3.0, ("arjuna",), True),
    "bow_lower": (bow_lower, 4.0, ("arjuna",), True),
    "charioteer": (charioteer, 3.0, ("krishna",), False),
    "reins_flick": (reins_flick, 1.6, ("krishna",), False),
    "foot_press": (foot_press, 2.4, ("krishna",), False),
    "calm_look": (calm_look, 4.0, ("krishna",), False),
}
