# Westmorland & Furness Council, South Lakeland area

Westmorland & Furness Council, South Lakeland area is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.southlakeland.gov.uk/bins-and-recycling/collection-calendar/> and select your location.  
- Rightclick -> copy the URL of the `Import these dates into your calendar` link.
- Replace the `url` in the example configuration with this link.

## Examples

### 8, Cliff Terrace, Kendal, LA9 4JR

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.southlakeland.gov.uk/Umbraco/Api/iCalRecycling/Get/?siteid=48750
```
