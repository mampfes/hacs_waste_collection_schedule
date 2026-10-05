# Medway Council

Support for schedules provided by [Medway Council](https://www.medway.gov.uk).

Source for medway.gov.uk services for Medway Council

## Configuration via configuration.yaml

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: medway_gov_uk
      args:
        uprn: UPRN
```

### Using postcode and housenameornumber

```yaml
waste_collection_schedule:
  sources:
    - name: medway_gov_uk
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
    - name: medway_gov_uk
      args:
        uprn: '100062390963'
```

### Using postcode and housenameornumber

```yaml
waste_collection_schedule:
  sources:
    - name: medway_gov_uk
      args:
        postcode: ME4 4AY
        housenameornumber: 194-198
```

## How to get the source arguments

Find your UPRN by entering your postcode at https://www.medway.gov.uk/homepage/45/check_collection_day. Alternatively provide your postcode and house name/number exactly as shown on the Medway website (e.g. '194-198').
