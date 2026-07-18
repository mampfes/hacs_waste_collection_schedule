# Stadt Tengen

Stadt Tengen is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.tengen.de/service+_+rathaus/buergerservice/abfallentsorgung/abfallkalender>.
- Click on `Alle Termine des Abfallkalenders in meinen Kalender (z. B. Outlook) übernehmen (.ics-Datei)` and copy the link.
- Use this link as the `url` parameter. This feed already covers the whole municipality (Tengen and Wiechs a.R.) and does not require an address.

## Examples

### Tengen

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.tengen.de/site/Tengen/zmservice/2266403/ical/vevent.ics
```
