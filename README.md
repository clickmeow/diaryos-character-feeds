# DiaryOS Character Feeds

A portable static website for showing DiaryOS character timeline feeds.

## Online display

GitHub Pages should publish this repository from the `main` branch root. The public entry is:

- `index.html`: character list
- `characters/<character_id>/index.html`: read-only timeline page

The online site is display-only. It does not need Python, a backend, upload APIs, or editing permission.

## Local editing

The local editor is kept for maintaining feeds before publishing.

Run from this folder:

```powershell
python shared\serve_editor.py
```

Then open:

```text
http://127.0.0.1:8765/editor.html
```

Saving writes both `feed.json` and `feed.csv`. Uploaded images are saved into the character's `images/` folder and named from `post_id`.

To refresh the read-only pages after editing:

```powershell
python shared\render_feed.py
```

## Data contract

- `characters/<character_id>/feed.json`: editor source of truth.
- `characters/<character_id>/feed.csv`: spreadsheet and AI-friendly copy.
- `characters/<character_id>/images/`: post images.
- `characters/<character_id>/index.html`: generated read-only display page.

Future Ren'Py sync should read `feed.json`, generate a game import table or `sns_imported_data.rpy`, then run the DiaryOS game project's git backup and Ren'Py lint.
