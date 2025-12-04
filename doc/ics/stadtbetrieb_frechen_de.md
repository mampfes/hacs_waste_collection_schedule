# Stadtbetrieb Frechen

Stadtbetrieb Frechen is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.stadtbetrieb-frechen.de/service/abfallkalender> and select your street name.  
- Right-click on `Jahreskalender importieren (iCal)` and copy link address.
- Use this link as the `url` parameter.
- Replace the year in the url with `{%Y}` this way the link keep valid for following years.

## Examples

### Elisabethstrasse

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.stadtbetrieb-frechen.de/service/abfallkalender/elisabethstrasse-141/{%Y}/ical
```
