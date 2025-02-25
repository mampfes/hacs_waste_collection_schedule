# Alzey-Worms

Alzey-Worms is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit <https://www.kreis-alzey-worms.de/aktuelles/nichts-mehr-verpassen/abfalltermine/> and select your location.  
- Click on `URL anzeigen` to see the ICS link.
- Use this url for the `url` parameter.
- You might want to add regex `(.*) \d+ \d+-wöchentl\.` parameter to remove the size and frequency of collections (e.g. `Restmüll 240 02-wöchentl.` -> `Restmüll`).

## Examples

### Alzeyer Pforte 1, 55234 Albig

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: "(.*) \\d+ \\d+-w\xF6chentl\\."
        url: https://abfall.alzey-worms.de/WasteManagementAlzeyworms/WasteManagementServiceServlet?ApplicationName=Calendar&SubmitAction=sync&StandortID=1053576001&AboID=313121&Fra=P;R;B;S;C;L&ObjektID=1145306001
```
