# Banyule City Council

Support for schedules provided by [Banyule City Council](https://www.banyule.vic.gov.au).

Source for Banyule City Council rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: banyule_vic_gov_au
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
    - name: banyule_vic_gov_au
      args:
        street_address: 6 Mandall Avenue, IVANHOE
```

## How to get the source arguments

Visit the [Banyule City Council bin collection services](https://www.banyule.vic.gov.au/Waste-environment/Waste-recycling/Bin-collection-services) page and search for your address. The street address should exactly match the address shown in the autocomplete result. For unlisted addresses use an adjacent listed address. Alternatively give the Location ID, the council's geolocation ID. It skips the address lookup and takes precedence when both are given. To find it, open your browser's developer tools (F12, Network tab), select your address on the page above and look for the request `https://www.banyule.vic.gov.au/ocapi/Public/myarea/wasteservices?geolocationid=<ID>&ocsvclang=en-AU`. The value after `geolocationid=` is your Location ID.
