# Unreal Engine 5.8 Previs Import Checklist: "The First Conch" Pilot

This document establishes the definitive specification and workflow for transferring the 18 pilot previs shots from Blender (`scripts/blockout.py`) into Unreal Engine 5.8 (`/Game/Previs/`).

---

## 1. Pipeline Architecture & Unit Conversion

| Dimension | Blender Space | Unreal Engine 5 Space | Transformation Rule |
|---|---|---|---|
| **System** | Right-Handed, Z-Up | Left-Handed, Z-Up | Invert Y-axis upon FBX/GLB coordinate transform |
| **Length Units** | Metric: Meters ($1.0\text{ m}$) | Centimeters ($1.0\text{ cm} = 1.0\text{ UU}$) | **Scale Factor: 100×** ($1\text{ m} \to 100\text{ cm}$) |
| **Framerate** | 24 fps | 24 fps (Level Sequence timebase) | Set Sequencer display rate to `24 fps Film` |
| **Aspect Ratio** | 2.39:1 Anamorphic Widescreen | 2.39:1 Cinematic Filmback | Sensor Width: `36.0 mm`, Sensor Height: `15.06 mm` |
| **Camera Class** | Cycles Perspective Camera | `CineCameraActor` | Map `lens` directly to `Current Focal Length (mm)` |

---

## 2. Master Shot & Camera Mapping Table (All 18 Shots)

Every focal length is grounded in `data/shots.json` with direct line references. Target positions and camera locations are converted from Blender meters to Unreal centimeters ($100\times$).

| Shot ID | Act | Title | Unreal Level Path | Camera Actor Name | Lens (mm) & Source Line | Camera Location (UE cm: X, Y, Z) | LookAt Target (UE cm: X, Y, Z) | Required 3D Assets & Staging |
|---|---|---|---|---|---|---|---|---|
| **SH010** | A | The field at dawn | `/Game/Previs/SH010_Field` | `CineCamera_SH010` | **45mm** ([shots.json:L230](data/shots.json#L230)) | `(-1400, -20000, 1200)` | `(0, 6000, 900)` | Ground plane, Pandava/Kaurava army blocks, Arjuna chariot (front pos), ape banner, low sun, dust cards |
| **SH020** | A | The ape banner | `/Game/Previs/SH010_Field` | `CineCamera_SH020` | **70mm** ([shots.json:L286](data/shots.json#L286)) | `(500, -12200, 140)` | `(0, -10060, 920)` | Arjuna chariot, ape banner standard, golden sun light, dust cards |
| **SH030** | A | The grandsire's roar | `/Game/Previs/SH010_Field` | `CineCamera_SH030` | **28mm** ([shots.json:L342](data/shots.json#L342)) | `(-1950, 9300, 140)` | `(-1200, 9650, 300)` | Bhishma white chariot, palmyra standard, Bhishma (`roar`), Duryodhana (`mace`), Kaurava host |
| **SH040** | A | Bhishma's conch | `/Game/Previs/SH010_Field` | `CineCamera_SH040` | **50mm** ([shots.json:L392](data/shots.json#L392)) | `(-1600, 9100, 260)` | `(-1200, 9600, 285)` | Bhishma white chariot, Bhishma (`conch`), Duryodhana (`mace`), Gangaputra conch, Kaurava host |
| **SH050** | A | Like a thousand suns | `/Game/Previs/SH010_Field` | `CineCamera_SH050` | **35mm** ([shots.json:L452](data/shots.json#L452)) | `(1300, -9300, 100)` | `(0, -9930, 260)` | Arjuna chariot, 4 white steeds, Krishna (`reins`), Arjuna (`bow_rest`), ape banner, bells, dust |
| **SH060** | A | Panchajanya & Devadatta | `/Game/Previs/SH010_Field` | `CineCamera_SH060` | **50mm** ([shots.json:L509](data/shots.json#L509)) | `(0, -9300, 260)` | `(0, -10000, 260)` | Arjuna chariot (hide horses), Krishna (`conch_lift`), Arjuna (`conch_lift`), Panchajanya, Devadatta |
| **SH070** | A | They blow together | `/Game/Previs/SH010_Field` | `CineCamera_SH070` | **30mm** ([shots.json:L558](data/shots.json#L558)) | `(550, -9350, 60)` | `(0, -9980, 290)` | Arjuna chariot (hide horses), Krishna (`conch`), Arjuna (`conch`), conches, ape banner |
| **SH080** | A | Paundra & Anantavijaya | `/Game/Previs/SH010_Field` | `CineCamera_SH080` | **35mm** ([shots.json:L632](data/shots.json#L632)) | `(-2250, -10100, 160)` | `(-3300, -10750, 290)` | Bhima chariot & Paundra conch (`conch`), Yudhishthira chariot, parasol & Anantavijaya (`conch`), Pandava host |
| **SH090** | A | The blare | `/Game/Previs/SH010_Field` | `CineCamera_SH090` | **20mm** ([shots.json:L695](data/shots.json#L695)) | `(1400, 12800, 220)` | `(0, -10000, 1400)` | Kaurava frontline soldiers recoiling, ground plane, distant Pandava line, dust cloud |
| **SH100** | B | Between the two armies | `/Game/Previs/SH010_Field` | `CineCamera_SH100` | **35mm** ([shots.json:L774](data/shots.json#L774)) | `(120, -10550, 320)` | `(0, -9600, 260)` | Arjuna chariot, Krishna (`reins`), Arjuna (`bow_rest`), ape banner, quiet Pandava front |
| **SH110** | B | The empty ground | `/Game/Previs/SH010_Field` | `CineCamera_SH110` | **16mm** ([shots.json:L820](data/shots.json#L820)) | `(7000, -600, 7000)` | `(0, -600, 0)` | Empty center stripe, Arjuna chariot rolling into center (`between`), both host army walls |
| **SH120** | B | Faces of kin | `/Game/Previs/SH010_Field` | `CineCamera_SH120` | **85mm** ([shots.json:L870](data/shots.json#L870)) | `(-5, -860, 295)` | `(-1200, 9600, 260)` | Arjuna chariot (foreground shoulder), distant Bhishma car (`stand`), Duryodhana (`mace`), Kaurava elders |
| **SH130** | B | Gandiva slips | `/Game/Previs/SH010_Field` | `CineCamera_SH130` | **50mm** ([shots.json:L910](data/shots.json#L910)) | `(1150, -600, 190)` | `(0, -600, 180)` | Arjuna chariot, Krishna (`reins`), Arjuna slumped (`slump`), Gandiva bow slipping/falling |
| **SH140** | B | Krishna turns | `/Game/Previs/SH010_Field` | `CineCamera_SH140` | **85mm** ([shots.json:L961](data/shots.json#L961)) | `(30, -160, 280)` | `(30, -555, 286)` | Krishna (`turn`), Arjuna (`slump`), chariot seat (hide horses & banner), halo card anchor |
| **SH150** | C | The universal form | `/Game/Previs/SH010_Field` | `CineCamera_SH150` | **12mm** ([shots.json:L1025](data/shots.json#L1025)) | `(600, -1600, 100)` | `(0, 40000, 18500)` | Arjuna chariot, Arjuna (`stand`), Vishvarupa cosmic hierarchy (10 extra arms, halo cards, star dome) |
| **SH160** | C | Arjuna beholds | `/Game/Previs/SH010_Field` | `CineCamera_SH160` | **18mm** ([shots.json:L1098](data/shots.json#L1098)) | `(5, -760, 250)` | `(-100, 40000, 16000)` | Arjuna shoulder (`stand`), cosmic Vishvarupa background, glowing rings, star dome |
| **SH170** | D | Arjuna rises | `/Game/Previs/SH010_Field` | `CineCamera_SH170` | **24mm** ([shots.json:L1158](data/shots.json#L1158)) | `(260, -340, 120)` | `(-35, -620, 300)` | Arjuna rising (`bow_raise`), Gandiva bow with lightning anchor, Krishna (`reins`), chariot body |
| **SH180** | D | The banner, then black | `/Game/Previs/SH010_Field` | `CineCamera_SH180` | **85mm** ([shots.json:L1220](data/shots.json#L1220)) | `(1290, 3640, 490)` | `(0, -655, 900)` | Ape banner on tall gold standard, snapping in wind, hot war sun, dust clouds |

---

## 3. Asset Breakdown & Unreal Representation

### 3.1 Environments & Sets
1. **Kurukshetra Ground Plane (`SM_Ground_Kurukshetra`)**:
   - Flat plain centered at $(0, 0, 0)$ extending $\pm 1000\text{ m}$ ($100,000\text{ UU}$).
   - Material: Pale ochre dust, trampled dry grass, chariot rut normals.
2. **Armies (`SM_Army_Pandava_Cards`, `SM_Army_Kaurava_Cards`)**:
   - Instanced Static Meshes (ISM) or Niagara crowd cards.
   - Pandava Line: Screen-left ($Y < -110\text{ m}$), upright standards.
   - Kaurava Line: Screen-right ($Y > 110\text{ m}$), denser formation, darker standards.
   - Empty No-Man's Ground: Between $Y = -110\text{ m}$ and $Y = +110\text{ m}$.
3. **Sky Domes (`BP_Sky_Previs`)**:
   - Swappable sky materials matching Act color palettes:
     - **Act A**: Apricot dawn haze (`#FFE2B0`), golden dust.
     - **Act B**: Overcast muted grey/cloud cover, diffused sun.
     - **Act C**: Cosmic void, deep nebula, star field, yantra cards.
     - **Act D**: Hot orange war sun, red dust haze.

### 3.2 Hero Chariots & Vehicles
1. **Arjuna's Golden Chariot (`BP_Chariot_Arjuna`)**:
   - Components: Gold body mesh, 2 spoked wheels, harness, 4 white horses (`SM_Horse_White_01-04`), ape banner standard (`SM_Standard_Ape`).
   - Sockets/Locators: `Seat_Krishna`, `Stand_Arjuna`, `Anchor_Banner`, `Anchor_Hub`.
2. **Bhishma's White Chariot (`BP_Chariot_Bhishma`)**:
   - Components: White carved body, silver trim, gold palmyra tree standard with 5 stars (`SM_Standard_Palmyra`).
   - Sockets: `Stand_Bhishma`, `Stand_Duryodhana`.
3. **Secondary Chariots**:
   - `BP_Chariot_Bhima`: Heavy car with lion emblem.
   - `BP_Chariot_Yudhishthira`: Royal car with golden royal parasol.

### 3.3 Characters & Pose Proxies
Humanoid proxies built with modular capsule/metaball topology in Blender (`humanoid()` in `blockout.py`). In Unreal, use skeletal or static pose meshes:
- `SK_Krishna`: Poses `reins`, `conch_lift`, `conch`, `turn`.
- `SK_Arjuna`: Poses `bow_rest`, `conch_lift`, `conch`, `slump`, `stand`, `bow_raise`.
- `SK_Bhishma`: Poses `stand`, `roar`, `conch`.
- `SK_Duryodhana`: Pose `mace`.
- `SK_Bhima`: Pose `conch`.
- `SK_Yudhishthira`: Pose `conch`.
- `SK_Vishvarupa`: Multi-armed cosmic form (10 extra arms proxy mesh).

### 3.4 Hero Props
- `SM_Bow_Gandiva`: Tall horn-and-gold recurve bow.
- `SM_Conch_Panchajanya`: Krishna's white spiral conch with gold mouthpiece.
- `SM_Conch_Devadatta`: Arjuna's pearl conch with silver/blue bands.
- `SM_Conch_Paundra`: Bhima's heavy ribbed conch with iron bands.
- `SM_Conch_Anantavijaya`: Yudhishthira's gold-banded conch.
- `SM_Conch_Gangaputra`: Bhishma's white conch.

---

## 4. Blender to Unreal Export & Import Steps

### Step 1: Blender Export Configuration
When exporting assets or layout scenes from Blender via `bpy`:
- **Format**: FBX (`bpy.ops.export_scene.fbx`) or glTF 2.0 (`bpy.ops.export_scene.gltf`).
- **Scale**: Set `Apply Scalings` to `FBX All`, Scale = `100.0` (or set Scene Units to Metric, Unit Scale = `0.01` before export).
- **Forward / Up**: Forward = `-Z Forward`, Up = `Y Up` (Standard FBX convention for Unreal import conversion).
- **Hierarchy**: Maintain empty parent locators (`empty()` in `blockout.py`) as transform groups/sockets.

### Step 2: Unreal Engine Content Browser Setup
Create the folder structure:
```
/Game/
  └── Previs/
      ├── SH010_Field (Master Level)
      ├── Cameras/
      ├── Sequences/
      │   ├── LS_Pilot_Master
      │   └── Shots/ (LS_SH010 to LS_SH180)
      ├── Meshes/
      │   ├── Characters/
      │   ├── Vehicles/
      │   ├── Props/
      │   └── Environment/
      └── Materials/
```

### Step 3: Camera & Level Sequence Setup
1. In `/Game/Previs/SH010_Field`, create a CineCameraActor for each shot (`CineCamera_SH010` to `CineCamera_SH180`).
2. Set Cine Camera attributes:
   - **Sensor Width**: `36.0 mm`
   - **Sensor Height**: `15.06 mm` (2.39:1 aspect ratio)
   - **Current Focal Length**: set to the exact millimeter value specified in Section 2.
3. Align Camera Transform ($X, Y, Z$) to the coordinates in Section 2.
4. Spawn a `TargetMarker` actor at the LookAt Target coordinates and set `CameraComponent -> Lookat Tracking Settings` to track the target actor.
5. In Sequencer (`LS_Pilot_Master`), create 18 shot tracks with the durations defined in `data/shots.json`.

---

## 5. Verification Checklist

- [x] All 18 shots covered with lens, position, target, and asset dependencies.
- [x] Every focal length cited with line number from `data/shots.json`.
- [x] Coordinate space and scaling conversion explicitly mapped (Blender meters $\times 100 \to$ Unreal cm).
- [x] Staging visibility overrides accounted for (e.g., hidden horses in SH060, SH070, SH140, SH170).
- [x] Asset naming conventions standardized under `/Game/Previs/`.
