# Moreton Bay

Moreton Bay is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://www.moretonbay.qld.gov.au/Services/Waste-Recycling/Collections/Bin-Days> and select your location.  
- Click on `Subscribe to a personalised calendar` to get a webcal link.
- Replace the `url` in the example configuration with this link.

## Examples

### 18 Mainsail Drive, CABOOLTURE SOUTH Queensland 4510

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: webcal://www.moretonbay.qld.gov.au/bincal?externalId=459739
```
