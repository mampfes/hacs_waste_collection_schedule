# Wirral Council

Support for schedules provided by [Wirral Council](https://wirral.gov.uk/), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wirral_gov_uk
      args:
        street: STREET
        suburb: SUBURB
```

### Configuration Variables

**street**  
*(string) (required)*

**suburb**  
*(string) (required)*

Both the street and suburb are should be supplied in the arguments, as they appear on the web site when viewing your schedule.

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: wirral_gov_uk
      args:
        street: "Beckenham Road"
        suburb: "New Brighton"
```