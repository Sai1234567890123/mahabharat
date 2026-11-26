# Series plan: the Mahabharat in story order

Status: **draft for sai's review** (2026-11-26).

**Decision (sai, 2026-11-26):** the series is told in story order. It begins with Vyasa dictating the epic to Ganesha and ends with Gandhari's curse on Krishna after the war. The finished Arjuna vs Karna duel ("The Anjalika") is released first as a **teaser**. It returns as its own episode when the story reaches the Karna Parva.

This closes the open question in `preproduction/COMMS/VISION_PLAN.md` (item 10, "Kurukshetra or Adi Parva").

## Format

- **Length:** each episode is 60 to 90 seconds, built around **one key scene** in 16:9 with a 9:16 safe area, as already locked for the web series.
- **Between episodes:** the gap is bridged by a short narrator line over the opening title. The voice is Vyasa, framed as telling the story to Ganesha.
- **Chapter ids:** every chapter id below (for example `B01C100`) points to `mahabharat-research/db/chapters.csv`, where each id has its line range in `source/`. Some ranges are marked "about": find the exact chapter during that episode's canon lock, which is pipeline step 1.
- **Pipeline:** every episode goes through the twelve steps in `pipeline.md`.
- **Compilations:** if longer viewing is wanted later, every three to four episodes can be cut into one 5-minute compilation without new animation.

## Season 1. Origins (Adi Parva)

| Ep | Title | The one key scene | Source chapters |
|---|---|---|---|
| 1 | The Scribe | Vyasa dictates the epic; Ganesha agrees to write only if Vyasa never pauses, and Vyasa asks that Ganesha understand every verse before writing. | B01C001 (lines about 456-480) |
| 2 | The River Queen | Ganga marries Shantanu on one condition, drowns seven sons, and leaves when he stops the eighth. | B01C097-B01C099 |
| 3 | The Son Returns | Ganga brings back the grown Devavrata; Shantanu accepts him as son and heir. | B01C100 |
| 4 | The Terrible Vow | Devavrata gives up the throne and marriage for his father's wish to marry Satyavati, and becomes Bhishma. | B01C100-B01C101 |
| 5 | Three Princesses | Bhishma carries off the princesses of Kashi; Amba is turned away by everyone. | B01C102 (Amba's later story: B05C174-B05C189) |
| 6 | Three Sons of Vyasa | The widows meet Vyasa: Dhritarashtra is born blind, Pandu pale, Vidura from the maid. | B01C103-B01C106 |
| 7 | The Sun's Child | Young Kunti tests Durvasa's mantra, Surya appears, and baby Karna is set afloat in a basket. | B01C111 |
| 8 | The Blindfold | Gandhari binds her eyes for her blind husband; the hundred sons are born from the vessels. | B01C110, B01C115-B01C116 |
| 9 | Pandu's Curse | Pandu shoots a mating deer and is cursed; the five Pandavas are born through the gods. | about B01C118-B01C124 |
| 10 | The Teacher | Drona arrives; Arjuna sees only the bird's eye; Ekalavya gives his thumb. | B01C131-B01C134 |
| 11 | The Tournament | Karna enters the arena and matches Arjuna, is mocked as a charioteer's son, and Duryodhana crowns him king of Anga. | B01C136-B01C139 |
| 12 | The Fee | The princes capture Drupada as Drona's fee, and the feud begins. | B01C140 |

## Season 2. Fire and Marriage (Adi Parva)

| Ep | Title | The one key scene | Source chapters |
|---|---|---|---|
| 13 | The House of Lac | The palace at Varanavata burns; the Pandavas escape through the tunnel. | B01C143-B01C148 |
| 14 | Hidimbi | Bhima kills the Rakshasa Hidimba and marries his sister (Ghatotkacha's mother). | B01C154-B01C157 |
| 15 | Bhima and Vaka | Bhima carries the cart of food to Vaka and kills him. | B01C162-B01C166 |
| 16 | The Swayamvara | Arjuna, disguised as a Brahmana, strings the bow and hits the target to win Draupadi. | B01C186-B01C191 |
| 17 | Share It | "Share what you have brought"; Kunti's words make Draupadi the wife of all five. | B01C193 onward |
| 18 | Subhadra | Arjuna drives off with Subhadra, with Krishna's blessing. | B01C222-B01C223 |
| 19 | Khandava | Arjuna and Krishna help Agni burn the Khandava forest (the root of Aswasena's hatred in the Karna duel). | B01C225-B01C230 |

## Season 3. The Dice (Sabha Parva)

| Ep | Title | The one key scene | Source chapters |
|---|---|---|---|
| 20 | The Hall of Illusions | Maya builds the hall; Duryodhana falls into the water and Draupadi laughs. | B02C001, B02C047 |
| 21 | Jarasandha | Bhima wrestles Jarasandha and splits him in two. | B02C014-B02C024 |
| 22 | Shishupala | At the Rajasuya, Krishna's discus ends Shishupala's hundredth insult. | B02C033-B02C043 |
| 23 | The Dice | Yudhishthira loses his kingdom, his brothers and himself to Shakuni. | B02C047-B02C065 |
| 24 | The Assembly | Draupadi is dragged into the hall; her cloth never ends; Bhima vows Duhshasana's blood. | B02C066 onward |
| 25 | Exile | The Pandavas leave for twelve years in the forest and one year in disguise. | end of B02 (about B02C076-B02C079) |

## Season 4. Forest and Disguise (Vana and Virata Parvas)

| Ep | Title | The one key scene | Source chapters |
|---|---|---|---|
| 26 | The Hunter | Arjuna fights Shiva disguised as a Kirata hunter and receives the Pashupata. | B03C039-B03C040 |
| 27 | Jayadratha | Jayadratha abducts Draupadi and is caught and shaved. | B03C262-B03C266 |
| 28 | The Earrings | Karna cuts off his armour and earrings and gives them to Indra. | B03C298-B03C301 |
| 29 | The Yaksha | At the poisoned lake, Yudhishthira answers the Yaksha's questions and his brothers live. | B03C310-B03C312 |
| 30 | Kichaka | In Virata's court Kichaka assaults Draupadi; Bhima kills him in the dance hall. | B04C014-B04C022 |
| 31 | Brihannala | Arjuna, disguised as a dance teacher, takes Prince Uttara's chariot and routs the Kuru army alone. | B04C035 onward |

## Season 5. The Road to War (Udyoga and Bhishma Parvas)

| Ep | Title | The one key scene | Source chapters |
|---|---|---|---|
| 32 | The Embassy | Krishna goes to Hastinapura for peace; when they try to seize him, he shows his universal form. | B05C090-B05C131 |
| 33 | Mother and Son | Kunti tells Karna he is her son; Karna refuses to leave Duryodhana but spares four brothers. | B05C137-B05C146 |
| 34 | The First Conch | The armies face each other and the conches sound (the old pilot "The First Conch"). | B06C025 |
| 35 | The Gita | Arjuna drops his bow; Krishna speaks. | B06C025-B06C042 |
| 36 | Bed of Arrows | Shikhandi in front, Arjuna behind; Bhishma falls onto a bed of arrows. | B06C120-B06C122 |
| 37 | Bhishma and Karna | Karna visits Bhishma, who tells him he knows he is Kunti's son. | B06C124 |

## Season 6. The War (Drona, Karna and Shalya Parvas)

| Ep | Title | The one key scene | Source chapters |
|---|---|---|---|
| 38 | The Wheel Formation | Abhimanyu breaks into the Chakravyuha and cannot get out. | about B07C033-B07C048 |
| 39 | Before Sunset | Arjuna kills Jayadratha as the sun returns from behind Krishna's darkness. | about B07C140-B07C145 |
| 40 | Ghatotkacha | Karna spends Indra's one-use dart on Ghatotkacha at midnight. | B07C173-B07C178 |
| 41 | "Ashvatthama Is Dead" | The half-truth; Drona lays down his weapons and dies. | B07C188-about B07C193 |
| 42 | Bhima's Vow | Bhima kills Duhshasana and keeps the vow from the assembly. | B08C083 |
| 43 | **The Anjalika** | Arjuna vs Karna, from the serpent arrow to the light entering the sun. **Built already:** 22 shots in `episodes/ep01_arjuna_vs_karna/`, released first as the teaser. | B08C089-B08C091 |
| 44 | The Mace | Bhima and Duryodhana duel; the blow below the waist; Balarama's anger. | B09C032-B09C058 |

## Season 7. Aftermath (Sauptika and Stri Parvas)

| Ep | Title | The one key scene | Source chapters |
|---|---|---|---|
| 45 | The Night Raid | Ashvatthama enters the sleeping camp and kills Draupadi's sons. | B10C001-B10C010 |
| 46 | Two Weapons | Ashvatthama and Arjuna release their weapons; Ashvatthama gives up his gem and is cursed. | B10C011-about B10C016 |
| 47 | The Field of Women | Gandhari sees the battlefield with inner sight and mourns. | B11C014-B11C024 |
| 48 | Karna's Mother | At the river offerings, Kunti reveals that Karna was her son. | B11C027 |
| 49 | **Gandhari's Curse** | Gandhari curses Krishna: in the thirty-sixth year his own race will destroy itself. Krishna accepts. This is the finale. | B11C025 (lines about 1915-1930) |

That gives 49 episodes in 7 seasons. At 60 to 90 seconds each, the whole series runs about 60 to 70 minutes.

## What this changes in the repo

- The duel folder keeps its name, `episodes/ep01_arjuna_vs_karna/`, so that no links break. In new documents it is called **the teaser**, and in the series it is **episode 43**.
- New episodes get folders named `episodes/s<season>e<ep>_<slug>/`, for example `episodes/s1e01_the_scribe/`.
- Step 1 (canon lock) for episode 1 comes next: check the Vyasa and Ganesha passage at B01 lines about 456-480 and write its shot cards.

## What sai should check

1. Is anything missing that must be in, for example Nala and Damayanti, Savitri, or Bhima and Hanuman?
2. Should Season 1 open with Vyasa and Ganesha as written here, or with the frame story of Sauti in the Naimisha forest?
3. Are 60 to 90 seconds per episode still right for a story this long, or should early seasons get 3 to 5 minute episodes?
