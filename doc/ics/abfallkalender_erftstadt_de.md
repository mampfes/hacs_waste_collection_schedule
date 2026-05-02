# Erftstadt (inoffical)

Erftstadt (inoffical) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://abfallkalender-erftstadt.de/> and select your location.
- Click on `Zum Kalender hinzufügen`.
- Click on `weiter` without selecting reminder.
- Copy the link below `Für Google Kalender` or copy the link from the `Abonnieren` or `Download` button.
- Use this link as the `url` parameter.
- Keeping the `regex` as it is, will remove the district name from the event title.

## Examples

### Borr

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: (.*) - Bezirk \d
        url: https://abfallkalender-erftstadt.de/download/bezirk_5.ics
```
### Frauental

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: (.*) - Bezirk \d
        url: webcal://abfallkalender-erftstadt.de/download/bezirk_2.ics
```
