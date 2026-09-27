# East Riding of Yorkshire Council

Support for schedules provided by [East Riding of Yorkshire Council](https://eastriding.gov.uk).

Source for East Riding of Yorkshire Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: eastriding_gov_uk
      args:
        uprn: UPRN
        postcode: POSTCODE
```

### Configuration Variables

**uprn**  
*(string) (required)*

**postcode**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: eastriding_gov_uk
      args:
        uprn: 010002364380
        postcode: DN14 6BJ
```
