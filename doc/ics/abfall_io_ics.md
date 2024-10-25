# Abfall IO ICS Version

Abfall IO ICS Version is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.

Support for multiple service provider using the AbfallPlus API.

## How to get the configuration arguments

- Go to your regions collection dates form.
- Select you location and your desired waste types.
- Right click -> copy link address of the `ICS` button.
- Replace the `url` in the example configuration with this link.
- Replace the year in the URL with `{%Y}` (`...timeperiod=20240101-20241231` -> `...timeperiod={%Y}0101-{%Y}1231`).

## Examples

### Göppingen

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://api.abfall.io/?key=f35bd08b1d18d9c81fcdee75dbcce5d3&mode=export&idhousenumber=2859&wastetypes=20,17,59,18,19,60&timeperiod={%Y}0101-{%Y}1231&showinactive=false&type=ics
```
