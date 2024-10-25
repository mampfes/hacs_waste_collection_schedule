# Bau- und Entsorgungsbetrieb Emden

Bau- und Entsorgungsbetrieb Emden is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.bee-emden.de/abfall/entsorgungssystem/abfuhrkalender> and search your location or find your `Bezirk`.  
- Right click and copy the link of the `abonnieren` button after your `Bezirk` or address.
- Replace the `url` in the example configuration with this link.

## Examples

### Port Arthur / Transvaal

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        split_at: ','
        url: https://www.bee-emden.de/abfall/entsorgungssystem/abfuhrkalender/ics/port-arthur-transvaal/abfuhrkalender.ics
```
### Larrelt

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        split_at: ','
        url: https://www.bee-emden.de/abfall/entsorgungssystem/abfuhrkalender/ics/larrelt/abfuhrkalender.ics
```
