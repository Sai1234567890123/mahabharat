# Mahabharata Series Bible (working draft)

**Source of record:** Kisari Mohan Ganguli, *The Mahabharata of Krishna-Dwaipayana Vyasa, Translated into English Prose* (1883–1896), Project Gutenberg eBook #7864 (public domain in the US). Local copies: `source/B01-adi.txt` to `source/B18-svargarohana.txt`. Chapter IDs and line numbers in the database refer to these files.

**Scope:** all 18 parvas of Ganguli's translation, from the Project Gutenberg volumes and single-parva eBooks. Source text for each parva is in `source/`. Chapter counts and gaps are in `db/books.csv`.

## Structure and IDs
- Book → Chapter (Ganguli "Section") → Scene → Shot. IDs: `B01C001` (chapter), `B01C001S01` (scene), `B01C001S01H01` (shot).
- A **scene** is a run of up to 5 consecutive paragraphs. This is a mechanical segmentation, not a dramatic one. Scene summaries are blank until a reading pass fills them.
- A **shot** is one paragraph of the source. It keeps its source line number, so any shot can be checked against the text.
- Summaries, tags, and visual notes are added by hand. Blank fields mean "not yet written", not "nothing happens".

## Frame narrative (Adi Parva, sections 1–2)
- Ugrashrava Sauti, son of Lomaharshana, recites the epic to the sages at Shaunaka's long sacrifice in the Naimisha forest.
- Sauti tells the sages about the gods' and sages' ancestry, the Bhrigu lineage, and the Puranic background before the central story.
- Vyasa composed the epic. Vaishampayana later recited it to King Janamejaya, who was hearing about his ancestors during his serpent sacrifice.

## Characters (first appearance in Adi Parva, from text search)
| Character | Role | Notes |
|---|---|---|
| Vyasa (Krishna-Dwaipayana) | Author-sage | Son of Satyavati and the sage Parashara; appears from the opening; fathers Dhritarashtra, Pandu, Vidura |
| Sauti | Narrator | Recites to the sages at Naimisha |
| Janamejaya | Listener, king | Hears the epic at his serpent sacrifice; his ancestry is the frame |
| Uparichara Vasu | Early king | Named early in the book; the ancestry he founds leads to Satyavati |
| Shantanu | King of Hastinapura | Marries Ganga; later marries Satyavati |
| Ganga | River goddess | Bears Shantanu's sons, who are returned to the river |
| Bhishma (Devavrata) | Shantanu's son | Takes a vow of celibacy; later the eldest elder of the Kuru house |
| Satyavati | Fisher-born queen | Bears Vyasa before marriage; her line continues the Kuru dynasty |
| Pandu | King | Sons: the five Pandavas |
| Dhritarashtra | King (blind) | Father of the Kauravas; married to Gandhari |
| Vidura | Half-brother | Son of Vyasa and a serving woman; a counsellor |
| Kunti | Queen | Receives a boon to summon gods; bears Yudhishthira, Bhima, Arjuna |
| Madri | Queen | Bears the twins Nakula and Sahadeva |
| Drona | Teacher of arms | Trains the princes; a rival and later a teacher to the Pandavas |
| Karna | Warrior | Appears with the tournament episodes |
| Draupadi | Princess | Swayamvara (contest) at Panchala |
| Krishna | Divine figure | Named across the book; cousin and ally of the Pandavas |
| Balarama | Krishna's brother | Named in the Yadava genealogy |
| Shakuntala and Dushyanta | Parents of Bharata | Source of the Bharata line (name check needed in text; the spelling in this translation may differ) |
| Yayati, Devayani, Sharmishtha | Royal and sage families | Devayani appears around section 75; Yayati is named from section 1 |
| Ekalavya | Forest archer | Appears around section 67 |
| Kadru and Vinata | Serpent and bird mothers | Appear around section 16; the Garuda/Naga rivalry starts there |
| Takshaka | Naga king | Named from section 3 |
| Astika | Sage | Named from section 1; plays a role in the serpent-sacrifice frame |
| Agni | Fire god | Named from section 1; with Arjuna, burns the Khandava forest |

Names are spelt as Ganguli prints them. Any spelling change for the series should be recorded in the table, not in the source.

## Places
- Naimisha forest: site of the frame recitation.
- Hastinapura: the Kuru capital; Shantanu's and the Kauravas' seat.
- Indraprastha: the Pandavas' city, built from the Khandava forest after it is burned.
- Panchala: Draupadi's kingdom; swayamvara site.
- Lac house (Jatugriha, around section 143): the house built to burn the Pandavas. They escape through a tunnel.

## Factions
- **Kuru house:** Bhishma, Dhritarashtra, Vidura, Pandu's line, Duryodhana and the Kauravas.
- **Pandavas:** Yudhishthira, Bhima, Arjuna, Nakula, Sahadeva, with Draupadi.
- **Serpents (Nagas):** Takshaka and the Naga kings. Their enmity with the Garuda birds starts in Adi Parva.
- **Gods and sages:** Indra, Agni, Vyasa, Narada, Vasishtha.

## Timeline (Book 1 only, in story order, not section order)
1. The Bhrigu and Puranic background, and the frame recitation.
2. Vasu, Satyavati, Vyasa's birth.
3. Shantanu, Ganga, Bhishma's vow.
4. Pandu's marriages and curse; Kunti's boons; the five Pandavas' births.
5. Dhritarashtra's line and the rivalry; the princes' training under Drona.
6. The lac-house escape; Draupadi's swayamvara and the shared marriage.
7. The Khandava forest burned for Agni; the founding of Indraprastha.
8. Serpent and bird enmity (Kadru, Vinata, Garuda); Takshaka and the serpent sacrifice frame.

Section numbers in the timeline are approximate and come from name search. Each event must be checked against its section before it is used in a script.

## World rules (working)
- Dharma, kinship, and oath carry weight. Oaths are kept even at great cost.
- Boons and curses take effect exactly as stated.
- Gods and sages appear among humans and can father children.

## Visual style notes (to be confirmed against the production look)
- Palette and texture follow the existing trailer look in `trailer-analysis/`. This file does not set it.
- Forest and fire scenes (Khandava) and the lac house are candidate set pieces.

## Parvas (structure, from db/books.csv)
| Book | Parva | Chapters | Numbering | Missing headings (source has no heading) |
|---|---|---|---|---|
| 1 | Adi Parva | 236 | roman | - |
| 2 | Sabha Parva | 79 | roman | 67 |
| 3 | Vana Parva | 313 | roman | - |
| 4 | Virata Parva | 71 | roman | 23 |
| 5 | Udyoga Parva | 199 | roman | - |
| 6 | Bhishma Parva | 124 | roman | - |
| 7 | Drona Parva | 200 | roman | 54 55 189 |
| 8 | Karna Parva | 96 | arabic | - |
| 9 | Shalya Parva | 65 | arabic | - |
| 10 | Sauptika Parva | 18 | arabic | - |
| 11 | Stri Parva | 27 | arabic | - |
| 12 | Shanti Parva | 363 | roman | 35 364 |
| 13 | Anushasana Parva | 168 | roman | - |
| 14 | Aswamedhika Parva | 92 | roman | - |
| 15 | Asramavasika Parva | 39 | roman | - |
| 16 | Mausala Parva | 8 | arabic | - |
| 17 | Mahaprasthanika Parva | 3 | arabic | - |
| 18 | Svargarohana Parva | 6 | arabic | - |

Notes: Karna, Shalya, Sauptika, and Stri were cut at their title lines, not at the volume's book markers. Those markers sit after the sections they introduce. The gap entries are sections the Gutenberg text never gives a heading for, so their text runs into the chapter before. Shanti's '34-35' heading is one combined chapter.
