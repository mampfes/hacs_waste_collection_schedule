# Dětmarovice (part Glembovec)

Dětmarovice (part Glembovec) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Village Dětmarovice does not provide calendar data in ICS format.
- The data was generated from the local paper calendar.
- Use the `url` from the example below.

## Examples

### Glembovec

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://raw.githubusercontent.com/aleswita/home-assistant/refs/heads/master/waste/detmarovice_glembovec.ics
```
