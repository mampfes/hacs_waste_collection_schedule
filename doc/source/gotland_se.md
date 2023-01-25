# Region Gotland

Support for schedules provided by [Region Gotland](https://edpfuture.gotland.se/), serving the municipality of Gotland, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: region_gotland_se
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: region_gotland_se
      args:
        uprn: 0000000000
```

## How to get the source argument

The source argument is the unique number of your property that has a waste collection service. The number can be obtained by logging in [here](https://edpfuture.gotland.se/FutureWeb/MyServices/SelectBuilding) and checking the "Välj anläggnings" dropdown list.
