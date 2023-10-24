# Zweckverband Abfallwirtschaft Südwestsachsen (ZAS)

Zweckverband Abfallwirtschaft Südwestsachsen (ZAS) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.za-sws.de/abfallkalender.cfm?ab=1> and select your location.  
- Click on `URL in die Zwischenablage kopieren` to copy the link to the ICS file.
- Replace the `url` in the example configuration with this link.

## Examples

### Gornsdorf, August-Bebel Strasse 23

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://online-portal.za-sws.de/WasteManagementSuedwestsachsen/WasteManagementServiceServlet?ApplicationName=Calendar&SubmitAction=sync&StandortID=16459903001&AboID=80078&Fra=P;R;B;C;S;W;L
        verify_ssl: false
```
