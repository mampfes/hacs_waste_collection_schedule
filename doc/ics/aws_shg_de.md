# Abfallwirtschaftsgesellschaft Landkreis Schaumburg

Abfallwirtschaftsgesellschaft Landkreis Schaumburg is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://aws-shg.de/WasteManagementSchaumburg.html?action=wasteDisposalServices> and select your location.  
- Under `ical-Kalenderabo`, click on `URL in die Zwischenablage kopieren` to copy the link address.
- Replace the `url` in the example configuration with this link.

## Examples

### Am Loh 1, 31559 Haste

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://kundenlogin.aws-shg.de/WasteManagementSchaumburg/WasteManagementServiceServlet?ApplicationName=Calendar&SubmitAction=sync&StandortID=367980001&AboID=201645&Fra=R;B;P;V;S
```
