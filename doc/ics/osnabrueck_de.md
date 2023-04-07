# Stadt Osnabrück

Stadt Osnabrück is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://nachhaltig.osnabrueck.de/de/abfall/muellabfuhr/muellabfuhr-digital/online-abfuhrkalender/> and select your location.  
- Right-click on `Termine importieren` and copy link address.
- Replace the `url` in the example configuration with this link.

## Examples

### Alte Landebahn 17

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: OSB (.*)
        url: https://geo.osnabrueck.de/osb-service/abfuhrkalender/?bezirk=2
```
