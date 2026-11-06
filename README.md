# Edvin Joseph

Portfolio site, served by GitHub Pages at https://edvinjoseph.github.io/.

`src.html` is the source. `build.py` writes `index.html` from it:

```
python build.py
```

It needs Python with Pillow. Images live in `w/`. The build also writes right-sized WebP copies to `w/opt/` and points the page at them; the originals stay for the links that open them. Copies are only remade when a source changes, so the first build is slow and later ones are quick. Pushing to `main` deploys the site through `.github/workflows/pages.yml`.

## Changing the film reviews

The Writing section comes from `reviews.json`. Each entry names a film by its Letterboxd address, the part after `letterboxd.com/film/`:

```json
{ "film": "dead-poets-society", "quote": "The line from your review to show." }
```

Leave out `quote` to show your whole review text. Add, remove or reorder entries, then run `python build.py`. It fetches each film's title, year, poster and your star rating from Letterboxd, saves new posters in `w/posters/`, and keeps a copy of what it fetched in `letterboxd-cache.json` so the page still builds offline.

## Credits

The 3D Mac (`w/mac-classic-glb.json`, a GLB stored as base64 in JSON, and its texture `w/mac-classic.jpg`) is based on "[Macintosh Classic (1991)](https://sketchfab.com/3d-models/macintosh-classic-1991-3b66e98d137d4a23aaa725ce0a8aec28)" by [Daniel O'Neil](https://sketchfab.com/doneil), licensed under [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/). Changes: the texture was resized to 2048px and the screen shows a screenshot drawn in by the page. It is drawn with [three.js](https://threejs.org), loaded from jsDelivr.
