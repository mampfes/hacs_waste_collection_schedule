# Abfallwirtschaftsbetrieb Landkreis Karlsruhe

Abfallwirtschaftsbetrieb Landkreis Karlsruhe is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.awb-landkreis-karlsruhe.de/start/wissen/abfuhrkalender.html> and select your location.  
- Click on `URL in die Zwischenablage kopieren` to copy link address.
- Replace the `url` in the example configuration with this link.

## Examples

### Adlerstr. 1, 76694 Forst

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://waste.awb-landkreis-karlsruhe.de/WasteManagementKarlsruheHaushalteBlank/WasteManagementServiceServlet?ApplicationName=Calendar&SubmitAction=sync&StandortID=717948001&AboID=60498&Fra=RC2;RC1;BT2;BC;RT;Schad;WC;WT;BT1
```
