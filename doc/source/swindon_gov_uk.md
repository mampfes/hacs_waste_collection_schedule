# Swindon Borough Council

Support for schedules provided by [Swindon Borough Council](https://www.swindon.gov.uk).

Swindon Borough Council, UK - Waste Collection

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: swindon_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: swindon_gov_uk
      args:
        uprn: '100121147490'
```
