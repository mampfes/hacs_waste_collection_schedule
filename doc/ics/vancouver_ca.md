# VanCollect

VanCollect is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Goto <https://vancouver.ca/home-property-development/garbage-and-recycling-collection-schedules.aspx> and select your address.  
- Click on `Get a calendar`.
- Click on `Add to iCal`.
- Right click on `Subscribe to Calendar` and copy the link.
- Replace the `url` in the example configuration with this link.

## Examples

### 166 W 47th Ave, Vancouver

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: webcal://recollect.a.ssl.fastly.net/api/places/3734BF46-A9A1-11E2-8B00-43B94144C028/services/193/events.en.ics?client_id=8844492C-9457-11EE-90E3-08A383E66757
```
