"""Kurukshetra field layout: writes layout.json for ue_assemble_kurukshetra.py.

Pure Python, fixed seed, so a rebuild is repeatable. All positions are in
Unreal units (cm), Z up. Field axis: the Pandava host stands at Y < 0 and
faces +Y (yaw 0); the Kaurava host stands at Y > 0 and faces -Y (yaw 180).
The empty middle strip runs along X through the origin, and Arjuna's
chariot stands at the origin, as in pilot shots SH080-SH090.

Usage: python layout.py [--per-side 20000] [--out layout.json]
"""
import argparse
import json
import math
import random

M = 100.0  # metres -> cm
SEED = 1801

# Sides: (sign of Y, yaw, soldier mesh, banner meshes, elephant tint, chariot)
SIDES = {
    "Pandava": dict(sy=-1, yaw=0.0, soldier="KRK_SoldierProxy_Pandava", soldier_final="krk_pandava_archer",
                    banners=["KRK_BannerPole_Saffron_Tall", "KRK_BannerPole_Saffron_Short"],
                    tents=["KRK_Tent_Saffron", "KRK_Tent_Marble"], chariot="hst_royal_chariot", tint="Saffron"),
    "Kaurava": dict(sy=1, yaw=180.0, soldier="KRK_SoldierProxy_Kaurava", soldier_final="krk_kaurava_soldier",
                    banners=["KRK_BannerPole_Red_Tall", "KRK_BannerPole_Red_Short"],
                    tents=["KRK_Tent_Red"], chariot="krk_duryodhana_chariot", tint="Red"),
}

STRIP_HALF = 90       # m: half-width of the empty middle ground (v3: hosts closer)
FRONT = 1100          # m: width of each host's front (v2: narrower, deeper blocks)
LANE_EVERY = 260      # m: chariot lane spacing along the front
LANE_W = 24           # m
SPACING = 1.4         # m between files (close order)
RANK_GAP = 1.7        # m between ranks
LINE_EVERY = 10       # ranks per line; lines are split by a 4 m gap (v3: solid masses)
CAMP_BACK = 120       # m: camp distance behind the rear line (v3: camps read in the wide shot)


def xf(x, y, z=0.0, yaw=0.0, s=1.0):
    return [round(x * M, 1), round(y * M, 1), round(z * M, 1), round(yaw, 2), round(s, 3)]


def build(per_side):
    rng = random.Random(SEED)
    groups = {}  # mesh -> {"folder":..., "instances":[...]} for instanced crowds/props
    heroes = []  # single actors

    def add(mesh, folder, t):
        groups.setdefault(mesh, {"folder": folder, "instances": []})["instances"].append(t)

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
                add(cfg["soldier"], f"KRK/{side}/Infantry",
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
                for h in range(4):
                    add("hst_white_horse", f"KRK/{side}/Horses",
                        xf(lx - 1.8 + h * 1.2, cy - sy * 4.2, 0, yaw))

        # war elephants: a line behind the infantry
        for ex in range(-FRONT // 2 + 30, FRONT // 2, 55):
            add(f"hst_war_elephant@{cfg['tint']}", f"KRK/{side}/Elephants",
                xf(ex + rng.uniform(-6, 6), sy * (depth + 22 + rng.uniform(-3, 3)), 0, yaw + rng.uniform(-8, 8)))

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
        heroes.append({"mesh": "krk_war_tent", "label": f"KRK3D_{side}_CommandTent",
                       "folder": f"KRK/{side}/Camp", "t": xf(0, cy0, 0, yaw)})

    # ground scatter (v2): dry grass and stones break up the flat plain
    for i in range(9000):
        if i % 3 == 0:
            x, y = rng.uniform(-260, 260), rng.uniform(-STRIP_HALF, STRIP_HALF)  # near the strip
        else:
            x, y = rng.uniform(-1600, 1600), rng.uniform(-1300, 1300)
        add("KRK_GrassTuft" if i % 4 else "KRK_Rock", "KRK/Ground",
            xf(x, y, 0, rng.uniform(0, 360), rng.uniform(0.6, 1.8)))

    # hero pieces, fixed positions
    heroes += [
        {"mesh": "hst_arjuna_chariot", "label": "KRK3D_Arjuna_Chariot", "folder": "KRK/Heroes", "t": xf(0, 0, 0, 0)},
        {"mesh": "krk_ape_banner", "label": "KRK3D_Arjuna_ApeBanner", "folder": "KRK/Heroes",
         "t": xf(0, -1.6, 0, 0, 1.4)},
        {"mesh": "krk_bhishma_chariot", "label": "KRK3D_Bhishma_Chariot", "folder": "KRK/Heroes",
         "t": xf(-40, STRIP_HALF + 12, 0, 180)},
        {"mesh": "krk_duryodhana_chariot", "label": "KRK3D_Duryodhana_Chariot", "folder": "KRK/Heroes",
         "t": xf(25, STRIP_HALF + 16, 0, 180)},
        {"mesh": "krk_war_drum_cart", "label": "KRK3D_Kaurava_DrumCart", "folder": "KRK/Heroes",
         "t": xf(-70, STRIP_HALF + 20, 0, 180)},
    ]
    for i in range(4):
        heroes.append({"mesh": "hst_white_horse", "label": f"KRK3D_Arjuna_Horse{i + 1}", "folder": "KRK/Heroes",
                       "t": xf(-1.8 + i * 1.2, 4.2, 0, 0)})

    cameras = [
        {"label": "KRK_CAM_Wide", "loc": xf(-660, -10, 45)[:3], "rot": [-4.0, -15.0, 0.0], "fov": 60,
         "note": "Establishing: both hosts across the empty strip, low sun behind the Kaurava side"},
        {"label": "KRK_CAM_HeroChariot", "loc": xf(-7, -11, 1.4)[:3], "rot": [6.0, 57.0, 0.0], "fov": 50,
         "note": "Low hero angle on Arjuna's chariot alone in the middle ground (SH080)"},
        {"label": "KRK_CAM_Bhishma", "loc": xf(-30, 30, 2.2)[:3], "rot": [2.0, 105.0, 0.0], "fov": 30,
         "note": "Across the field to Bhishma's car from Arjuna's side (SH030/SH100)"},
    ]
    sun = {"pitch": -11.0, "yaw": -95.0, "color": "#FFC37A", "fog_color": "#B48A5A", "fog_density": 0.008, "clouds": True}
    return {"world": "Kurukshetra", "seed": SEED, "per_side": per_side, "terrain": "KRK_Terrain",
            "groups": groups, "heroes": heroes, "cameras": cameras, "sun": sun}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-side", type=int, default=20000)
    ap.add_argument("--out", default="layout.json")
    a = ap.parse_args()
    data = build(a.per_side)
    with open(a.out, "w") as f:
        json.dump(data, f, indent=1)
    n = sum(len(g["instances"]) for g in data["groups"].values())
    print(f"{n} instances in {len(data['groups'])} groups, {len(data['heroes'])} hero actors -> {a.out}")
    for k, g in sorted(data["groups"].items()):
        print(f"  {k:36s} {len(g['instances']):5d}")


if __name__ == "__main__":
    main()
