# Abfallwirtschaft Landkreis Haßberg

Abfallwirtschaft Landkreis Haßberg is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://portal.awhas.de/> and register yourself.
- Configure your location on page `Persönliche Daten`.
- Go back to `Übersicht` and then select `Terminerinnerungen im iCal-Format`.
- Select your desired waste types.
- Click on `Abbonieren`.
- Copy the displayed link.
- Replace the `url` in the example configuration with this link.

## Examples

### AWHAS

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://portal.awhas.de/icalabo.html?key=b1b8d70bb7d1c93f4afbbcca5c57857fcf979511
```
