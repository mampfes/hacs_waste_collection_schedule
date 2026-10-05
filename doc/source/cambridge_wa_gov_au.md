# Town of Cambridge (WA)

Support for schedules provided by [Town of Cambridge (WA)](https://www.cambridge.wa.gov.au).

Source for Town of Cambridge (Western Australia) rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cambridge_wa_gov_au
      args:
        street_address: STREET_ADDRESS
        geolocation_id: GEOLOCATION_ID
```

### Configuration Variables

**street_address**  
*(string) (optional)*

**geolocation_id**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cambridge_wa_gov_au
      args:
        geolocation_id: c70848c4-fe33-431d-85aa-987ff8b155cb
```

## How to get the source arguments

Visit the [Town of Cambridge Find My Bin Day](https://www.cambridge.wa.gov.au/Residents/Waste-Recycling/Find-My-Bin-Day) page and search for your address. The street address should exactly match the address shown in the autocomplete result. For unlisted addresses use an adjacent listed address. Alternatively give the Location ID, the council's geolocation ID. It skips the address lookup and takes precedence when both are given. To find it, open your browser's developer tools (F12, Network tab), select your address on the page above and look for the request `https://www.cambridge.wa.gov.au/ocapi/Public/myarea/wasteservices?geolocationid=<ID>&ocsvclang=en-AU`. The value after `geolocationid=` is your Location ID.
