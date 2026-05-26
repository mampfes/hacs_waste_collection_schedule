# Odvoz Odpadu

Odvoz Odpadu is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://odvoz-odpadu.eu/> and search for your municipality.
- Copy the link address of the "Google / Apple Kalendár" button (or the ICS icon).
- The URL will look like `https://odvoz-odpadu.eu/miesto/XXXX/kalendar.ics` (where XXXX is your municipality ID).
- Use this URL as the `url` parameter in your Home Assistant configuration.

## Examples

### Dolna_Ves

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://odvoz-odpadu.eu/miesto/1400/kalendar.ics
```
