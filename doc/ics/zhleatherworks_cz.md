# Lysá nad Labem

Lysá nad Labem is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Open <https://www.zhleatherworks.cz/waste_calendar/> and use the "Filtr Lokace" field to get the location.
- Click on "Zkopírovat URL ICS souboru do schránky". The ICS calendar URL will be copied.
- Use the URL from the clipboard as the `url` parameter.

## Examples

### Sojovicka

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.zhleatherworks.cz/calendars/Sojovick%C3%A1.ics
```
### Bozeny_Nemcove

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.zhleatherworks.cz/calendars/Bo%C5%BEeny%20N%C4%9Bmcov%C3%A9.ics
```
