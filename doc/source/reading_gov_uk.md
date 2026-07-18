# Reading Council

Support for schedules provided by [Reading Council](https://reading.gov.uk).

Source for reading.gov.uk services for Reading Council.

## Configuration via configuration.yaml

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: reading_gov_uk
      args:
        uprn: UPRN
```

### Using postcode and housenameornumber

```yaml
waste_collection_schedule:
  sources:
    - name: reading_gov_uk
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
    - name: reading_gov_uk
      args:
        uprn: '310027679'
```

### Using postcode and housenameornumber

```yaml
waste_collection_schedule:
  sources:
    - name: reading_gov_uk
      args:
        postcode: RG31 5PN
        housenameornumber: '65'
```

## How to get the source arguments

Provide your UPRN, or provide both your postcode and house name or number. Find your UPRN at https://www.findmyaddress.co.uk/
