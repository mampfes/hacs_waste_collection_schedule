# EDG Entsorgung Dortmund

EDG Entsorgung Dortmund is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.edg.de/de/entsorgungsdienstleistungen/rein-damit/abfallkalender/abfallkalender.htm> and select your location and press `weiter`.  
- Click on `URL in die Zwischenablage kopieren` to copy the ical url.
- Replace the `url` in the example configuration with this link.
- Leave the `regex` untouched
- You can use the different types as `Bioabfall`, `Altpapier`, `Restabfall` and `Wertstoffe`

## Examples

### Baackweg 1

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: ^(\w*) \d* .*
        url: https://kundenportal.edg.de/WasteManagementDortmund/WasteManagementServiceServlet?ApplicationName=Calendar&SubmitAction=sync&StandortID=1271001001&AboID=66930&Fra=P;R;B;W
```
