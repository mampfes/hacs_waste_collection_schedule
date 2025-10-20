# North Tyneside Council

North Tyneside Council is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.northtyneside.gov.uk/waste-collection-schedule> and search your address.  
- Copy the link from `Add to iCalendar`
- Replace the `url` in the example configuration with this link.

## Examples

### uprn_47098397_waste

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.northtyneside.gov.uk/waste-collection-schedule/download/47098397
```
