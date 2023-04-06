# Limburg.net

Limburg.net is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.limburg.net/afvalkalender> and select your location.  
- Click on `Download`.
- Under `Kies formaat`, select `Android/iPhone`.
- Copy the webcal link.
- Replace the `url` in the example configuration with this link.

## Examples

### Bandstraat 11, Bilzen

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: webcal://www.limburg.net/ics/afvalkalender/73006/10998/11/0
```
