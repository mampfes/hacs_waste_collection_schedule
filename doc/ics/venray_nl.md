# Gemeente Venray

Gemeente Venray is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit <https://afvalkalender.venray.nl/wanneer> and select your location.  
- click on the button `Zet in je agenda`.
- Scroll down to "PC of Laptop" and press the `Kopieer naar klembord` button to copy the required URL.
- Replace the `url` in the example configuration with this link.

## Examples

### 5809EH 12

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://afvalkalender.venray.nl/ical/0984200000024569
```
