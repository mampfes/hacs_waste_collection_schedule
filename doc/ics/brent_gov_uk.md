# Brent Council

Brent Council is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://recyclingservices.brent.gov.uk/waste> and enter your post code, and on the following page select your address.  
- Right click -> copy the url of the `Add to your calendar (.ics file)` link.
- Replace the `url` in the example configuration with this link. (If you know your address reference, you can just replace the last part of the url with it.)

## Examples

### 25 Shaftesbury Avenue, Harrow, HA3 0QU

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://recyclingservices.brent.gov.uk/waste/2038877/calendar.ics
```
