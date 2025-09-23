# Northumberland County Council

Support for schedules provided by [Northumberland County Council](https://www.northumberland.gov.uk/bins-recycling-waste/bin-collections-residents), serving Northumberland, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: northumberland_gov_uk
      args:
        postcode: POSTCODE
```

### Configuration Variables
**postcode**
*(string) (required)*

Your postcode, e.g., NE19 1AA

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: northumberland_gov_uk
      args:
        postcode: "NE19 1AA"
```

## How to find your postcode

Simply use your postal code. You can verify it works by visiting the [Northumberland County Council bin collection checker](https://bincollection.northumberland.gov.uk/) and entering your postcode.