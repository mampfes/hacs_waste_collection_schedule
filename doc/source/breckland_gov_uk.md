# Breckland Council

Support for schedules provided by [Breckland Council](https://www.breckland.gov.uk/mybreckland).

Source for breckland.gov.uk

## Configuration via configuration.yaml

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: breckland_gov_uk
      args:
        uprn: UPRN
```

### Using postcode and address

```yaml
waste_collection_schedule:
  sources:
    - name: breckland_gov_uk
      args:
        postcode: POSTCODE
        address: ADDRESS
```

### Configuration Variables

**uprn**  
*(string) (alternative)*

**postcode**  
*(string) (alternative)*

**address**  
*(string) (alternative)*

Provide one of: `uprn` or `postcode` + `address`.

## Example

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: breckland_gov_uk
      args:
        uprn: '10011977093'
```

### Using postcode and address

```yaml
waste_collection_schedule:
  sources:
    - name: breckland_gov_uk
      args:
        postcode: IP22 2LJ
        address: glen travis
```

## How to get the source arguments

Provide your UPRN, or your postcode plus part of your address as the council lists it. Find your UPRN at https://www.findmyaddress.co.uk/
