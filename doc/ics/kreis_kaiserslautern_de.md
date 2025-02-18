# Landkreis Kaiserslautern

Landkreis Kaiserslautern is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://abfallapp.softwareentwicklung-roth.de/web/KL/en/kalender>.
- Select your city, street, and waste types.
- Right-click on the `Download as iCalendar` button and copy the link.
- Replace the `url` in the example configuration with this link.
- Replace the year in the url by {%Y}.

## Examples

### Ramstein

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://abfallapp.softwareentwicklung-roth.de/{%Y}/KL/Ramstein/Rathausring/ics/de?abfallart_Restmuell=on&abfallart_GelberSack=on&abfallart_Biomuell=on&abfallart_Papier=on
```
