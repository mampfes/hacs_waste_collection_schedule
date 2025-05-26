# Recology San Francisco

Recology San Francisco is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.recology.com/recology-san-francisco/collection-calendar/>
- Enter your home address in the search field and click "Search"
- Click on "ADD TO MY CALENDAR" and select "iCal"
- Right-click on the iCal link and copy the link address
- Replace the `url` in the example configuration with this link

## Examples

### 835 Florida St San Francisco

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: webcal://recollect-us.global.ssl.fastly.net/api/places/F8DA6588-B076-11E8-BA4B-30AA635824F2/services/265/events.en-US.ics?client_id=79B7D646-3A76-11F0-91E0-BB51B3DF21C3
```
