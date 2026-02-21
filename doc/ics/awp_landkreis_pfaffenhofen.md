# Abfallwirtschaftsbetrieb des Landkreises Pfaffenhofen a.d.Ilm (AWP)

Abfallwirtschaftsbetrieb des Landkreises Pfaffenhofen a.d.Ilm (AWP) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.awp-paf.de/Abfuhrtermine/Abfallkalender.aspx> and select your town.
- Enter your street and house number.
- Click on `ical-Kalenderabo` and `URL in die Zwischenablage kopieren` to get a webcal link.
- Use this link as the `url` parameter.

## Examples

### Raiffeisenstr. 19

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://abfuhrtermine.awp-paf.de/WasteManagementPfaffenhofen/WasteManagementServiceServlet?ApplicationName=Calendar&SubmitAction=sync&StandortID=150372001&AboID=523613&Fra=P;B;S;RM
```
