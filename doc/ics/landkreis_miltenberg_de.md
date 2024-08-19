# Landratsamt Miltenberg

Landratsamt Miltenberg is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://sperrgut.landkreis-miltenberg.de/WasteManagementMiltenberg/WasteManagementServlet?SubmitAction=wasteDisposalServices> and select your location.  
- Click on `URL ANZEIGEN` to get a webcal link.
- Replace the `url` in the example configuration with this link.

## Examples

### Am Ullersbach 3, 97903 Collenberg

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://sperrgut.landkreis-miltenberg.de/WasteManagementMiltenberg/WasteManagementServiceServlet?ApplicationName=Calendar&SubmitAction=sync&StandortID=82947985001&AboID=107727&Fra=R2;B2;P1;R4;P2;P4;Gelb;SM;R1;B1
```
