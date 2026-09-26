# Kiama City Council

Support for schedules provided by [Kiama City Council](https://kiama.nsw.gov.au).

Source script for kiama.nsw.gov.au

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kiama_nsw_gov_au
      args:
        geolocationid: GEOLOCATIONID
```

### Configuration Variables

**geolocationid**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kiama_nsw_gov_au
      args:
        geolocationid: 3e54d9b4-e0b8-41cf-8518-d48c1cc5407b
```

## How to get the source arguments

Go to <https://www.kiama.nsw.gov.au/Services/Waste-and-recycling/Find-my-bin-collection-dates>
Open the developer tools (F12), Go to the Network tab
Put in your address, and click Search.

Look for a network call to the wasteservices endpoint, it will have geolocationid=<GUID>
This GUID is what you need, it is unique to your service address.
