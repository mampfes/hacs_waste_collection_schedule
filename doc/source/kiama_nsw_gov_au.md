# Kiama Municipal Council

Support for schedules provided by [Kiama Municipal council](https://www.kiama.nsw.gov.au/), serving Kiama Municipality, New South Wales, Australia

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: kiama_nsw_gov_au
      args:
        geolocationid: GUID
```

### Configuration Variables

**geolocationid**  
*(string) (mandatory)*

### How to find your geolocationid

Go to <https://www.kiama.nsw.gov.au/Services/Waste-and-recycling/Find-my-bin-collection-dates>
Open the developer tools (F12), Go to the Network tab
Put in your address, and click Search.

Look for a network call to the wasteservices endpoint, it will have geolocationid=<GUID>
This GUID is what you need, it is unique to your service address.


## Example

```yaml
waste_collection_schedule:
  sources:
  - name: kiama_nsw_gov_au
    args:
      geolocationid: f2c04fcf-e3d3-424e-aa90-1d365bbf0130
```
