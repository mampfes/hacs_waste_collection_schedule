# Südbrandenburgischer Abfallzweckverband

Südbrandenburgischer Abfallzweckverband is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.sbazv.de/entsorgungstermine/restmuell-papier-gelbesaecke-laubsaecke-weihnachtsbaeume/>
- Mark all types of waste and enter your address
- Click on "Kalenderexport"
- Click on "URL in die Zwischenablage kopieren"
- Replace the `url` in the example configuration with this link.

## Examples

### Rangsdorf

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        split_at: ' & '
        url: https://fahrzeuge.sbazv.de/WasteManagementSuedbrandenburg/WasteManagementServiceServlet?ApplicationName=Calendar&SubmitAction=sync&StandortID=1369739001&AboID=10760&Fra=P;R;WB;L;GS
```
