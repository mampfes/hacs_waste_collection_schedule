# City of Darebin

Support for schedules provided by [City of Darebin](https://www.darebin.vic.gov.au/Waste-environment-and-climate/Bins-and-waste-collection/When-is-my-bin-collection-day).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: darebin_vic_gov_au
      args:
        property_location: PROPERTY_LOCATION

```

### Configuration Variables

**property_location**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: darebin_vic_gov_au
      args:
        property_location: 274 Gower Street PRESTON 3072
```

## How to get the source arguments

Visit the [City of Darebin Find my bin collection day page](https://darebin.maps.arcgis.com/apps/instant/basic/index.html?appid=51d4de7339f84dd5a6d2790cb2081be2) page and search for your address. The safest value is the Address shown in the Property Information panel, for example `266 Gower Street PRESTON 3072`.

Common variations are accepted as well: commas, a trailing `VIC`/`VICTORIA` and abbreviated street types (`St`, `Rd`, `Ave`, ...) are rewritten to the form the council's address register holds, and a missing or slightly wrong suburb/postcode is retried with a shorter prefix. If several properties match, the error message lists the matching addresses so you can copy the right one.
