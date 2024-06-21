# AWG Bassum

AWG Bassum is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.awg-bassum.de/abfuhrkalender.html>
- Click on "Ort wählen" and choose your location
- Type in your street adddress in "Ihre Straße"
- Click on the name of your street
- Scroll down and copy the link of "iCal herunterladen".

## Examples

### Bassum / Alte Poststraße

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.awg-bassum.de/abfuhrkalender.html?year=2024&city=Bassum&street=Alte%20Poststr.&slug=Alte%20Poststr.------Bassum--27211--Bassum&ical=1
```
