# Litovel

Litovel is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://svoz.litovle.cz/> and using field "Filtr Lokace" filter desired location.
- Click on "Zkopírovat URL ICS souboru do schránky". The URL to ICS calendar will be copied to clipboard.
- Replace the `url` in the example configuration with link from the clipboard.

## Examples

### Olomoucka

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://svoz.litovle.cz/calendars/Olomouck%C3%A1.ics
```
### Vitezna_sidliste

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://svoz.litovle.cz/calendars/V%C3%ADt%C4%9Bzn%C3%A1%20-%20s%C3%ADdli%C5%A1t%C4%9B.ics
```
