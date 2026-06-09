# Landkreis Heidenheim

Landkreis Heidenheim is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.abfall-hdh.de/internet/inhalt/inhalt.php?seite=98> and select your location.
- Most fields are pre-filled. In the **Params** field, add your `gemeinde`, `ortsteil` and `strasse` to the existing JSON, e.g.: `{"gemeinde": "Dischingen", "ortsteil": "Hofen", "strasse": "", "bio": "1", ...}`
- Set `split_at` to `\+` if events contain combined waste types.
- Set waste type toggles (`bio`, `garten`, `gs`, `rest`, `papier`, `papiertonne`) to `"0"` to hide unwanted types.

## Examples

### Dischingen Hofen

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        method: POST
        params:
          bio: '1'
          garten: '1'
          gemeinde: Dischingen
          gs: '1'
          ortsteil: Hofen
          papier: '1'
          papiertonne: '1'
          rest: '1'
          strasse: ''
          tag: '0'
          uhrzeit: ''
        url: https://mobil.abfallwirtschaft-heidenheim.de/icalendar/download.php
        year_field: jahr
```
### Heidenheim, Heidenheim, Hauptstraße

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        method: POST
        params:
          bio: '1'
          garten: '1'
          gemeinde: Heidenheim
          gs: '1'
          ortsteil: Heidenheim
          papier: '1'
          papiertonne: '1'
          rest: '1'
          strasse: "Hauptstra\xDFe"
          tag: '0'
          uhrzeit: ''
        split_at: \+
        url: https://mobil.abfallwirtschaft-heidenheim.de/icalendar/download.php
        year_field: jahr
```
