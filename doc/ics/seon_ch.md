# Seon

Seon is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.seon.ch/verwaltung/dienstleistungen.html/21/service/370>
- Click on `Entsorgungskalender Google` to get a ical link. If the button is broken use the `URL in Zwichenablage kopieren` button.
- Replace the `url` in the example configuration with this link.

## Examples

### Oberdorfstrasse 11, 5703 Seon

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.seon.ch/public/upload/assets/7330/Entsorgungskalender_Outlook%202025.ics?fp=1
```
