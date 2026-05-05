# FES Frankfurter Entsorgungs- und Service GmbH

FES Frankfurter Entsorgungs- und Service GmbH is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://frankfurtplus.de/abfallkalender> and search for your address.
- Select your street and house number.
- Note the `address_id` number from the URL (e.g. `https://frankfurtplus.de/abfallkalender?address_id=69882`).
- Use the ICS URL format: `https://frankfurtplus.de/abfallkalender/ADDRESS_ID/ical`

## Examples

### Ludwig-Ruppel-Str. 89

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: '[^:]+:\s*(.*)'
        url: https://frankfurtplus.de/abfallkalender/69882/ical
```
