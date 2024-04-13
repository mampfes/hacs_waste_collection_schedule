# Landkreis Heidenheim

Landkreis Heidenheim is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.abfall-hdh.de/internet/inhalt/inhalt.php?seite=98> and select your location.  
- Replace the `gemeinde`, `ortsteil` and `strasse` in the example configuration with the names you selected (leave `strasse` as is if you do not selected one on the website).
- You may also want to set the `bio`, `garten`, `gs`, `rest`, `papier` and `papiertonne` parameters to `"0"` if you do not want to see the corresponding waste types in the calendar.

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
