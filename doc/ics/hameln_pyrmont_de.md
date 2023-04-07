# Landkreis Hameln-Pyrmont

Landkreis Hameln-Pyrmont is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://kaw.hameln-pyrmont.de/Service/Abfuhrterminmodul/Abfuhrterminkalender/> and select your location.  
- Click on `URL in die Zwischenablage kopieren` to copy link address.
- Replace the `url` in the example configuration with this link.

## Examples

### Ahorn 1, 31855 Aerzen

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: webcal://om.kaw-hameln.de/WasteManagementHameln/WasteManagementServiceServlet?ApplicationName=Calendar&SubmitAction=sync&StandortID=26881528001&AboID=355061&Fra=P;C4;R;B;S;V;G;M;C1;C2
```
