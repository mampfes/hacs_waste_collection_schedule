# Banyule City Council

Support for schedules provided by [Banyule City Council](https://www.banyule.vic.gov.au/binday). This implementation is heavily based upon the Stonnington City Council parser, as both interfaces appear to use the same back-end.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: banyule_vic_gov_au
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**<br>
*(string) (optional)*

**geolocation_id**<br>
*(string) (optional)*

At least one argument must be provided.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: banyule_vic_gov_au
      args:
        street_address: 6 Mandall Avenue, IVANHOE
```

```yaml
waste_collection_schedule:
  sources:
    - name: banyule_vic_gov_au
      args:
        geolocation_id: 4f7ebfca-1526-4363-8b87-df3103a10a87
```

## How to get the source arguments

Visit the [Banyule City Council bin collection services](https://www.banyule.vic.gov.au/Waste-environment/Waste-recycling/Bin-collection-services) page and search for your address. The ```street_address``` argument should exactly match the street address shown in the autocomplete result. For unlisted addresses use an adjacent listed address.

The ```geolocation_id``` argument can be used to bypass the initial address lookup on first use. This value can be discovered using the developer console in any modern browser and inspecting the request sent once an address is selected and the search button is clicked. The request URL takes the format: ```https://www.banyule.vic.gov.au/ocapi/Public/myarea/wasteservices?geolocationid=<GEOLOCATION ID>&ocsvclang=en-AU```.
