# Abfallwirtschaft Rems-Murr (AWRM) - ICS Version

Abfallwirtschaft Rems-Murr (AWRM) - ICS Version is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.abfallwirtschaft-rems-murr.de/muell-entsorgen/ihr-abfallkalender> and select your town, street name and number.
- Select the waste types that should be included in the waste calendar.
- You can ignore the year selection, if present. Click `Weiter`.
- In the `ical-Kalenderabo` section, show and copy the URL or press `URL in die Zwischenablage kopieren`.
- Replace the `url` in the example configuration with this link.

## Examples

### Oppach

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www2.awrm.de/WasteManagementRemsmurr/WasteManagementServiceServlet?ApplicationName=Calendar&SubmitAction=sync&StandortID=948227001&AboID=219299&Fra=Gelb;Papier;Bio;RestTonne2wo
```
