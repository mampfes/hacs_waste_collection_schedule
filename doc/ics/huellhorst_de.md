# Gemeinde Hüllhorst

Gemeinde Hüllhorst is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

The village community "Dorfgemeinschaft für ein zukunftsorientiertes Büttendorf" publishes
the waste collection calendar of the whole municipality of Hüllhorst as an ICS file every year.

- Go to <https://www.buettendorf.info/abfuhrkalender/>.
- Right-click -> copy link address on one of the `Download` buttons
  (`Abfuhrkalender <year> mit Erinnerung` includes a reminder at 18:00 the day before,
  `Abfuhrkalender <year> ohne Erinnerung` does not).
- Use this link as the `url` parameter.
- Note: a new link is published every year, so you will need to revisit the page
  and update the `url` parameter once the current year's calendar is no longer valid.

## Examples

### Abfuhrkalender ohne Erinnerung

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.buettendorf.info/app/download/13461722949/Abfuhrkalender+2026+ohne+Erinnerung.ics?t=1772087961
```
