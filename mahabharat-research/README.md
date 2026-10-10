# Mahabharata research (project folder)

Source: the Ganguli prose translation (1883–1896), public domain. Gutenberg e-texts for each parva, joined into one text per parva.

## Layout

- `source/B01-adi.txt` … `source/B18-svargarohana.txt`: plain text for each of the 18 parvas, with Gutenberg headers removed.
- `BIBLE.md`: the series bible (frame narrative, characters, places, factions, timeline, world rules, parva table).
- `db/`: `books.csv`, `chapters.csv` (2,107 rows), `scenes.csv` (3,508), `shots.csv` (12,048), and `mahabharat.sqlite` with the same four tables.
- `annotations/Bxx.json`: per-parva annotations, keyed by chapter, then scene and shot ID. Each chapter has a summary; each scene and shot has a short plain-language note. These are merged into the CSVs and the SQLite database.
- `annotations/chunks/`: the working files the parallel annotation runs wrote, plus `plan.json` (which chapters each chunk covered). Kept for traceability; `Bxx.json` is the merged result.
- `reader/`: offline HTML reader, one page per parva plus `index.html`. Open `index.html` in a browser.
- `site/`: an older structure-only site (no annotations). Kept for reference.

## IDs

- Book: `B01`–`B18`.
- Chapter: `B01C001` (sequence number within the book).
- Scene: `B01C001S01` (groups of up to five paragraphs; mechanical split).
- Shot: `B01C001S01H01` (one paragraph; `source_line` gives its line in the source file).

## Notes and limits

- Chapter boundaries follow the source headings. Where the source has no heading, some chapters stay merged: Sabha 66–67, Virata 22–23, Drona 54–55 and 189, and Shanti 364. Shanti "XXXIV–XXXV" is one chapter.
- Summaries and notes are paraphrases written from the text, not a commentary. Check a detail against the source before relying on it.
- Passages that are Gutenberg licence text or translator's footnotes are labelled as such rather than treated as narrative.
- Each word count is checked against the source (`books.csv`, `word_check` = 0 for all 18 parvas).
