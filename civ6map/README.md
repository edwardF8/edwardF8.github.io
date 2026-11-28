# Civ6 Atlas

An interactive world map of *Civilization VI*: World Wonders (53), Natural Wonders (34 + 3 scenario-only) and Civs (50, with 76 leaders), each pinned at its real-world location. Click a dot for in-game art, quotes and effects, real photographs, and history.

## Open it

Double-click `index.html`. It works straight from the file system, but you need an internet connection for the map tiles, fonts and photos.

If your browser blocks anything when the file is opened directly, serve the folder instead:

```bash
python3 -m http.server 8642 --directory civ6map
```

Then open <http://localhost:8642>.

## Using it

- **Click a dot** (or a name in the list) to open its panel. **Diamonds** are world wonders, coloured by era. **Circles** are natural wonders. **Emblem badges** are civilizations, placed at their historical capital. A **dashed ring** marks a legendary or approximate site.
- Each wonder panel opens with its in-game quote. Press the speaker button to hear it read aloud. Civ panels show every leader with portrait, quote, ability and agenda, and link to the civ's wonders.
- **Search** with the box, or press `/` to jump to it. Press `Enter` to open the first match.
- **Filter** by World/Natural and by era. The first era click shows only that era; later clicks add or remove eras.
- Use **←/→** to step through wonders, and **Esc** to close the panel.
- **Surprise me** opens a random wonder.
- Switch the base map between Satellite, Night, Terrain and Light (bottom right).
- Each wonder has its own link, e.g. `index.html#petra`.

## Files

| File | What it is |
| --- | --- |
| `index.html`, `styles.css`, `app.js` | The page (Leaflet map, panels, lightbox) |
| `data.js` | Generated data for all wonders: game stats, location, history, image URLs |
| `civs.js` | Generated data for all civs: leaders, abilities, uniques, history, photos |
| `quotes.js` | The in-game quote for every wonder |
| `tools/parse.py` | Parses the Civilization Wiki wonder tables (wikitext) into JSON |
| `tools/world.json`, `tools/natural.json` | Hand-written real-world data: location, coordinates, dates, history |
| `tools/build.py` | Merges everything, fetches Civ wiki art and Wikipedia/Commons photos, writes `data.js` |
| `tools/civs.json`, `tools/civ_build.py` | Researched civ list (capitals, history, linked wonders) and the script that adds Civ wiki leaders/uniques and photos, writing `civs.js` |
| `tools/quotes.py` | Pulls each wonder's in-game quote from the Civ wiki |

### Rebuilding `data.js`

```bash
cd civ6map/tools
curl -s "https://civilization.fandom.com/api.php?action=parse&page=List_of_wonders_in_Civ6&prop=wikitext&format=json" | python3 -c "import json,sys;print(json.load(sys.stdin)['parse']['wikitext']['*'])" > wonders.txt
curl -s "https://civilization.fandom.com/api.php?action=parse&page=List_of_natural_wonders_in_Civ6&prop=wikitext&format=json" | python3 -c "import json,sys;print(json.load(sys.stdin)['parse']['wikitext']['*'])" > naturals.txt
python3 parse.py wonders.txt naturals.txt parsed.json
python3 build.py parsed.json world.json natural.json .cache ../data.js
python3 civ_build.py civs.json .cache ../civs.js
```

## Credits

- Game data and wonder art come from the [Civilization Wiki](https://civilization.fandom.com). *Civilization VI* © Firaxis Games / 2K. This is an unofficial fan project.
- Photos come from [Wikimedia Commons](https://commons.wikimedia.org). Each photo's author and licence appear in the photo viewer.
- Map tiles: © Esri and contributors, © OpenStreetMap contributors, © CARTO.
- Built with [Leaflet](https://leafletjs.com).
