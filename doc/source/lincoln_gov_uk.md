# City Of Lincoln Council

Support for schedules provided by [City Of Lincoln Council](https://www.lincoln.gov.uk/).

Source for City Of Lincoln Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lincoln_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

### Configuration Variables

**postcode**  
*(string) (required)*

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: lincoln_gov_uk
      args:
        postcode: LN5 7SH
        uprn: 000235024846
```
