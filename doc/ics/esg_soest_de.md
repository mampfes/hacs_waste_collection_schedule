# ESG Soest - Entsorgungswirtschaft Soest GmbH

ESG Soest - Entsorgungswirtschaft Soest GmbH is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.esg-soest.de/abfallkalender> and select your location and press `weiter`.
- Enter your street and press `weiter`.
- Right click and copy the link of the `.ics-Datei` button.
- Replace the `url` in the example configuration with this link.

## Examples

### Rathausstraße (Soest)

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.esg-soest.de/abfallkalender/soest/rathausstrasse/herunterladen
```
