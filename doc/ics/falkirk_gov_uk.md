# Falkirk

Falkirk is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.falkirk.gov.uk/services/bins-rubbish-recycling/household-waste/bin-collection-dates.aspx> and select your location.  
- Click on `Add to smartphone`.
- select Android and uncheck Remind me.
- Replace the `url` in the example configuration with the link shown in the bar below `Remind me`.

## Examples

### 23, WEIR STREET, FALKIRK, FK1 1RB

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: webcal://www.falkirk.gov.uk/bin-ical?uprn=136028227
```
