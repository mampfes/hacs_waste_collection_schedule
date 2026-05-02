# Entsorgungsbetrieb Märkisch-Oderland

Entsorgungsbetrieb Märkisch-Oderland is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.entsorgungsbetrieb-mol.de/de/tourenplan-2024.html> and select your location.  
- copy the link of the `ICS` button.
- Use this link as the `url` parameter.
- Replace the year in the url with `{%Y}` (as shown in the example).

## Examples

### Buckow, Hasenholz

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://api.abfall.io/?key=efb75cbd1f08fae1d4e47ae72a85c655&mode=export&idhousenumber=7701&wastetypes=18,2139,20,2639,295,42,1480&timeperiod={%Y}0101-{%Y}1231&showinactive=false&type=ics
```
