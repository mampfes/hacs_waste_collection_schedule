# Landkreis Northeim (unofficial)

Landkreis Northeim (unofficial) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.

This is an unofficial service provided by nerdbridge Einbeck!

## How to get the configuration arguments

- Goto <https://abfall.nerdbridge.de/> and select your municipality.  
- Click on `In die Zwischenablage kopieren` and to copy the link address.
- Replace the `url` in the example configuration with this link.

## Examples

### Einbeck (Bezirk 2)

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://abfall.nerdbridge.de/ical/abfall-nom-einbeck_bezirk_2-HM2W,HM4W,PET,BIO,PAP,GL.ics
```
