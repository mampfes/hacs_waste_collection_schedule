# Geminfo.app

Geminfo.app is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://geminfo.app> and select your municipality.
- In the search field "Deine Gemeinde oder Stadt suchen" put in the name of your municipality and select it from the list.
- Click on the "Termine (Kalender, Veranstaltungen)" button.
- On the left side, select the types of waste you want to include in your calendar (Abfallkalender, Altstoffsammelzentrum, Biomüll, Restmüll, Gelber Sack).
- On the top right, right-click on the button "als iCal herunterladen" and copy link address.
- Replace the `url` in the example configuration with this link.

## Examples

### Thannhausen

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://graphql.sta.io/feed/c/i/5d9d1c1a5ff20a142ec8edc9/appointments.ics
```
