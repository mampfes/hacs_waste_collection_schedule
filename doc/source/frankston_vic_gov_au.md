# Frankston City Council

Support for schedules provided by [Frankston City Council](https://frankston.gov.au).

Source script for frankston.vic.gov.au

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: frankston_vic_gov_au
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: frankston_vic_gov_au
      args:
        address: 45r Wedge Rd, Carrum Downs Vic
```
