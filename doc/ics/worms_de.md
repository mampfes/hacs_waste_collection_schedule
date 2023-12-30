# ebwo - Entsorgungs- und Baubetrieb Anstalt des öffentlichen Rechts der Stadt Worms

ebwo - Entsorgungs- und Baubetrieb Anstalt des öffentlichen Rechts der Stadt Worms is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.worms.de/de/web/ebwo/abfallkalender/{%Y}/> and select your street.
- Search for your street and click on the street name.
- Right click on the 'Export-Datei (.ics) herunterladen' button and select 'Copy link address'.
- Replace the `url` in the example configuration with this link.

## Examples

### Ahornweg

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.worms.de/de/web/ebwo/abfallkalender/{%Y}/ical.php?id=4ca5c7e9a80af5540.93039563
```
### Marktplatz

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.worms.de/de/web/ebwo/abfallkalender/{%Y}/ical.php?id=4ca5c7e9a80e1b805.42577576
```
