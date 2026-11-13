"""Kurukshetra field layout: writes layout.json for ue_assemble_kurukshetra.py.

Pure Python, fixed seed, so a rebuild is repeatable. All positions are in
Unreal units (cm), Z up. Heights follow the terrain (terrain_heights.json from
build_kit.py), so nothing is buried or floating. Field axis: the Pandava host stands at Y < 0 and
faces +Y (yaw 0); the Kaurava host stands at Y > 0 and faces -Y (yaw 180).
The empty middle strip runs along X through the origin, and Arjuna's
chariot stands at the origin, as in pilot shots SH080-SH090.

Soldiers, chariots with crews and horse teams, war elephants, cavalry, command tents, the standard and
the drum cart are the Blender hero models from hero/build_hero.py (krk_*); nothing needs TRELLIS. --soldiers proxy falls back to the flat kit proxies if the PC struggles.

Usage: python layout.py [--per-side 20000] [--soldiers hero|proxy] [--wrecks 0] [--out layout.json]
"""
import argparse
import json
import math
import os
import random

M = 100.0  # metres -> cm
SEED = 1801

# Sides: (sign of Y, yaw, soldier mesh, banner meshes, elephant tint, chariot)
SIDES = {
    "Pandava": dict(sy=-1, yaw=0.0, proxy="KRK_SoldierProxy_Pandava", soldier="krk_pandava_archer",
                    banners=["KRK_BannerPole_Saffron_Tall", "KRK_BannerPole_Saffron_Short"],
                    tents=["KRK_Tent_Saffron", "KRK_Tent_Marble"], chariot="krk_rank_chariot",
                    war_tent="krk_war_tent", team="krk_horse_team", elephant="krk_war_elephant",
                    cavalry="krk_pandava_cavalry"),
    "Kaurava": dict(sy=1, yaw=180.0, proxy="KRK_SoldierProxy_Kaurava", soldier="krk_kaurava_soldier",
                    banners=["KRK_BannerPole_Red_Tall", "KRK_BannerPole_Red_Short"],
                    tents=["KRK_Tent_Red"], chariot="krk_rank_chariot_red",
                    war_tent="krk_war_tent_red", team="krk_horse_team_dark", elephant="krk_war_elephant_red",
                    cavalry="krk_kaurava_cavalry"),
}

STRIP_HALF = 90       # m: half-width of the empty middle ground (v3: hosts closer)
FRONT = 1100          # m: width of each host's front (v2: narrower, deeper blocks)
LANE_EVERY = 260      # m: chariot lane spacing along the front
LANE_W = 24           # m
SPACING = 1.4         # m between files (close order)
RANK_GAP = 1.7        # m between ranks
LINE_EVERY = 10       # ranks per line; lines are split by a 4 m gap (v3: solid masses)
CAMP_BACK = 120       # m: camp distance behind the rear line (v3: camps read in the wide shot)
FRONT_RANKS = 2       # ranks that use the second pose (spears levelled, bows drawn)
CAV_WING = 110        # m: width of each cavalry wing beyond the infantry front
CAV_RANKS = 5


HEIGHTS = None  # ground height grid written by build_kit.py (terrain_heights.json)


def load_heights(path):
    global HEIGHTS
    if os.path.exists(path):
        HEIGHTS = json.load(open(path))
    else:
        print(f"WARNING: {path} not found, everything is placed at Z=0 and will sit below the ground")


def ground(x, y):
    """Terrain height in metres at Unreal (x, y) metres. The grid is in Blender coordinates (Y flipped)."""
    if HEIGHTS is None:
        return 0.0
    h = HEIGHTS
    fx = min(max((x - h["x0_m"]) / h["res_m"], 0), h["nx"] - 1.001)
    fy = min(max((-y - h["y0_m"]) / h["res_m"], 0), h["ny"] - 1.001)
    i, j = int(fx), int(fy)
    u, v = fx - i, fy - j
    c = h["cm"]
    return ((c[j][i] * (1 - u) + c[j][i + 1] * u) * (1 - v) + (c[j + 1][i] * (1 - u) + c[j + 1][i + 1] * u) * v) / 100


def xf(x, y, z=0.0, yaw=0.0, s=1.0):
    """Transform in Unreal units. z is the height above the ground at (x, y), not above zero."""
    return [round(x * M, 1), round(y * M, 1), round((z + ground(x, y)) * M, 1), round(yaw, 2), round(s, 3)]


def build(per_side, soldiers="hero", wrecks=0):
    rng = random.Random(SEED)
    groups = {}  # mesh -> {"folder":..., "instances":[...]} for instanced crowds/props
    heroes = []  # single actors

    def add(mesh, folder, t):
        groups.setdefault(mesh, {"folder": folder, "instances": []})["instances"].append(t)

    def team(mesh, x, y, yaw, folder):
        """Team of four under the yoke. The team model shares the chariot's origin, so it takes its transform."""
        add(mesh, folder, xf(x, y, 0, yaw))

    for side, cfg in SIDES.items():
        sy, yaw = cfg["sy"], cfg["yaw"]
        # soldier blocks between lanes; depth chosen so the count lands near per_side
        lanes = [-FRONT / 2 + i * LANE_EVERY for i in range(int(FRONT / LANE_EVERY) + 1)]
        usable = FRONT - len(lanes) * LANE_W
        cols = int(usable / SPACING)
        ranks = max(2, math.ceil(per_side / cols))
        step = usable / math.ceil(per_side / ranks)  # spread the columns over the whole front
        placed = 0
        x = -FRONT / 2
        while x < FRONT / 2 and placed < per_side:
            if any(abs(x - lx) < LANE_W / 2 for lx in lanes):
                x += step
                continue
            for r in range(ranks):
                if placed >= per_side:
                    break
                if rng.random() < 0.04:  # gaps make the mass ragged, not a grid
                    continue
                ragged = 3 * math.sin(x / 53.0 + sy) + 1.0 * math.sin(x / 17.0)
                yy = sy * (STRIP_HALF + 6 + ragged + r * RANK_GAP + (r // LINE_EVERY) * 4)
                mesh = cfg["proxy"] if soldiers == "proxy" else cfg["soldier"] + ("_b" if r < FRONT_RANKS else "")
                add(mesh, f"KRK/{side}/Infantry",
                    xf(x + rng.uniform(-0.6, 0.6), yy + rng.uniform(-0.6, 0.6), 0,
                       yaw + rng.uniform(-6, 6), rng.uniform(0.95, 1.05)))
                placed += 1
            x += step
        depth = STRIP_HALF + 12 + ranks * RANK_GAP + (ranks // LINE_EVERY) * 4

        # banner line just in front of the infantry, and a second line behind it
        for i, bx in enumerate(range(-FRONT // 2, FRONT // 2 + 1, 25)):
            add(cfg["banners"][i % 2], f"KRK/{side}/Banners",
                xf(bx + rng.uniform(-2, 2), sy * (STRIP_HALF + 2), 0, yaw + 90 + rng.uniform(-10, 10)))
        for i, bx in enumerate(range(-FRONT // 2 + 12, FRONT // 2, 40)):
            add(cfg["banners"][0], f"KRK/{side}/Banners",
                xf(bx, sy * (depth + 8), 0, yaw + 90 + rng.uniform(-10, 10), 1.2))

        # chariots in each lane, four horses ahead of each car
        for lx in lanes[1:-1]:
            for k in range(3):
                cy = sy * (STRIP_HALF + 15 + k * 18)
                add(cfg["chariot"], f"KRK/{side}/Chariots", xf(lx, cy, 0, yaw))
                team(cfg["team"], lx, cy, yaw, f"KRK/{side}/Horses")

        # war elephants: a line behind the infantry
        for ex in range(-FRONT // 2 + 30, FRONT // 2, 55):
            add(cfg["elephant"], f"KRK/{side}/Elephants",
                xf(ex + rng.uniform(-6, 6), sy * (depth + 22 + rng.uniform(-3, 3)), 0, yaw + rng.uniform(-8, 8)))

        # cavalry wings on both flanks, level with the front ranks
        for wing in (-1, 1):
            for r in range(CAV_RANKS):
                cx = FRONT / 2 + 14
                while cx < FRONT / 2 + 14 + CAV_WING:
                    add(cfg["cavalry"], f"KRK/{side}/Cavalry",
                        xf(wing * cx + rng.uniform(-0.5, 0.5), sy * (STRIP_HALF + 10 + r * 4.6 + rng.uniform(-0.6, 0.6)),
                           0, yaw + rng.uniform(-5, 5), rng.uniform(0.96, 1.04)))
                    cx += 2.6

        # camp behind the host
        cy0 = sy * (depth + CAMP_BACK)
        for i in range(160):
            a = rng.uniform(0, math.tau)
            r = rng.uniform(20, 140)
            add(cfg["tents"][i % len(cfg["tents"])], f"KRK/{side}/Camp",
                xf(math.cos(a) * r * 2.2, cy0 + math.sin(a) * r, 0, rng.choice([0, 90, 180, 270])))
        for i in range(24):
            add(["KRK_WeaponRack", "KRK_SpearStack", "KRK_ShieldStack", "KRK_FirePit"][i % 4], f"KRK/{side}/Camp",
                xf(rng.uniform(-500, 500), cy0 + rng.uniform(-200, 200), 0, rng.uniform(0, 360)))
        for i in range(0, 1200, 10):  # palisade across the camp front
            add("KRK_Palisade", f"KRK/{side}/Camp", xf(-600 + i, cy0 + sy * 170, 0, 0))  # behind the camp
        heroes.append({"mesh": cfg["war_tent"], "label": f"KRK3D_{side}_CommandTent",
                       "folder": f"KRK/{side}/Camp", "t": xf(0, cy0, 0, yaw)})

    # ground scatter (v2): dry grass and stones break up the flat plain
    for i in range(9000):
        if i % 3 == 0:
            x, y = rng.uniform(-260, 260), rng.uniform(-STRIP_HALF, STRIP_HALF)  # near the strip
        else:
            x, y = rng.uniform(-1600, 1600), rng.uniform(-1300, 1300)
        add("KRK_GrassTuft" if i % 4 else "KRK_Rock", "KRK/Ground",
            xf(x, y, 0, rng.uniform(0, 360), rng.uniform(0.6, 1.8)))

    # battle dressing (off for the pilot, which is set before the first arrow): wrecks in the middle ground
    for i in range(wrecks):
        add("krk_chariot_wreck", "KRK/Battle",
            xf(rng.uniform(-300, 300), rng.uniform(-STRIP_HALF + 15, STRIP_HALF - 15), 0, rng.uniform(0, 360)))
    for i in range(wrecks * 12):
        add("krk_arrow_cluster", "KRK/Battle",
            xf(rng.uniform(-320, 320), rng.uniform(-STRIP_HALF + 5, STRIP_HALF - 5), 0, rng.uniform(0, 360),
               rng.uniform(0.8, 1.3)))

    # hero pieces, fixed positions (chariot origins are midway between the axles)
    bhishma, duryodhana = (-40, STRIP_HALF + 12), (25, STRIP_HALF + 16)
    heroes += [
        {"mesh": "krk_arjuna_chariot", "label": "KRK3D_Arjuna_Chariot", "folder": "KRK/Heroes", "t": xf(0, 0, 0, 0)},
        {"mesh": "krk_ape_banner", "label": "KRK3D_Pandava_ApeStandard", "folder": "KRK/Heroes",
         "t": xf(-14, -(STRIP_HALF + 3), 0, 0)},
        {"mesh": "krk_bhishma_chariot", "label": "KRK3D_Bhishma_Chariot", "folder": "KRK/Heroes",
         "t": xf(*bhishma, 0, 180)},
        {"mesh": "krk_duryodhana_chariot", "label": "KRK3D_Duryodhana_Chariot", "folder": "KRK/Heroes",
         "t": xf(*duryodhana, 0, 180)},
        {"mesh": "krk_war_drum_cart", "label": "KRK3D_Kaurava_DrumCart", "folder": "KRK/Heroes",
         "t": xf(-70, STRIP_HALF + 20, 0, 180)},
    ]
    heroes += [
        {"mesh": "krk_horse_team", "label": "KRK3D_Arjuna_Team", "folder": "KRK/Heroes", "t": xf(0, 0, 0, 0)},
        {"mesh": "krk_horse_team", "label": "KRK3D_Bhishma_Team", "folder": "KRK/Heroes", "t": xf(*bhishma, 0, 180)},
        {"mesh": "krk_horse_team_dark", "label": "KRK3D_Duryodhana_Team", "folder": "KRK/Heroes",
         "t": xf(*duryodhana, 0, 180)},
    ]

    cameras = [
        {"label": "KRK_CAM_Wide", "loc": xf(-660, -10, 45)[:3], "rot": [-4.0, -15.0, 0.0], "fov": 60,
         "note": "Establishing: both hosts across the empty strip, low sun behind the Kaurava side"},
        {"label": "KRK_CAM_HeroChariot", "loc": xf(-7, -11, 1.4)[:3], "rot": [6.0, 57.0, 0.0], "fov": 50,
         "note": "Low hero angle on Arjuna's chariot alone in the middle ground (SH080)"},
        {"label": "KRK_CAM_Battle", "loc": xf(-34, -128, 9)[:3], "rot": [-5.0, 74.0, 0.0], "fov": 58,
         "note": "Over the Pandava front ranks: Arjuna's chariot alone in the strip, the Kaurava host beyond"},
        {"label": "KRK_CAM_Bhishma", "loc": xf(-30, 30, 2.2)[:3], "rot": [2.0, 105.0, 0.0], "fov": 30,
         "note": "Across the field to Bhishma's car from Arjuna's side (SH030/SH100)"},
    ]
    sun = {"pitch": -11.0, "yaw": -95.0, "color": "#FFC37A", "fog_color": "#B48A5A", "fog_density": 0.008, "clouds": True}
    return {"world": "Kurukshetra", "seed": SEED, "per_side": per_side, "soldiers": soldiers, "terrain": "KRK_Terrain",
            "groups": groups, "heroes": heroes, "cameras": cameras, "sun": sun}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-side", type=int, default=20000)
    ap.add_argument("--soldiers", choices=["hero", "proxy"], default="hero")
    ap.add_argument("--wrecks", type=int, default=0, help="chariot wrecks (and 12 arrow clusters each) in the middle ground, for battle shots")
    ap.add_argument("--out", default="layout.json")
    ap.add_argument("--heights", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "terrain_heights.json"))
    a = ap.parse_args()
    load_heights(a.heights)
    data = build(a.per_side, a.soldiers, a.wrecks)
    with open(a.out, "w") as f:
        json.dump(data, f, indent=1)
    n = sum(len(g["instances"]) for g in data["groups"].values())
    print(f"{n} instances in {len(data['groups'])} groups, {len(data['heroes'])} hero actors -> {a.out}")
    for k, g in sorted(data["groups"].items()):
        print(f"  {k:36s} {len(g['instances']):5d}")


if __name__ == "__main__":
    main()
