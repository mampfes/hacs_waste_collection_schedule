# West Lothian Council

Support for schedules provided by [West Lothian Council](https://www.westlothian.gov.uk).

Source for services for West Lothian

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: westlothian_gov_uk
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
    - name: westlothian_gov_uk
      args:
        postcode: EH48+4DD
        uprn: '135007799'
```
