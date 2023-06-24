# Trondheim

Trondheim is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://trv.no/plan/> and search for your address.  
- Copy the link address of `Legg til i kalender (iCal)` to get a webcal link.
- Replace the `url` in the example configuration with this link.

## Examples

### Asalvegen 1A

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: webcal://trv.no/calendar/002cac88-e10d-4138-b4d6-d3494d892f4b
```
