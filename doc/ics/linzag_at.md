# Linz AG

Linz AG is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.linzag.at/portal/de/privatkunden/zuhause/abfall/service_dienstleistungen/abfallkalender> and select your location.  
- Click on the download `Abfallkalender (ICS)` button and copy the download link or copy the link of the button after you already pressed it (href changes after first click).
- Replace the `url` in the example configuration with this link.
- Replace the date in the url (after `downloadStartDate=`) with `01-01-{%Y}` this way the link keep valid for following years.

## Examples

### Freistädter Straße 9, 4040 Linz

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://services.linzag.at/abfall-rest/icalCalendar?reminderTime=19&address=Freist%C3%A4dter%20Stra%C3%9Fe%209,%204040%20Linz&addressId=12170&isBusinessApp=false&PAP=02&BIO=&LVP=02&RMU=21&downloadStartDate=01-01-{%Y}
```
