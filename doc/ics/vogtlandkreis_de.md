# Landkreis Vogtland

Landkreis Vogtland is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://vogtlandkreis.de/Bürgerservice-und-Verwaltung/Infos-und-Services/Abfallentsorgung/Abfuhrtermine> and select your location.  
- Click on `URL ANZEIGEN` to get a ical link. If the button is broken use the `URL in Zwichenablage kopieren` button.
- Replace the `url` in the example configuration with this link.

## Examples

### Bergen, Am Anger 3a

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://awi.vogtlandkreis.de/WasteManagementVogtland/WasteManagementServiceServlet?ApplicationName=Calendar&SubmitAction=sync&StandortID=1017029001&AboID=217980&Fra=R2;P;P1;B;G;R1https://awi.vogtlandkreis.de/WasteManagementVogtland/WasteManagementServiceServlet?ApplicationName=Calendar&SubmitAction=sync&StandortID=1017786001&AboID=217979&Fra=R2;P;P1;B;G;R1
```
