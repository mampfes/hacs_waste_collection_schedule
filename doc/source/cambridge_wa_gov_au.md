# Town of Cambridge (WA)

Support for schedules provided by [Town of Cambridge](https://www.cambridge.wa.gov.au/), serving Western Australian suburbs including Floreat, Wembley, City Beach, West Leederville and Mount Claremont. The implementation uses the same OpenCities (OCAPI) back-end pattern as other Australian council sources.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cambridge_wa_gov_au
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**
*(string) (optional)*

**geolocation_id**
*(string) (optional)*

At least one argument must be provided.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cambridge_wa_gov_au
      args:
        street_address: 99 The Boulevard, FLOREAT 6014
```

```yaml
waste_collection_schedule:
  sources:
    - name: cambridge_wa_gov_au
      args:
        geolocation_id: ec16b372-7aab-4082-8519-2163c431777d
```

## How to get the source arguments

Visit the [Town of Cambridge Find My Bin Day](https://www.cambridge.wa.gov.au/Residents/Waste-Recycling/Find-My-Bin-Day) page and search for your address. The ```street_address``` argument should exactly match the street address shown in the autocomplete result. For unlisted addresses use an adjacent listed address.

The ```geolocation_id``` argument can be used to bypass the initial address lookup on first use. This value can be discovered using the developer console in any modern browser and inspecting the request sent once an address is selected and the search button is clicked. The request URL takes the format: ```https://www.cambridge.wa.gov.au/ocapi/Public/myarea/wasteservices?geolocationid=<GEOLOCATION ID>&ocsvclang=en-AU```.
