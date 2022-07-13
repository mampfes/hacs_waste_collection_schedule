# Melton City Council

Support for schedules provided by [Melton City Council](https://www.melton.vic.gov.au/My-Area). This implementation is heavily based upon the Stonnington City Council parser, as both interfaces appear to use the same back-end.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: melton_vic_gov_au
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
    - name: melton_vic_gov_au
      args:
        street_address: 23 PILBARA AVENUE BURNSIDE 3023
```

```yaml
waste_collection_schedule:
  sources:
    - name: melton_vic_gov_au
      args:
        geolocation_id: 00faf1f7-9aa0-4b2c-a9b9-54c29401e68c
```

## How to get the source arguments

Visit the [Melton City Council My Area](https://www.melton.vic.gov.au/My-Area) page and search for your address. The ```street_address``` argument should exactly match the street address shown in the autocomplete result. For unlisted addresses use an adjacent listed address.

The ```geolocation_id``` argument can be used to bypass the initial address lookup on first use. This value can be discovered using the developer console in any modern browser and inspecting the request sent once an address is selected and the search button is clicked. The request URL takes the format: ```https://www.melton.vic.gov.au/ocapi/Public/myarea/wasteservices?geolocationid=<GEOLOCATION ID>&ocsvclang=en-AU```.
