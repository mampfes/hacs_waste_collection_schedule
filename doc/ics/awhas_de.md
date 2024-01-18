# Abfallwirtschaft Landkreis Haßberg

Abfallwirtschaft Landkreis Haßberg is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.

## How to get the configuration arguments

- Goto <https://awido.cubefour.de/customer/awhas/mobile/>.
- Select your Location and Garbage Types
- Click on "Termine und Daten laden"
- Select "Mehr" bottom left.
- Select "Erinnerungen beantragen"
- Select "weiter ..."
- Copy the Link from the Button "Termine als iCalendar".
- Replace the `url` in the example configuration with this link.

## Examples

### AWHAS

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://awido.cubefour.de//Customer/awhas/KalenderICS.aspx?oid=99945703-4fb1-4949-a6d2-19d9f2deba13&jahr=2024&reminder=-1.21:00&fraktionen=1,2,3,4,11
```
