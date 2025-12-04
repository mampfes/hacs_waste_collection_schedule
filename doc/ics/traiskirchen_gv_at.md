# Stadtgemeinde Traiskirchen

Stadtgemeinde Traiskirchen is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://traiskirchen.gv.at/abfall-entsorgung/online-abfuhrplan/> and search your address.  
- Copy the link of `Abfuhrbereich...` below `Kalender zum Download als ICS` button.
- Use this link as the `url` parameter.

## Examples

### Abfuhrbereich 5

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://traiskirchen.gv.at/fileadmin/files/download/iCAL-Abfuhrkalender/Abfuhrbereich_5.ics
```
