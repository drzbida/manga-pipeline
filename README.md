# Manga url to ePUBs pipeline

This is a **swiftly thrown together** script to automate manga reading workflows for e‑readers, so I can avoid the pain of doing it manually. It:

* Downloads manga chapters via `gallery-dl`
* Splits them into fixed-size batches (so EPUBs don’t get huge or mix up chapters)
* Converts each batch into an EPUB with KCC

## Prerequisites

1. **Python** (3.7+) -> no external libraries are used as of now

2. **gallery-dl** in your `$PATH`

3. **KCC** executable (e.g. `KCC_c2e_7.4.1.exe` or whatever the latest version is) downloaded from:

   [https://github.com/ciromattia/kcc/releases](https://github.com/ciromattia/kcc/releases)

4. **For linux users only:** you’ll also need `wine` to run the KCC `.exe`.

It *probably* also works on macOS with wine. Tested on arch + wine 10.8 and windows11.

## Usage

```bash
$ python manga-pipeline.py --help
usage: manga-pipeline.py [-h] -u MANGA_URL -k KCC [--wine WINE] [-b BATCH_SIZE] [-m MIN_CHAPTER] [-x MAX_CHAPTER] [-w CUSTOM_WIDTH] [-e CUSTOM_HEIGHT]

Download manga chapters, batch them, and convert to EPUB.

options:
  -h, --help            show this help message and exit
  -u, --manga-url       URL of the manga series/chapters (required)
  -k, --kcc             Path to the KCC executable (required)
  --wine WINE           Run KCC under Wine (default: False)
  -b, --batch-size      Number of chapters per EPUB (default: 20)
  -m, --min-chapter     First chapter to download (optional)
  -x, --max-chapter     Last chapter to download (optional)
  -w, --custom-width    Width for KCC (default: 1264)
  -e, --custom-height   Height for KCC (default: 1680)
```

**Example:** grab *The Apothecary Diaries* chapters 15–76, 15 chapters per EPUB, on linux (using wine):

```bash
$ python manga-pipeline.py \
    -u https://weebcentral.com/series/01J76XYCCTKZ5GDQ05600AG7TQ/Kusuriya-No-Hitorigoto \
    -b 15 -m 15 -x 76 --wine --kcc kcc-cli.exe
```

**Resulting EPUBs (`epubs/`):**

```bash
$ ls -lh epubs
total 1002M
-rw-r--r-- 1 bida bida 203M May 28 00:49 'The Apothecary Diaries_015_029.epub'
-rw-r--r-- 1 bida bida 235M May 28 00:49 'The Apothecary Diaries_030_044.epub'
-rw-r--r-- 1 bida bida 247M May 28 00:50 'The Apothecary Diaries_045_059.epub'
-rw-r--r-- 1 bida bida 271M May 28 00:50 'The Apothecary Diaries_060_074.epub'
-rw-r--r-- 1 bida bida  49M May 28 00:50 'The Apothecary Diaries_075_076.epub'
```

> [!WARNING]  
> All output folders are cleared between runs (including `epubs/`)
---

## Future (maybe)

* Clean up a bit
* Add auto-transfer options (e.g. mount-and-copy when tablet’s plugged in, SSH copy (e.g with Koreader ssh server), cloud upload)

## Support these projects which do all the work
* [Kindle Comic Converter](https://github.com/ciromattia/kcc)
* [gallery-dl](https://github.com/mikf/gallery-dl)
