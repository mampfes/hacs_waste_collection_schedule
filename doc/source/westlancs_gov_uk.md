# West Lancashire Council

Support for schedules provided by [West Lancashire Council](https://westlancs.gov.uk).

Source for West Lancashire Council waste collection schedule.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: westlancs_gov_uk
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
    - name: westlancs_gov_uk
      args:
        postcode: WN8 9QR
        uprn: '10012340497'
```
