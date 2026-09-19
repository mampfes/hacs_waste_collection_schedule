# Bath & North East Somerset Council

Support for schedules provided by [Bath & North East Somerset Council](https://bathnes.gov.uk).

Source for bathnes.gov.uk services for Bath & North East Somerset Council

## Configuration via configuration.yaml

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: bathnes_gov_uk
      args:
        uprn: UPRN
```

### Using postcode and housenameornumber

```yaml
waste_collection_schedule:
  sources:
    - name: bathnes_gov_uk
      args:
        postcode: POSTCODE
        housenameornumber: HOUSENAMEORNUMBER
```

### Configuration Variables

**uprn**  
*(string) (alternative)*

**postcode**  
*(string) (alternative)*

**housenameornumber**  
*(string) (alternative)*

Provide one of: `uprn` or `postcode` + `housenameornumber`.

## Example

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: bathnes_gov_uk
      args:
        uprn: '10001138699'
```

### Using postcode and housenameornumber

```yaml
waste_collection_schedule:
  sources:
    - name: bathnes_gov_uk
      args:
        postcode: BA1 2LR
        housenameornumber: 1
```

## How to get the source arguments

Provide your UPRN, or both your postcode and house name or number. Find your UPRN at https://www.findmyaddress.co.uk/
