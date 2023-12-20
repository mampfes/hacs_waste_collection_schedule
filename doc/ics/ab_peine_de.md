# Landkreis Peine

Landkreis Peine is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.ab-peine.de/Abfuhrtermine/> and select your address. You can leave `Ab Monat` and `Darstellung` as is.
- For all bin types leave all bin types **unselected**  
- Copy the link of the `Kalender abonnieren` button
- Replace the `url` in the example configuration with this link.

## Examples

### Barbecke

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: webcal://www.ab-peine.de/output/options.php?ModID=48&call=webcal&&pois=3660.301
```
### Peine Gerhart-Hauptmann-Straße

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: webcal://www.ab-peine.de/output/options.php?ModID=48&call=webcal&&pois=3660.166
```
