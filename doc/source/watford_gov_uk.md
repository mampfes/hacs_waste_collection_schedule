# Watford Borough Council

Support for schedules provided by [Watford Borough Council](https://www.watford.gov.uk/).

Source for waste collection services for Watford Borough Council

## Configuration via configuration.yaml

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: watford_gov_uk
      args:
        uprn: UPRN
```

### Using address

```yaml
waste_collection_schedule:
  sources:
    - name: watford_gov_uk
      args:
        address: ADDRESS
```

### Configuration Variables

**uprn**  
*(string) (alternative)*

**address**  
*(string) (alternative)*

Provide one of: `uprn` or `address`.

## Example

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: watford_gov_uk
      args:
        uprn: '100080932722'
```
