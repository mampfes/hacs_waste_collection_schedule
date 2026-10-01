# Cheshire East Council

Support for schedules provided by [Cheshire East Council](https://cheshireeast.gov.uk).

Source for cheshireeast.gov.uk services for Cheshire East

## Configuration via configuration.yaml

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: cheshire_east_gov_uk
      args:
        uprn: UPRN
```

### Using postcode and name_number

```yaml
waste_collection_schedule:
  sources:
    - name: cheshire_east_gov_uk
      args:
        postcode: POSTCODE
        name_number: NAME_NUMBER
```

### Configuration Variables

**uprn**  
*(string) (alternative)*

**postcode**  
*(string) (alternative)*

**name_number**  
*(string) (alternative)*

Provide one of: `uprn` or `postcode` + `name_number`.

## Example

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: cheshire_east_gov_uk
      args:
        uprn: '100010132073'
```

### Using postcode and name_number

```yaml
waste_collection_schedule:
  sources:
    - name: cheshire_east_gov_uk
      args:
        postcode: WA16 0AY
        name_number: '3'
```

## How to get the source arguments

Enter either your UPRN (available from [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/)) OR your postcode and house number or name.
