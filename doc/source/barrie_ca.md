# City of Barrie

Support for schedules provided by [City of Barrie](https://www.barrie.ca/services-payments/garbage-recycling-organics/curbside-collection/collection-schedules), Ontario, Canada.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: barrie_ca
      args:
        street_number: STREET_NUMBER
        street_name: STREET_NAME
```

### Configuration Variables

**street_number**
*(string) (required)*

**street_name**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: barrie_ca
      args:
        street_number: "47"
        street_name: Quance St
```

## How to get the source arguments

Enter your street number and street name as shown on the [Barrie collection schedule page](https://www.barrie.ca/services-payments/garbage-recycling-organics/curbside-collection/collection-schedules). Abbreviate street suffixes (e.g. "St" not "Street", "Ave" not "Avenue").
