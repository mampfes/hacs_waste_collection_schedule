# Brandenburg an der Havel

Brandenburg an der Havel is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.stadt-brandenburg.de/leben/abfall-und-abwasser/entsorgungstermine> and select your street
- Right-click on the `Kalenderimport` button and copy the url
- Use this link as the `url` parameter

## Examples

### Akazienweg\

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://brandenburg.abfall-app.net/download?system=ical&period=1&street=4&categories=&view=month
```
