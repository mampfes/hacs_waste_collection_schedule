# Logan City Council

Support for schedules provided by [Logan City Council](https://www.logan.qld.gov.au/waste/bin-collection-day).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: logan_qld_gov_au
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
    - name: brisbane_qld_gov_au
      args:
        property_location: 150 Wembley Rd, Logan Central QLD 4114
```

## How to get the source arguments

Visit the [Logan City Council My Property Tool](https://az-prod-wa02.azurewebsites.net/) page and search for your address.  The argument should exactly match the result shown for Address portion of the Property Information with an additional comma after the street name. 