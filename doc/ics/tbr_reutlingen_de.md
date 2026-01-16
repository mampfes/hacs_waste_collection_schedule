# Technischer Betriebsdienst Reutlingen

Technischer Betriebsdienst Reutlingen is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Open <https://www.tbr-reutlingen.de/entsorgungskalender> and go to section `Entsorgungskalender 2025`.
- Select your street, desired waste types and timeperiod.
- Right-click on `ICS` and copy link address.
- Use this link as `url` parameter.
- The link contains a query parameter called `timeperiod` which defines the start and end of the selected year. You need to modify the value of it from e.g. `20250101-20251231` to `{%Y}0101-{%Y}1231`.

## Examples

### Reutlingen

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://api.abfall.io/?key=1bf5dd3852fd8c24ec5679c53f678540&mode=export&idhousenumber=658&wastetypes=27,50,66,65,31,3061,169&timeperiod={%Y}0101-{%Y}1231&showinactive=false&type=ics
```
