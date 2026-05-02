# Gossau ZH

Gossau ZH is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

Use the URL below. All areas of Gossau ZH are included in a single calendar.
Use the `types` filter in your sensor configuration to show only your area
(e.g. "Kehricht und Sperrgut (Gossau-Dorf, Grüt, Ober-Ottikon, Hellberg)").

## Examples

### Gossau ZH

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.gossau-zh.ch/evt-kategorie/entsorgungskalender/?ical=1
```
