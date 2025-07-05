# Landkreis Schwäbisch Hall

Support for schedules provided by [Landkreis Schwäbisch Hall](https://www.lrasha.de) located in Baden-Württemberg, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lrasha_de
      args:
        location: "68329"
```

### Configuration Variables

**location**
*(string) (required)*

## How to get the source arguments

Visit [Abfallkalender](https://www.lrasha.de/de/buergerservice/abfallwirtschaft/abfallkalender), select your location and click on import. Now you see a link to import the calendar. The number after `SecondCategoryIds=` has to be entered in the configuration.


You can make a manual API call http://api.cross-7.de/public/calendar/399/events/ics?SecondCategoryIds=68329 and download the ICS file. Open it in a texteditor to view the location. This way you can find your location and the id. Attached is list of some locations and their Ids:
68320 Schwäb. Hall 4
68321 Michelbach/Bilz
68322 Michelfeld
68323 Rosengarten
68324 Fichtenberg
68325 Oberrot
68326 Sulzbach-Laufen
68327 Fichtenau
68328 Frankenhardt
68329 Kreßberg
68330 Crailsheim
68331 Stimpfach
68332 Crailsheim - Bezirk 2
68333 Crailsheim - Bezirk 3
68334 Crailsheim - Bezirk 4
68335 Crailsheim - Bezirk 5
68336 Bühlertann
68337 Bühlerzell
68338 Obersontheim
68339 Schwäb. Hall 3
68340 Vellberg
68341 Braunsbach
68342 Schwäb. Hall 2
68343 Untermünkheim
68344 Wolpertshausen
68345 Ilshofen
68346 Gerabronn
68347 Schrozberg
68348 Schwäb. Hall 5
68349 Blaufelden
68350 Langenburg
68351 Schwäb. Hall 1
68352 Vellberg
68353 Fichtenberg
68354 Blaufelden
