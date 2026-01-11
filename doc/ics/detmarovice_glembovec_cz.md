# Dětmarovice (part Glembovec)

Dětmarovice (part Glembovec) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- village Dětmarovice does not support any solution for the source calendar data in ICS format
- the data was "generated" from the local paper calendar :-)

## Examples

### Glembovec

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://raw.githubusercontent.com/aleswita/home-assistant/refs/heads/master/waste/detmarovice_glembovec.ics
```
