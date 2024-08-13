# GDA Amstetten

GDA Amstetten is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://gda.gv.at/abholtermine> and select your location.  
- Copy the link of the `iCal` Button.
- Replace the `url` in the example configuration with this link.

## Examples

### Markt 47, 3365 Allhartsberg

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://gda.abfuhrtermine.at/webcalzip/Markt/47/3365/03171/30501
```
### Schlossstraße 2, 3311 Zeillern

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://gda.abfuhrtermine.at/webcalzip/Schlossstra%C3%9Fe/2/3311/03349/30544
```
