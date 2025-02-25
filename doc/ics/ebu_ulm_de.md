# ULM (EBU)

ULM (EBU) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.ebu-ulm.de/abfall/abfuhrtermine.php> and select your location.  
- Scroll down and copy the link of the `ICS Kalenderdaten für Outlook / iCal...` button.
- Replace the `url` in the example configuration with this link.
- Replcae the year with `{%Y}` to keep the link valid for following years.

## Examples

### bezirk 4 (Hauptbahnhof)

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.ebu-ulm.de/export.php?bezirk=4&jahr={%Y}
```
